import asyncio
import random
import json
import aiohttp
import logging
import datetime

from tweets import Tweets
from urllib.parse import quote, urlencode
from fake_useragent import UserAgent
from static import USER_AGENT_LIST, BEARER, SEARCH_URL
from twitter_user import User
from guest_token import Token


def get_logger():
    """
    Get the logger.
    :return: logging.LoggerAdapter
    """
    logger = logging.getLogger('logger_component')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())

    return logging.LoggerAdapter(logger, {'session': 1})


def _formatDate(date):
    try:
        return int(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp())
    except ValueError:
        return int(datetime.datetime.strptime(date, "%Y-%m-%d").timestamp())


def _sanitizeQuery(_url, params):
    _serialQuery = ""
    _serialQuery = urlencode(params, quote_via=quote)
    _serialQuery = _url + "?" + _serialQuery
    return _serialQuery


class Twtsc:
    def __init__(self):
        self.token = Token()
        self.token.refresh()

        self.logger = get_logger()

    def get_user_agent(self, tweet_search: bool = False):
        try:
            if tweet_search:
                return "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36"

            return UserAgent(verify_ssl=False, use_cache_server=False).random
        except:
            return random.choice(USER_AGENT_LIST)

    async def make_request(self, url, *, headers=None):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, ssl=True) as response:
                resp = await response.text()
                if response.status == 429:  # Rate Limit Exceeded
                    self.token.refresh()
                    return await self.make_request(url, headers=headers)

                return resp

    async def search_user_tweets(
            self, user: User, limit: int = 100, *,
            search_text: str = None, until: str = None, since: str = None, exclude_retweets: bool = False
    ) -> Tweets:
        params = [
            ('include_can_media_tag', '1'),
            ('include_ext_alt_text', 'true'),
            ('include_quote_count', 'true'),
            ('include_reply_count', '1'),
            ('tweet_mode', 'extended'),
            ('include_entities', 'true'),
            ('include_user_entities', 'true'),
            ('include_ext_media_availability', 'true'),
            ('send_error_codes', 'true'),
            ('simple_quoted_tweet', 'true'),
            ('count', limit),
            ('spelling_corrections', '1'),
            ('ext', 'mediaStats%2ChighlightedLabel'),
            ('tweet_search_mode', 'live'),  # this can be handled better, maybe take an argument and set it then
        ]

        query = f"from:{user.username}"
        if search_text:
            query += f' {search_text}'
        if until:
            query += f' until:{_formatDate(until)}'
        if since:
            query += f' since:{_formatDate(since)}'
        if exclude_retweets:
            query += f' exclude:nativeretweets exclude:retweets'

        params.append(('q', query))
        url_query = _sanitizeQuery(SEARCH_URL, params)

        _headers = {
            'authorization': BEARER,
            'x-guest-token': self.token.token,
        }

        response = await self.make_request(url_query, headers=_headers)
        tweets_data = json.loads(response)
        tweets = Tweets(tweets_data)
        return tweets

    async def get_user(self, *, username: str = None, user_id: str = None) -> User:
        if username:
            url_values = quote(json.dumps({'screen_name': username, 'withHighlightedLabel': False}))
            request_url = f'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={url_values}'
        elif user_id:
            url_values = quote(json.dumps({'userId': user_id, 'withHighlightedLabel': False}))
            request_url = f'https://api.twitter.com/graphql/B9FuNQVmyx32rdbIPEZKag/UserByRestId?variables={url_values}'
        else:
            return None

        _headers = {
            'authorization': BEARER,
            'x-guest-token': self.token.token,
        }
        try:
            response = await self.make_request(request_url, headers=_headers)
            user_data = json.loads(response)
            return User(user_data)
        except Exception as e:
            self.logger.exception(f'Error fetching user: {e}')


async def main():
    twit = Twtsc()

    twitter_user = await twit.get_user(username='TLDRNewsUK')
    print(twitter_user.link)

    user_tweets = await twit.search_user_tweets(twitter_user, limit=5)
    print(user_tweets.all_tweets)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
