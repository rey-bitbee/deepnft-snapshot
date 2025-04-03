import base64
import hmac
import hashlib
import time
import urllib.parse

import httpx
from loguru import logger


class DingdingRobot:
    def __init__(self, access_token, secret) -> None:
        self._access_token = access_token
        self._secret = secret

    def notify(self, msg_type, **kwargs):
        timestamp, sign = self.get_params()
        if msg_type == "markdown":
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": kwargs.get("title"),
                    "text": kwargs.get("text"),
                }
            }

        self.request(timestamp, sign, data)

    def get_params(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self._secret.encode("utf-8")
        string_to_sign = '{}\n{}'.format(timestamp, self._secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def request(self, timestamp, sign, data):
        url = "https://oapi.dingtalk.com/robot/send"
        params = dict(
            access_token=self._access_token,
            timestamp=timestamp,
            sign=sign
        )
        try:
            resp = httpx.post(url=url, params=params, json=data)
            logger.info("call dingding webhook: status_code: {}", resp.status_code)
            if resp.status_code == 200:
                logger.info("success call dingding webhook: resp: {}", resp.json())
            else:
                logger.error("fail call dingding webhook: resp: {}", resp.content)
        except Exception as err:
            logger.error("fail call dingding webhook {}", str(err))
