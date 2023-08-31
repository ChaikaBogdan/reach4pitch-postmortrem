import os
import hashlib

from django.core.exceptions import FieldError
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import PasswordResetView
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, resolve_url, redirect
from django.db import transaction
from django.db.models import Count, Prefetch
from django.template.loader import render_to_string
from django.http import Http404, JsonResponse
from django.views.generic.edit import CreateView
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    UpdateView,
)
from django.views import View
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from flags.state import flag_disabled
from PIL import Image

from .constants import (
    SUBSCRIBERS_GROUP_NAME,
    PITCH_EXTERNAL_LINKS_INITIAL,
    PITCH_CHANGES_REQUESTED,
)
from .forms import (
    PitchCreateForm,
    PitchUpdateForm,
    UserSignUpForm,
    UserPasswordResetForm,
)
from .formsets import ExternalLinkCreateFormSet, ExternalLinkUpdateFormSet
from .jobs import send_email
from .models import (
    AbuseReport,
    Pitch,
    Publisher,
    Like,
    Review,
    User,
    Notification,
    Resolution,
    ResolutionType,
    Platform,
    Service,
    ExternalLink,
)

ITEMS_PER_PAGE = 5


class EmailConfirmTokenGenerator(PasswordResetTokenGenerator):
    pass


class Index(TemplateView):
    template_name = "index.html"


class Pitches(LoginRequiredMixin, ListView):
    model = Pitch
    paginate_by = ITEMS_PER_PAGE
    template_name = "pitches/list.html"
    default_order_by = ("-likes_count", "-created_at", "name")
    order_by_key = "order_by"

    def get_queryset(self, *args, **kwargs):
        request = self.request
        order_by = request.GET.getlist(
            self.order_by_key,
            default=self.default_order_by,
        )
        qs = super().get_queryset(*args, **kwargs)
        user = request.user
        if user.publisher_id:
            pitch_ids = (
                Review.objects.filter(
                    publisher_id=user.publisher_id,
                )
                .values_list("pitch_id", flat=True)
                .distinct()
            )
            qs = qs.filter(
                is_published=True,
                is_resolved=False,
                pk__in=pitch_ids,
            )
        else:
            qs = qs.filter(created_by_id=user.pk)
        reviews_qs = Review.objects.prefetch_related(
            "publisher",
            "resolution__resolution_type",
        )
        reviews_prefetch = Prefetch("reviews", queryset=reviews_qs)
        qs = qs.annotate(
            likes_count=Count("likes"),
        ).prefetch_related(reviews_prefetch)
        try:
            result = qs.order_by(*order_by)
        except FieldError as exc:
            messages.warning(request, str(exc))
            result = qs.order_by(*self.default_order_by)
        return result

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        order_by = self.request.GET.getlist(self.order_by_key)
        for default_order in self.default_order_by:
            order_by.append(default_order)
        context["filters"] = {}
        for order in order_by:
            is_desc = order.startswith("-")
            key = order[1:] if is_desc else order
            value = order[1:] if is_desc else f"-{order}"
            context["filters"].setdefault(key, f"?{self.order_by_key}={value}")
        return context


class Publishers(ListView):
    model = Publisher
    paginate_by = ITEMS_PER_PAGE
    template_name = "publishers/list.html"
    ordering = "-name"
    default_order_by = ("name",)
    order_by_key = "order_by"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        order_by = self.request.GET.getlist(self.order_by_key)
        for default_order in self.default_order_by:
            order_by.append(default_order)
        context["filters"] = {}
        for order in order_by:
            is_desc = order.startswith("-")
            key = order[1:] if is_desc else order
            value = order[1:] if is_desc else f"-{order}"
            context["filters"].setdefault(key, f"?{self.order_by_key}={value}")
        return context

    def get_queryset(self, *args, **kwargs):
        request = self.request
        order_by = request.GET.getlist(
            self.order_by_key,
            default=self.default_order_by,
        )
        qs = super().get_queryset(*args, **kwargs)
        try:
            result = qs.order_by(*order_by)
        except FieldError as exc:
            messages.warning(request, str(exc))
            result = qs.order_by(*self.default_order_by)
        return result


