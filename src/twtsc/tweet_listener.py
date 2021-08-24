import asyncio

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
        if self.user in self.twtsc:
            del self.twtsc.listeners[self.user]

    async def runner(self):
        while not self.stop_event.is_set():
            start = time.time()
            if not self.timestamp:
                await self.get_last_tweet_timestamp()

            await self.new_tweets()
            end = time.time()

            await asyncio.sleep(self.interval - (end - start))

    async def get_last_tweet_timestamp(self):
        last_tweet = await self.twtsc.search_user_tweets(self.user, limit=1)

        if last_tweet:
            last_tweet = last_tweet[0]
            timestamp = last_tweet.unix_timestamp
        else:
            timestamp = time.time()

        self.timestamp = timestamp

    async def new_tweets(self):
        new_tweets = await self.twtsc.search_user_tweets(self.user, since=self.timestamp)

        if new_tweets:
            self.timestamp = new_tweets[-1].unix_timestamp
            is_await = inspect.iscoroutinefunction(object)
            if is_await:
                await self.callback(new_tweets)
            else:
                self.callback(new_tweets)
