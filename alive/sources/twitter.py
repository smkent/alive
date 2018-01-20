import twitter

from .source import Source
from ..util import epoch_time_to_datetime


DEFAULT_KEYWORD = 'alive'
MAX_TWEETS = 10
TWEET_URL_FORMAT = 'https://twitter.com/statuses/{}'


class Twitter(Source):
    name = 'twitter'

    def __init__(self, *args, **kwargs):
        super(Twitter, self).__init__(*args, **kwargs)
        self._twitter = None
        if 'twitter' not in self.config or not self.config.twitter:
            raise Exception('No Twitter configuration is present')
        self.usernames = self._list(self.config.twitter.get('username'))
        if not self.usernames:
            raise Exception('No Twitter username(s) are configured')
        self.keywords = [
            keyword.strip().lower() for keyword in
            self._list(self.config.twitter.get('keyword', DEFAULT_KEYWORD))
        ]
        if not self.keywords:
            raise Exception('No Twitter keyword(s) are configured')

    def _list(self, value):
        return list(value) if isinstance(value, (list, tuple)) else [value]

    @property
    def _client(self):
        if not self._twitter:
            api_args = {}
            for arg in ['consumer_key', 'consumer_secret',
                        'access_token_key', 'access_token_secret']:
                if arg not in self.config.twitter:
                    raise Exception('Missing Twitter configuration value {}'
                                    .format(arg))
                api_args.update({arg: self.config.twitter[arg]})
            self._twitter = twitter.Api(tweet_mode='extended', **api_args)
        return self._twitter

    def check(self):
        tweets = []
        for username in self.usernames:
            tweets += self._client.GetUserTimeline(screen_name=username,
                                                   count=MAX_TWEETS)
        for tweet in sorted(tweets, key=lambda x: x.created_at_in_seconds):
            if tweet.created_at_in_seconds <= self._last_checked:
                continue
            if tweet.user.screen_name.lower() != username.lower():
                continue

            tweet_keyword, tweet_action = tweet.full_text.split(' ', 1)
            if tweet_keyword.strip().lower() not in self.keywords:
                continue
            is_test = (tweet_action and
                       tweet_action.split()[0].lower() == 'test')
            source_text = ('A Tweet sent at {} by {}: "{}" ({})'
                           .format(
                               epoch_time_to_datetime(
                                   tweet.created_at_in_seconds),
                               tweet.user.screen_name,
                               tweet.full_text,
                               TWEET_URL_FORMAT.format(tweet.id_str)))
            yield source_text, is_test
            self._last_checked = tweet.created_at_in_seconds
