import datetime
import pytz
import tzlocal


def epoch_time_to_datetime(epoch_time, tzinfo=tzlocal.get_localzone()):
    return (datetime.datetime.utcfromtimestamp(epoch_time)
            .replace(tzinfo=pytz.utc).astimezone(tzinfo))
