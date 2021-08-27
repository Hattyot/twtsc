import asyncio
import random

from .tweets import ParseError
from .twitter_user import User
from typing import Callable, Union, Awaitable
import inspect
import time


class Listener:
    def __init__(self, twtsc, user: User, callback: Union[Callable, Awaitable], *,  interval: int = 60):
        # required
        self.twtsc = twtsc
        self.user = user
        self.callback = callback

        # options
        self.interval = interval

        if interval < 60:
            raise Exception(f'Interval can not be below 60s')

        self.timestamp = 0
        self.stop_event = asyncio.Event()

    def stop(self):
        self.stop_event.set()
        if self.user in self.twtsc.listeners:
            del self.twtsc.listeners[self.user]

    async def runner(self):
        while not self.stop_event.is_set():
            try:
                start = time.time()
                if not self.timestamp:
                    await self.get_last_tweet_timestamp()

                await self.new_tweets()
                end = time.time()

                await asyncio.sleep(self.interval - (end - start) + (random.randint(-5, 5)))
            except ParseError:
                self.timestamp = time.time()
            except Exception as e:
                print('ERROR in runner', e)
                await asyncio.sleep(self.interval + (random.randint(-5, 5)))

    async def get_last_tweet_timestamp(self):
        last_tweet = await self.twtsc.search_user_tweets(self.user, limit=1)

        if last_tweet:
            last_tweet = last_tweet[0]
            timestamp = int(last_tweet.unix_timestamp) + 1
        else:
            timestamp = int(time.time())

        self.timestamp = timestamp

    async def new_tweets(self):
        new_tweets = await self.twtsc.search_user_tweets(self.user, since=self.timestamp)

        if new_tweets:
            self.timestamp = int(new_tweets[-1].unix_timestamp) + 1
            is_await = inspect.iscoroutinefunction(self.callback)
            if is_await:
                await self.callback(new_tweets)
            else:
                self.callback(new_tweets)