class PitchDetails(LoginRequiredMixin, DetailView):
    model = Pitch
    template_name = "pitches/details.html"

    def get_queryset(self):
        reviews_qs = Review.objects.filter(
            resolution__isnull=False,
        ).prefetch_related(
            "publisher",
            "resolution__resolution_type",
        )
        reviews_prefetch = Prefetch("reviews", queryset=reviews_qs)
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "likes",
                "services",
                "platforms",
                reviews_prefetch,
            )
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        pitch = self.object
        user = self.request.user
        context["resolutions"] = []
        context["is_pitch_liked"] = bool(
            [like for like in pitch.likes.all() if like.created_by_id == user.id]
        )
        context["remaining_platforms"] = Platform.objects.exclude(
            pk__in=[p.id for p in pitch.platforms.all()]
        )
        context["remaining_services"] = Service.objects.exclude(
            pk__in=[s.id for s in pitch.services.all()]
        )
        for review in pitch.reviews.all():
            resolution = review.resolution
            context["resolutions"].append(
                {
                    "publisher": review.publisher,
                    "description": resolution.description,
                    "type": resolution.resolution_type.name,
                }
            )
        return context


class PublisherDetails(DetailView):
    model = Publisher
    template_name = "publishers/details.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "services",
                "platforms",
            )
        )


class _PublisherForbiddenMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or not bool(user.publisher_id)


class _PitcherForbiddenMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or bool(user.publisher_id)


class PitchCreate(_PublisherForbiddenMixin, CreateView):
    form_class = PitchCreateForm
    template_name = "pitches/create.html"

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        formset = ExternalLinkCreateFormSet(
            request.POST if request.method == "POST" else None,
            queryset=ExternalLink.objects.none(),
            initial=[{"name": name} for name in PITCH_EXTERNAL_LINKS_INITIAL],
        )
        context["external_links_formset"] = formset
        return context

    @transaction.atomic
    def form_valid(self, form, *args, **kwargs):
        formset = ExternalLinkCreateFormSet(self.request.POST)
        if not formset.is_valid():
            return self.form_invalid(form)
        response = super().form_valid(form, *args, **kwargs)
        publisher = form.cleaned_data["publisher"]
        pitch = self.object
        links_to_create = []
        content_type = ContentType.objects.get_for_model(Pitch)
        for external_link in formset.save(commit=False):
            if not external_link.url:
                continue
            external_link.object_id = pitch.id
            external_link.content_type = content_type
            links_to_create.append(external_link)
        ExternalLink.objects.bulk_create(links_to_create)
        Review.objects.create(publisher=publisher, pitch=pitch)
        return response


class PitchUpdate(_PublisherForbiddenMixin, UpdateView):
    model = Pitch
    form_class = PitchUpdateForm
    template_name = "pitches/update.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(created_by_id=self.request.user.pk)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        pitch = self.object
        content_type = ContentType.objects.get_for_model(Pitch)
        queryset = ExternalLink.objects.filter(
            content_type=content_type,
            object_id=pitch.id,
        )
        formset = ExternalLinkUpdateFormSet(
            request.POST if request.method == "POST" else None,
            queryset=queryset,
        )
        context["external_links_formset"] = formset
        return context

    @transaction.atomic
    def form_valid(self, form, *args, **kwargs):
        formset = ExternalLinkUpdateFormSet(self.request.POST)
        if not formset.is_valid():
            return self.form_invalid(form)
        response = super().form_valid(form, *args, **kwargs)
        content_type = ContentType.objects.get_for_model(Pitch)
        pitch = self.object
        links_to_update = []
        links_to_create = []
        links_ids_to_delete = []
        for external_link in formset.save(commit=False):
            if external_link.id:
                if external_link.url:
                    links_to_update.append(external_link)
                else:
                    links_ids_to_delete.append(external_link.id)
            else:
                external_link.object_id = pitch.id
                external_link.content_type = content_type
                links_to_create.append(external_link)
        if links_to_create:
            ExternalLink.objects.bulk_create(links_to_create)
        if links_to_update:
            ExternalLink.objects.bulk_update(
                links_to_update,
                ["url"],
            )
        if links_ids_to_delete:
            ExternalLink.objects.filter(pk__in=links_ids_to_delete).delete()
        return response


