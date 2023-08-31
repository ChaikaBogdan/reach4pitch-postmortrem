from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import (
    User,
    Pitch,
    Publisher,
    Review,
    PublisherService,
    Resolution,
    ResolutionType,
    Platform,
    Service,
    ExternalLink,
    PricingPlan,
    AbuseReport,
    Subscriber,
    Webhook,
    Notification,
)


class ExternalLinksInline(GenericTabularInline):
    model = ExternalLink
    verbose_name = "Link"
    verbose_name_plural = "Links"
    extra = 1


class PublisherServicesInline(admin.TabularInline):
    model = PublisherService
    verbose_name = "Service"
    verbose_name_plural = "Services"
    extra = 1


class ReviewsInline(admin.TabularInline):
    model = Review
    verbose_name = "Review"
    verbose_name_plural = "Reviews"
    extra = 1


class WebhooksInline(admin.TabularInline):
    model = Webhook
    verbose_name = "Webhook"
    verbose_name_plural = "Webhooks"
    extra = 1


class NotificationsInline(admin.TabularInline):
    model = Notification
    verbose_name = "Notification"
    verbose_name_plural = "Notifications"
    extra = 0


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    inlines = [ReviewsInline, ExternalLinksInline]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    inlines = [
        ReviewsInline,
        PublisherServicesInline,
        ExternalLinksInline,
        WebhooksInline,
    ]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    inlines = [
        NotificationsInline,
    ]


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return False


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    pass


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass


@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    pass


@admin.register(ResolutionType)
class ResolutionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(AbuseReport)
class AbuseReportAdmin(admin.ModelAdmin):
    pass
