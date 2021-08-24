import datetime


class User:
    type = "user"

    def __init__(self, user_data: dict):
        if 'data' not in user_data and 'user' not in user_data['data']:
            msg = 'malformed json! cannot be parsed to get user data'
            raise Exception(msg)

        self.id = user_data['data']['user']['rest_id']

        try:
            self.name = user_data['data']['user']['legacy']['name']
        except:
            self.name = ''

        try:
            self.username = user_data['data']['user']['legacy']['screen_name']
        except:
            self.username = ''

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
        self.background_image = user_data['data']['user']['legacy']['profile_banner_url']

        # link to user account
        self.link = f'https://twitter.com/{self.username}'


User_formats = {
    'join_date': '%Y-%m-%d',
    'join_time': '%H:%M:%S %Z'
}