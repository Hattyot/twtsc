import datetime


class BasicUser:
    """For reply and mention users."""
    def __init__(self, user_data: dict):
        self.id = user_data['id']
        self.screen_name = user_data['screen_name']
        self.name = user_data['name']

    def __dict__(self):
        return {
            'id': self.id,
            'screen_name': self.screen_name,
            'name': self.name
        }

    def __eq__(self, other):
        if type(other) == str:
            return other == self.screen_name or other == self.name or other == str(self.id)
        if type(other) == int:
            return other == int(self.id)
        if type(other) == User or type(other) == User:
            return other.id == self.id


class User:
    def __init__(self, twtsc, user_data: dict):
        if 'data' not in user_data or 'user' not in user_data['data']:
            msg = 'malformed json! cannot be parsed to get user data'
            raise Exception(msg)

        self.twtsc = twtsc

        self.id = user_data['data']['user']['rest_id']

        try:
            self.name = user_data['data']['user']['legacy']['name']
        except:
            self.name = ''

        try:
            self.screen_name = user_data['data']['user']['legacy']['screen_name']
        except:
            self.screen_name = ''

        try:
            self.bio = user_data['data']['user']['legacy']['description']
        except:
            self.bio = ''

        try:
            self.location = user_data['data']['user']['legacy']['location']
        except:
            self.location = ''

        # url listed on user's account
        try:
            self.url = user_data['data']['user']['legacy']['url']
        except:
            self.url = ''

        _dt = user_data['data']['user']['legacy']['created_at']
        _dt = datetime.datetime.strptime(_dt, '%a %b %d %H:%M:%S %z %Y')

        self.join_date = _dt.strftime(User_formats['join_date'])
        self.join_time = _dt.strftime(User_formats['join_time'])

        self.tweets = int(user_data['data']['user']['legacy']['statuses_count'])
        self.following = int(user_data['data']['user']['legacy']['friends_count'])
        self.followers = int(user_data['data']['user']['legacy']['followers_count'])
        self.likes = int(user_data['data']['user']['legacy']['favourites_count'])
        self.media_count = int(user_data['data']['user']['legacy']['media_count'])

        self.is_private = user_data['data']['user']['legacy']['protected']
        self.is_verified = user_data['data']['user']['legacy']['verified']
        self.avatar = user_data['data']['user']['legacy']['profile_image_url_https']

        try:
            self.background_image = user_data['data']['user']['legacy']['profile_banner_url']
        except:
            self.background_image = ''

        # link to user account
        self.link = f'https://twitter.com/{self.screen_name}'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if type(other) == str:
            return other == self.screen_name or other == self.name or other == str(self.id)
        if type(other) == int:
            return other == int(self.id)
        if type(other) == User:
            return other.id == self.id


User_formats = {
    'join_date': '%Y-%m-%d',
    'join_time': '%H:%M:%S %Z'
}