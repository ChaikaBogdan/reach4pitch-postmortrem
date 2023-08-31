from django.db import models

from .constants import SUBSCRIBERS_GROUP_NAME


class SubscriberManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                groups__name=SUBSCRIBERS_GROUP_NAME,
            )
        )
