import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from tinymce.models import HTMLField

from .managers import SubscriberManager


class Like(models.Model):
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="likes",
        related_query_name="like",
    )
    created_at = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return f"Like #{self.id} from user #{self.created_by_id}"

    class Meta:
        unique_together = ["created_by", "content_type", "object_id"]


class ExternalLink(models.Model):
    icon = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=255)
    url = models.URLField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return f"External link {self.name} - {self.url}"


class Pitch(models.Model):
    name = models.CharField(max_length=255)
    # Using uuid as primary has complexity with generic relations
    slug = models.UUIDField(default=uuid.uuid4, editable=False)
    tagline = models.CharField(max_length=255, blank=True, default="")
    cover = models.URLField(null=True, blank=True)
    description = HTMLField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="pitches",
        related_query_name="pitch",
    )
    likes = GenericRelation(
        Like,
        related_name="pitches",
        related_query_name="pitch",
    )
    links = GenericRelation(
        ExternalLink,
        related_name="links",
        related_query_name="link",
    )
    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_abused = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    platforms = models.ManyToManyField("Platform", blank=True)
    services = models.ManyToManyField("Service", blank=True)

    class Meta:
        verbose_name_plural = "Pitches"

    def get_absolute_url(self) -> str:
        return reverse("backend:pitch_details", kwargs={"slug": self.slug})

    def __str__(self) -> str:
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=255)
    icon = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Publisher(models.Model):
    pitches = models.ManyToManyField(Pitch, through="Review")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    tagline = models.CharField(max_length=255, default="", blank=True)
    description = HTMLField(default="", blank=True)
    logo = models.URLField(null=True, blank=True)
    likes = GenericRelation(
        Like,
        related_name="publishers",
        related_query_name="publisher",
    )
    links = GenericRelation(
        ExternalLink,
        related_name="links",
        related_query_name="link",
    )
    created_at = models.DateTimeField(default=timezone.now)
    platforms = models.ManyToManyField(Platform, blank=True)
    services = models.ManyToManyField(Service, through="PublisherService", blank=True)
    email = models.EmailField(null=True, blank=True)

    def clean_fields(self, *args, **kwargs):
        super().clean_fields(*args, **kwargs)
        slug = slugify(self.name)
        if self.slug != slug and Publisher.objects.filter(slug=slug).exists():
            raise ValidationError(
                {"name": f'"{self.name}" producing non unique slug - "{slug}"'}
            )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("backend:publisher_details", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Webhook(models.Model):
    class Action(models.TextChoices):
        PITCH_PUBLISHED = "pitch_published", "Pitch submitted to review"

    action = models.CharField(
        max_length=255,
        choices=Action.choices,
        default=Action.PITCH_PUBLISHED,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="webhooks",
        related_query_name="webhook",
    )
    url = models.URLField()

    def __str__(self):
        return f"Publisher #{self.publisher_id} webhook on #{self.action}"

    class Meta:
        unique_together = ["action", "publisher"]


class PricingPlan(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    enabled = models.BooleanField(default=True)
    max_pitches = models.PositiveIntegerField(default=1)
    max_reviews = models.PositiveIntegerField(default=1)
    max_lfp = models.PositiveIntegerField(default=0)
    max_lft = models.PositiveIntegerField(default=0)
    max_team = models.PositiveIntegerField(default=1)
    premium_support = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PublisherService(models.Model):
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
    description = HTMLField(default="", blank=True)

    def __str__(self):
        return f"Publisher #{self.publisher_id} service #{self.service_id}"

    class Meta:
        unique_together = ["service", "publisher"]


class User(AbstractUser):
    email = models.EmailField(unique=True)
    pricing_plan = models.ForeignKey(
        PricingPlan,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="users",
        related_query_name="user",
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def get_full_name(self):
        name_parts = [self.first_name, self.last_name]
        full_name = " ".join(name_parts).strip()
        if full_name:
            return full_name
        return self.get_username()


class Subscriber(User):
    objects = SubscriberManager()

    class Meta:
        proxy = True


class ResolutionType(models.Model):
    name = models.CharField(max_length=255)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="resolution_types",
        related_query_name="resolution_type",
    )

    def __str__(self):
        return f"Resolution for publisher #{self.publisher_id} - {self.name}"

    class Meta:
        unique_together = ["name", "publisher"]


class Resolution(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="resolutions",
        related_query_name="resolution",
    )
    resolution_type = models.ForeignKey(
        ResolutionType,
        on_delete=models.PROTECT,
        related_name="resolutions",
        related_query_name="resolution",
    )
    description = HTMLField(default="", blank=True)

    def __str__(self):
        return f"Resolution #{self.id} at {self.created_at.isoformat()}"


class Review(models.Model):
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.PROTECT,
        related_name="reviews",
        related_query_name="review",
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="reviews",
        related_query_name="review",
    )
    resolution = models.ForeignKey(
        Resolution,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviews",
        related_query_name="review",
    )

    def __str__(self):
        return f"Pitch #{self.pitch_id} review from publisher #{self.publisher_id}"

    class Meta:
        unique_together = ["pitch", "publisher"]


class AbuseReport(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="abuse_reports",
        related_query_name="abuse_report",
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.PROTECT,
        related_name="abuse_reports",
        related_query_name="abuse_report",
    )
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="resolved_abuses",
        related_query_name="resolved_abuse",
        blank=True,
        null=True,
    )
    description = HTMLField(default="", blank=True)

    def __str__(self):
        return f"Pitch #{self.pitch_id} abuse from user #{self.created_by}"


class Notification(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    created_for = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="notifications",
        related_query_name="notification",
    )
    seen_at = models.DateTimeField(blank=True, null=True)
