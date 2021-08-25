import datetime
from time import strftime, localtime
from .twitter_user import User, BasicUser

Tweet_formats = {
    'datetime': '%Y-%m-%d %H:%M:%S %Z',
    'datestamp': '%Y-%m-%d',
    'timestamp': '%H:%M:%S'
}


def _get_mentions(tw) -> list[BasicUser]:
    """
    Extract mentions from tweet
    """
    try:
        mentions = [
            BasicUser(_mention) for _mention in tw['entities']['user_mentions']
            if tw['display_text_range'][0] < _mention['indices'][0]
        ]
    except KeyError:
        mentions = []

    return mentions


class Card:
    def __init__(self, card_data: dict):
        self.url = card_data['url']
        try:
            self.description = card_data['binding_values']['description']['string_value']
            self.title = card_data['binding_values']['title']['string_value']
            self.thumbnail = card_data['binding_values']['thumbnail_image_large']['image_value']['url']
        except:
            self.description = ''
            self.title = ''
            self.thumbnail = ''


class Tweet:
    def __init__(self, tweet_data: dict, *, user: User = None):
        self.user = user

        self.id = int(tweet_data['id_str'])
        self.conversation_id = tweet_data["conversation_id_str"]

        _dt = tweet_data['created_at']
        _dt = datetime.datetime.strptime(_dt, '%a %b %d %H:%M:%S %z %Y')
        self.unix_timestamp = _dt.timestamp()

        self.tweet_text = tweet_data['full_text']
        self.lang = tweet_data['lang']

        self.replies_count = tweet_data['reply_count']
        self.retweets_count = tweet_data['retweet_count']
        self.likes_count = tweet_data['favorite_count']

        self.datetime = str(_dt.strftime(Tweet_formats['datetime']))
        self.datestamp = _dt.strftime(Tweet_formats['datestamp'])
        self.timestamp = _dt.strftime(Tweet_formats['timestamp'])
        self.date = self.datetime

        self.user_id = int(tweet_data["user_id_str"])
        self.name = tweet_data["user_data"]['name']
        self.screen_name = tweet_data["user_data"]['screen_name']
        self.avatar = tweet_data['user_data']['profile_image_url_https']
        self.link = f"https://twitter.com/{self.screen_name}/status/{self.id}"

        self.place = tweet_data['geo'] if 'geo' in tweet_data and tweet_data['geo'] else ""
        self.timezone = strftime("%z", localtime())

        self.mentions = _get_mentions(tweet_data)

        self.retweet_data: Tweet = Tweet(tweet_data['retweet_data']) if 'retweet_data' in tweet_data else None
        self.retweet = bool(self.retweet_data)
        self.reply = bool(tweet_data.get('in_reply_to_status_id', None))
        self.quote_data: Tweet = Tweet(tweet_data['quote_data']) if 'quote_data' in tweet_data else None
        self.quote = bool(self.quote_data)

        self.card_data: Card = Card(tweet_data.get('card')) if 'card' in tweet_data else None

        try:
            self.urls = [_url['expanded_url'] for _url in tweet_data['entities']['urls']]
        except KeyError:
            self.urls = []

        try:
            self.photos = [
                _img['media_url_https'] for _img in tweet_data['entities']['media']
                if _img['type'] == 'photo' and _img['expanded_url'].find('/photo/') != -1
            ]
        except KeyError:
            self.photos = []

        try:
            self.video = True if len(tweet_data['extended_entities']['media']) else False
        except KeyError:
            self.video = True

        try:
            self.thumbnail = tweet_data['extended_entities']['media'][0]['media_url_https']
        except KeyError:
            self.thumbnail = ''

        try:
            self.hashtags = [hashtag['text'] for hashtag in tweet_data['entities']['hashtags']]
        except KeyError:
            self.hashtags = []
        try:
            self.cashtags = [cashtag['text'] for cashtag in tweet_data['entities']['symbols']]
        except KeyError:
            self.cashtags = []

    def __eq__(self, other):
        if type(other) == str:
            return other == str(self.id)
        if type(other) == int:
            return other == int(self.id)
        if type(other) == Tweet:
            return other.id == self.id

    def __str__(self):
        return f'<Tweet {self.id}>'

    def __repr__(self):
        return f'<Tweet {self.id}>'


def parse_tweets_data(tweets_data) -> list[Tweet]:
    tweets = []
    for timeline_entry in tweets_data['timeline']['instructions'][0]['addEntries']['entries']:
        if timeline_entry['entryId'].startswith('sq-I-t-') or timeline_entry['entryId'].startswith('tweet-'):
            if 'tweet' in timeline_entry['content']['item']['content']:
                _id = timeline_entry['content']['item']['content']['tweet']['id']
                # skip the ads
                if 'promotedMetadata' in timeline_entry['content']['item']['content']['tweet']:
                    continue

            elif 'tombstone' in timeline_entry['content']['item']['content'] and 'tweet' in \
                    timeline_entry['content']['item']['content']['tombstone']:
                _id = timeline_entry['content']['item']['content']['tombstone']['tweet']['id']
            else:
                _id = None
                continue

            tweet_data = tweets_data['globalObjects']['tweets'].get(_id, None)
            tweet_data['user_data'] = tweets_data['globalObjects']['users'][tweet_data['user_id_str']]

            if 'quoted_status_id_str' in tweet_data:
                quote_id = tweet_data['quoted_status_id_str']
                tweet_data['quote_data'] = tweets_data['globalObjects']['tweets'][quote_id]
                tweet_data['quote_data']['user_data'] = tweets_data['globalObjects']['users'][
                    tweet_data['quote_data']['user_id_str']]
            if 'retweeted_status_id_str' in tweet_data:
                rt_id = tweet_data['retweeted_status_id_str']
                tweet_data['retweet_data'] = tweets_data['globalObjects']['tweets'][rt_id]
                tweet_data['retweet_data']['user_data'] = tweets_data['globalObjects']['users'][
                    tweet_data['retweet_data']['user_id_str']]

            tweet_obj = Tweet(tweet_data)
            tweets.append(tweet_obj)

    return tweets
