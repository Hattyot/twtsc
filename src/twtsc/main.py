import random
import json
import aiohttp
import logging
import asyncio

from .tweet_listener import Listener
from .tweets import parse_tweets_data, Tweet
from urllib.parse import quote, urlencode
from fake_useragent import UserAgent
from .static import USER_AGENT_LIST, BEARER, SEARCH_URL
from .twitter_user import User
from .guest_token import Token
from typing import Union, Optional, Callable, Awaitable


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


class Twtsc:
    def __init__(self, loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()

        self.token = Token()
        self.token.refresh()
        self.logger = get_logger()
        self.listeners: dict[User, Listener] = {}

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
                    headers['x-guest-token'] = self.token.token
                    return await self.make_request(url, headers=headers)

                return resp

    def create_tweet_listener(self, user: User, callback: Union[Callable, Awaitable], *, interval: int = 60):
        if not self.loop.is_running():
            raise NotImplementedError('Registering a new tweet listener currently requires a running event loop')

        listener = Listener(self, user, callback, interval=interval)
        self.loop.create_task(listener.runner())
        self.listeners[user] = listener

    async def search_user_tweets(
            self, user: User, limit: int = 100, *,
            search_text: str = None, until: int = None, since: int = None, exclude_retweets: bool = False,
            only_retweets: bool = False
    ) -> list[Tweet]:
        tweets_data = await self._search_request(
            user, limit, search_text=search_text, until=until, since=since, exclude_retweets=exclude_retweets,
            only_retweets=only_retweets
        )
        tweets = parse_tweets_data(tweets_data)

        # if retweets have not been exluded and only_retweets isnt true, include retweets in tweet list
        # yes this is stupid and ii hate it too
        if not exclude_retweets and not only_retweets:
            user_retweets = await self._search_request(
                user, limit, search_text=search_text, until=until, since=since, only_retweets=True
            )

            retweets = parse_tweets_data(user_retweets)
            tweets = tweets + retweets

        tweets = sorted(tweets, key=lambda tweet: -tweet.unix_timestamp)[:limit]
        for tweet in tweets:
            tweet.user = user

        return tweets[::-1]

    async def _search_request(
            self, user: User, limit: int = 100, *,
            search_text: str = None, until: int = None, since: int = None, exclude_retweets: bool = False,
            only_retweets: bool = False
    ) -> dict:
        params = [
            ('include_can_media_tag', '1'),
            ('include_want_retweets', '1'),
            ('include_ext_alt_text', 'true'),
            ('include_quote_count', 'true'),
            ('include_reply_count', '1'),
            ('include_cards', '1'),
            ('cards_platform', 'Web-12'),
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

        query = f"from:{user.screen_name}"
        if search_text:
            query += f' {search_text}'
        if until:
            query += f' until:{int(until)}'
        if since:
            query += f' since:{int(since)}'
        if exclude_retweets:
            query += f' -filter:quote -filter:retweets'
        if only_retweets:
            query += f' +filter:nativeretweets'

        params.append(('q', query))
        url_query = SEARCH_URL + "?" + urlencode(params, quote_via=quote)

        _headers = {
            'authorization': BEARER,
            'x-guest-token': self.token.token,
        }

        response = await self.make_request(url_query, headers=_headers)
        return json.loads(response)

    async def get_user(self, *, username: str = None, user_id: str = None) -> Optional[User]:
        if username:
            url_values = quote(json.dumps({'screen_name': username, 'withHighlightedLabel': False}))
            request_url = f'https://api.twitter.com/graphql/jMaTS-_Ea8vh9rpKggJbCQ/UserByScreenName?variables={url_values}'
        elif user_id:
            url_values = quote(json.dumps({'userId': str(user_id), 'withHighlightedLabel': False}))
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
            return User(self, user_data)
        except Exception as e:
            self.logger.exception(f'Error fetching user: {e}')