class PitchPublisherCreate(PitchCreate):
    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        slug = self.kwargs["slug"]
        publisher_qs = Publisher.objects.prefetch_related("platforms", "services")
        publisher = get_object_or_404(publisher_qs, slug=slug)
        initial["publisher"] = publisher
        return initial


_next_key = "next"


class UserSignup(SuccessMessageMixin, CreateView):
    form_class = UserSignUpForm
    template_name = "registration/signup.html"
    success_message = "Check %(email)s inbox for activation email"
    success_url = reverse_lazy("backend:index")

    def dispatch(self, request, *args, **kwargs):
        if flag_disabled("SIGNUP_ENABLED", request=request):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def _get_next_value(self):
        return self.request.POST.get(
            _next_key,
            self.request.GET.get(_next_key),
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["next_key"] = _next_key
        next_value = self._get_next_value()
        if next_value:
            context.update({_next_key: next_value})
        return context

    def _send_activation_email(self):
        user = self.object
        email_activation_token = EmailConfirmTokenGenerator()
        current_site = get_current_site(self.request)
        site_name = current_site.name
        subject = render_to_string(
            "registration/activate_email_subject.txt",
            {
                "site_name": site_name,
            },
        ).strip()
        protocol = self.request.scheme
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        domain = current_site.domain
        token = email_activation_token.make_token(user)
        context = {
            "user": user,
            "domain": domain,
            "protocol": protocol,
            "uid": uid,
            "token": token,
            "site_name": site_name,
            "next_key": _next_key,
        }
        next_value = self._get_next_value()
        if next_value:
            context[_next_key] = next_value
        message = render_to_string(
            "registration/activate_email.html",
            context,
        ).strip()
        send_email.delay(user.email, subject, message)

    def form_valid(self, form):
        response = super().form_valid(form)
        self._send_activation_email()
        return response


class UserResetPassword(PasswordResetView):
    form_class = UserPasswordResetForm


class EmailActivate(View):
    http_method_names = ["get"]

    def get(self, request, uidb64, token):
        email_activation_token = EmailConfirmTokenGenerator()
        pk = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=pk)
        if user.is_active:
            raise Http404()
        if not email_activation_token.check_token(user, token):
            raise Http404()
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.info(request, "You account is active - please login.")
        next_value = request.GET.get(_next_key)
        url = resolve_url("login")
        if next_value:
            url = f"{url}?{_next_key}={next_value}"
        return redirect(url)


