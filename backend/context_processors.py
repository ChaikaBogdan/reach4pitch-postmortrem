from typing import Any, Dict

from django.http import HttpRequest

AUTH_PAGES_URL_NAMES = frozenset(
    (
        "login",
        "password_reset",
        "signup",
        "password_reset_done",
    )
)


def auth(request: HttpRequest) -> Dict[str, Any]:
    url_name = request.resolver_match.url_name
    return {
        "is_auth_page": url_name in AUTH_PAGES_URL_NAMES,
    }


def notifications(request: HttpRequest) -> Dict[str, Any]:
    user = request.user
    if user.is_authenticated:
        notifications = user.notifications.filter(created_for=user).order_by(
            "-created_at"
        )
    else:
        notifications = []
    unread_count = 0
    for notification in notifications:
        if not notification.seen_at:
            unread_count += 1
    return {
        "notifications": notifications,
        "unread_count": unread_count,
    }
