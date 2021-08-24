import asyncio
import random
import json
import aiohttp
import logging
from urllib.parse import quote
from fake_useragent import UserAgent
from static import USER_AGENT_LIST, BEARER
from typing import Optional
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


class Twtsc:
    def __init__(self, config: 'Config'):
        self.config = config

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

    async def search_user(self, *, username: str = None, user_id: str = None):
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


class Config:
    def __init__(self):
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None


async def main():
    config = Config()
    config.user_name = 'TLDRNewsUK'
    twit = Twtsc(config)

    twitter_user = await twit.search_user(username='TLDRNewsUK')
    print(twitter_user.link)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
