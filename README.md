Simple twitter scraper inspired and based on [twint](https://github.com/twintproject/twint)

## Requirements
* python 3.9
* aiohttp
* fake-useragent

## Install
### Git:
```
git clone https://github.com/Hattyot/twtsc.git
pip3 install -e twtsc
```
## Examples
```python
import asyncio
from twtsc import Twtsc
from twtsc import Tweet


async def get_user_tweets():
    twit = Twtsc()

    twitter_user = await twit.get_user(username='TLDRNewsUK')
    # twitter_user = await twit.get_user(user_id='892125759963312128')

    user_tweets = await twit.search_user_tweets(twitter_user, limit=5)
    print(user_tweets)


async def get_twitter_user():
    twit = Twtsc()

    twitter_user = await twit.get_user(username='TLDRNewsUK')
    print(twitter_user.link)


async def register_tweet_listener():
    def new_tweet(tweets: list[Tweet]):
        print(tweets)

    twit = Twtsc()
    
    twitter_user = await twit.get_user(username='TLDRNewsUK')
    callback = new_tweet
    twit.create_tweet_listener(twitter_user, callback)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.create_task(get_twitter_user())
    loop.create_task(get_user_tweets())
    loop.create_task(register_tweet_listener())

    loop.run_forever()

```