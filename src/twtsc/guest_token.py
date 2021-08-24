import re
import time
import requests


class TokenExpiryException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RefreshTokenException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Token:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'}
        )
        self._retries = 5
        self._timeout = 10
        self.url = 'https://twitter.com'

        self.token = ''

    def _request(self):
        for attempt in range(self._retries + 1):
            # The request is newly prepared on each retry because of potential cookie updates.
            req = self._session.prepare_request(requests.Request('GET', self.url))
            try:
                r = self._session.send(req, allow_redirects=True, timeout=self._timeout)
            except requests.exceptions.RequestException as exc:
                pass
            else:
                success, msg = (True, None)
                if success:
                    return r
            if attempt < self._retries:
                # TODO : might wanna tweak this back-off timer
                sleep_time = 2.0 * 2 ** attempt
                time.sleep(sleep_time)
        else:
            msg = f'{self._retries + 1} requests to {self.url} failed, giving up.'
            self.token = None
            raise RefreshTokenException(msg)

    def refresh(self):
        res = self._request()
        match = re.search(r'\("gt=(\d+);', res.text)
        if match:
            self.token = str(match.group(1))
        else:
            self.token = None
            raise RefreshTokenException('Could not find the Guest token in HTML')
