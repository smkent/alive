import os
import time

from .source import Source

DEFAULT_TEST_INTERVAL = 2629800  # Total seconds in year / 12, approx. 1 month
DEFAULT_MESSAGE = os.linesep.join([
    'This is a periodic test message sent to confirm the application and ',
    'outbound email are working properly.',
])


class PeriodicTest(Source):
    name = 'periodic_test'

    def __init__(self, *args, **kwargs):
        super(PeriodicTest, self).__init__(*args, **kwargs)
        try:
            config = self.config.periodic_test or {}
        except:
            config = {}
        self._enabled = config.get('enabled', True)
        self._interval = config.get('interval', DEFAULT_TEST_INTERVAL)

    def check(self):
        if not self._enabled:
            return
        last_checked = self._last_checked
        now = int(time.time())
        if last_checked:
            if now <= (last_checked + self._interval):
                return
            yield DEFAULT_MESSAGE, True
        self._last_checked = now
