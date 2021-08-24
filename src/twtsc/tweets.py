import datetime
import json
from time import strftime, localtime
from twitter_user import User, BasicUser

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


def _get_reply_to(tw) -> list[BasicUser]:
    try:
        reply_to = [
            BasicUser(_mention) for _mention in tw['entities']['user_mentions']
            if tw['display_text_range'][0] < _mention['indices'][0]
        ]
    except KeyError:
        reply_to = []

    return reply_to


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

        self.username = tweet_data["user_data"]['screen_name']
        self.link = f"https://twitter.com/{self.username}/status/{self.id}"

        self.datetime = str(_dt.strftime(Tweet_formats['datetime']))
        self.datestamp = _dt.strftime(Tweet_formats['datestamp'])
        self.timestamp = _dt.strftime(Tweet_formats['timestamp'])
        self.date = self.datetime

        self.user_id = int(tweet_data["user_id_str"])
        self.name = tweet_data["user_data"]['name']
        self.place = tweet_data['geo'] if 'geo' in tweet_data and tweet_data['geo'] else ""
        self.timezone = strftime("%z", localtime())
        self.mentions = _get_mentions(tweet_data)
        self.reply_to = _get_reply_to(tweet_data)
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

        try:
            self.retweet = True
            self.retweet_id = tweet_data['retweet_data']['retweet_id']
            self.retweet_date = tweet_data['retweet_data']['retweet_date']
            self.user_rt = tweet_data['retweet_data']['user_rt']
            self.user_rt_id = tweet_data['retweet_data']['user_rt_id']
        except KeyError:
            self.retweet = False
            self.retweet_id = ''
            self.retweet_date = ''
            self.user_rt = ''
            self.user_rt_id = ''

        try:
            self.quote_url = tweet_data['quoted_status_permalink']['expanded'] if tweet_data['is_quote_status'] else ''
        except KeyError:
            # means that the quoted tweet have been deleted
            self.quote_url = 0

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

            if 'retweeted_status_id_str' in tweet_data:
                rt_id = tweet_data['retweeted_status_id_str']
                _dt = tweets_data['globalObjects']['tweets'][rt_id]['created_at']
                _dt = datetime.datetime.strptime(_dt, '%a %b %d %H:%M:%S %z %Y')
                _dt = str(_dt.strftime(Tweet_formats['datetime']))
                tweet_data['retweet_data'] = {
                    'user_rt_id': tweets_data['globalObjects']['tweets'][rt_id]['user_id_str'],
                    'user_rt': tweets_data['globalObjects']['tweets'][rt_id]['full_text'],
                    'retweet_id': rt_id,
                    'retweet_date': _dt,
                }

            tweet_obj = Tweet(tweet_data)
            tweets.append(tweet_obj)

    return tweets
