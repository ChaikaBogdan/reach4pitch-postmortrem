from django.urls import path
from .views import (
    Index,
    Pitches,
    Publishers,
    PitchDetails,
    PitchCreate,
    PitchUpdate,
    PitchPublisherCreate,
    PitchAbuse,
    PitchPublish,
    PitchLike,
    PitchReview,
    PublisherDetails,
    NotificationHide,
)

app_name = "backend"
urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("pitches", Pitches.as_view(), name="pitches_list"),
    path("publishers", Publishers.as_view(), name="publishers_list"),
    path("pitches/<uuid:slug>", PitchDetails.as_view(), name="pitch_details"),
    path(
        "publishers/<str:slug>",
        PublisherDetails.as_view(),
        name="publisher_details",
    ),
    path("pitch/create", PitchCreate.as_view(), name="pitch_create"),
    path("pitch/<str:slug>/update", PitchUpdate.as_view(), name="pitch_update"),
    path("pitch/like", PitchLike.as_view(), name="pitch_like"),
    path("pitch/abuse", PitchAbuse.as_view(), name="pitch_abuse"),
    path("pitch/publish", PitchPublish.as_view(), name="pitch_publish"),
    path("pitch/review", PitchReview.as_view(), name="pitch_review"),
    path(
        "<str:slug>/pitch",
        PitchPublisherCreate.as_view(),
        name="pitch_publisher_create",
    ),
    path("notification/hide", NotificationHide.as_view(), name="notification_hide"),
]
