import logging

from django.test.runner import DiscoverRunner


class CustomDiscoverRunner(DiscoverRunner):
    def run_tests(self, *args, **kwargs):
        # Don't show logging messages while testing
        logging.disable(logging.INFO)
        result = super().run_tests(*args, **kwargs)
        logging.disable(logging.NOTSET)
        return result
