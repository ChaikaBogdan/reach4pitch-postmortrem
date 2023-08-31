from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = "Fix loaded data for production"

    def handle(self, *args, **kwargs):
        domain = settings.ALLOWED_HOSTS[0] if not settings.DEBUG else "127.0.0.1:8000"
        current_site = Site.objects.get_current()
        if current_site.domain != domain:
            current_site.domain = domain
            current_site.name = domain
            current_site.save(update_fields=["domain", "name"])
            self.stdout.write(
                self.style.SUCCESS('Default site renamed to "%s"' % domain)
            )