class PitchLike(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        slug = request.POST.get("slug", None)
        if not slug:
            return JsonResponse({}, status=404)
        try:
            pitch = Pitch.objects.get(slug=slug)
        except Pitch.DoesNotExist:
            return JsonResponse({}, status=404)
        if not pitch.is_published:
            return JsonResponse({}, status=404)
        user = request.user
        if pitch.created_by_id == user.pk:
            return JsonResponse({}, status=404)
        liked = True
        try:
            pitch.likes.get(created_by=user).delete()
        except Like.DoesNotExist:
            pitch.likes.create(created_by=user)
        else:
            liked = False
        return JsonResponse({"liked": liked})


class EmailCollect(View):
    http_method_names = ["post"]

    def _send_confirmation_email(self, user: User) -> None:
        current_site = get_current_site(self.request)
        site_name = current_site.name
        subject = render_to_string(
            "registration/collect_email_subject.txt",
            {
                "site_name": site_name,
            },
        ).strip()
        message = render_to_string(
            "registration/collect_email.html",
            {
                "user": user,
                "site_name": site_name,
            },
        ).strip()
        send_email.delay(user.email, subject, message)

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            raise Http404()
        email = request.POST.get("email", None)
        if not email:
            raise Http404()
        if User.objects.filter(email=email).exists():
            messages.warning(
                request,
                "It seems you already in our mailing list!",
            )
            return redirect("backend:index")
        with transaction.atomic():
            group, _ = Group.objects.get_or_create(name=SUBSCRIBERS_GROUP_NAME)
            user = User.objects.create(username=email, email=email, is_active=False)
            user.set_unusable_password()
            user.groups.add(group)
            user.save()
        self._send_confirmation_email(user)
        messages.info(
            request,
            "Thanks for staying in touch!",
        )
        return redirect("backend:index")


class PitchAbuse(_PitcherForbiddenMixin, View):
    http_method_names = ["post"]

    @staticmethod
    def _send_abuse_notification(pitch: Pitch):
        text = render_to_string(
            "pitches/abuse_notification.html",
            {
                "pitch": pitch,
            },
        ).strip()
        Notification.objects.create(
            created_for=pitch.created_by,
            text=text,
        )

    @staticmethod
    def _send_abuse_email(request, pitch: Pitch) -> None:
        current_site = get_current_site(request)
        site_name = current_site.name
        subject = render_to_string(
            "pitches/abuse_email_subject.txt",
            {
                "site_name": site_name,
            },
        ).strip()
        message = render_to_string(
            "pitches/abuse_email.html",
            {
                "pitch": pitch,
                "site_name": site_name,
            },
        ).strip()
        send_email.delay(
            pitch.created_by.email,
            subject,
            message,
        )

    def post(self, request):
        user = request.user
        pitch_slug = request.POST.get("slug", None)
        if not pitch_slug:
            raise Http404()
        try:
            pitch = Pitch.objects.select_related("created_by").get(slug=pitch_slug)
        except Pitch.DoesNotExist:
            raise Http404()
        if not pitch.is_published:
            raise Http404()
        if not user.publisher.reviews.filter(pitch=pitch).exists():
            raise Http404()
        description = self.request.POST.get("description", "").strip()
        if AbuseReport.objects.filter(
            pitch=pitch,
            created_by=user,
            resolved_at__isnull=True,
        ).exists():
            messages.warning(
                request,
                "It seems you already reported abuse for this pitch!",
            )
            return redirect("backend:pitches_list")
        with transaction.atomic():
            AbuseReport.objects.create(
                created_by=user,
                pitch=pitch,
                description=description,
            )
            pitch.is_published = False
            pitch.is_abused = True
            pitch.is_resolved = True
            pitch.save(update_fields=["is_published", "is_abused", "is_resolved"])
            self._send_abuse_notification(pitch)
        self._send_abuse_email(request, pitch)
        messages.info(
            request,
            "Thanks for reporting this violation!",
        )
        return redirect("backend:pitches_list")


class PitchPublish(_PublisherForbiddenMixin, View):
    http_method_names = ["post"]

    @staticmethod
    def _send_new_pitch_email(request, pitch: Pitch, publisher: Publisher) -> None:
        current_site = get_current_site(request)
        site_name = current_site.name
        protocol = request.scheme
        domain = current_site.domain
        subject = render_to_string(
            "pitches/new_email_subject.txt",
            {
                "site_name": site_name,
            },
        ).strip()
        message = render_to_string(
            "pitches/new_email.html",
            {
                "domain": domain,
                "protocol": protocol,
                "site_name": site_name,
                "pitch": pitch,
            },
        ).strip()
        send_email.delay(publisher.email, subject, message)

    @staticmethod
    def _send_new_pitch_notification(pitch: Pitch, publisher: Publisher) -> None:
        text = render_to_string(
            "pitches/new_notification.html",
            {
                "pitch": pitch,
            },
        ).strip()
        notifications = [
            Notification(
                created_for=created_for,
                text=text,
            )
            for created_for in publisher.users.all()
        ]
        if notifications:
            Notification.objects.bulk_create(notifications)

    def post(self, request):
        pitch_slug = request.POST.get("slug", None)
        if not pitch_slug:
            raise Http404()
        reviews_qs = Review.objects.prefetch_related("publisher")
        reviews_prefetch = Prefetch("reviews", queryset=reviews_qs)
        try:
            pitch = Pitch.objects.prefetch_related(reviews_prefetch).get(
                slug=pitch_slug
            )
        except Pitch.DoesNotExist:
            raise Http404()
        if pitch.is_published:
            raise Http404()
        if pitch.abuse_reports.filter(resolved_at__isnull=True).exists():
            messages.warning(request, "Your pitch was reported for abuse!")
            return redirect("backend:pitches_list")
        pitch.is_published = True
        pitch.save(update_fields=["is_published"])
        for review in pitch.reviews.all():
            publisher = review.publisher
            self._send_new_pitch_notification(pitch, publisher)
            if publisher.email:
                self._send_new_pitch_email(request, pitch, publisher)
        messages.info(request, "Your pitch successfully published!")
        return redirect("backend:pitches_list")


class PitchReview(_PitcherForbiddenMixin, View):
    http_method_names = ["post"]

    @staticmethod
    def _send_pitch_reviewed_email(request, pitch: Pitch) -> None:
        current_site = get_current_site(request)
        site_name = current_site.name
        protocol = request.scheme
        domain = current_site.domain
        subject = render_to_string(
            "pitches/reviewed_email_subject.txt",
            {
                "site_name": site_name,
            },
        ).strip()
        message = render_to_string(
            "pitches/reviewed_email.html",
            {
                "domain": domain,
                "protocol": protocol,
                "site_name": site_name,
                "pitch": pitch,
            },
        ).strip()
        send_email.delay(pitch.created_by.email, subject, message)

    @staticmethod
    def _send_pitch_reviewed_notification(pitch: Pitch) -> None:
        text = render_to_string(
            "pitches/reviewed_notification.html",
            {
                "pitch": pitch,
            },
        ).strip()
        Notification.objects.create(
            created_for=pitch.created_by,
            text=text,
        )

    def post(self, request):
        pitch_slug = request.POST.get("slug", None)
        resolution_type = request.POST.get("resolution_type", None)
        description = self.request.POST.get("description", "").strip()
        if not (pitch_slug and resolution_type):
            raise Http404()
        publisher_id = request.user.publisher_id
        try:
            review = Review.objects.select_related(
                "pitch__created_by",
            ).get(
                pitch__slug=pitch_slug,
                pitch__is_resolved=False,
                publisher_id=publisher_id,
            )
        except Review.DoesNotExist:
            raise Http404()
        with transaction.atomic():
            resolution_type, _ = ResolutionType.objects.get_or_create(
                name=resolution_type,
                publisher_id=publisher_id,
            )
            resolution, _ = Resolution.objects.get_or_create(
                resolution_type=resolution_type,
                created_by_id=publisher_id,
                defaults={"description": description},
            )
            review.resolution = resolution
            review.save(update_fields=["resolution"])
            pitch = review.pitch
            pitch.is_published = False
            updated_pitch_fields = ["is_published"]
            if resolution_type.name != PITCH_CHANGES_REQUESTED:
                pitch.is_resolved = True
                updated_pitch_fields.append("is_resolved")
            pitch.save(update_fields=updated_pitch_fields)
            self._send_pitch_reviewed_notification(pitch)
        self._send_pitch_reviewed_email(request, pitch)
        messages.info(request, "Pitch was successfully reviewed!")
        return redirect("backend:pitches_list")


class NotificationHide(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get("notification_id", None)
        if not notification_id:
            raise Http404()
        try:
            notification = Notification.objects.get(pk=notification_id)
        except Notification.DoesNotExist:
            return JsonResponse({}, status=404)
        user = request.user
        if notification.created_for_id != user.pk:
            return JsonResponse({}, status=404)
        if notification.seen_at:
            return JsonResponse({}, status=404)
        notification.seen_at = timezone.now()
        notification.save(update_fields=["seen_at"])
        return JsonResponse({})


@method_decorator(csrf_exempt, name="dispatch")
class UploadImage(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        file_obj = request.FILES["file"]
        try:
            Image.open(file_obj).verify()
        except Exception as exc:
            return JsonResponse({"message": f"Invalid image file - {exc}"})
        path = os.path.join(
            settings.MEDIA_ROOT,
            "tinymce",
        )
        if not os.path.exists(path):
            os.makedirs(path)
        _, file_ext = os.path.splitext(file_obj.name)
        chunks = []
        md5 = hashlib.md5()
        for chunk in file_obj.chunks():
            md5.update(chunk)
            chunks.append(chunk)
        file_name = md5.hexdigest()
        file_full_name = f"{file_name}{file_ext}"
        file_path = os.path.join(path, file_full_name)
        file_url = f"{settings.MEDIA_URL}tinymce/{file_full_name}"
        with open(file_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        return JsonResponse(
            {
                "message": "Image uploaded successfully",
                "location": file_url,
            }
        )
