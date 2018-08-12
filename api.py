import configparser
import vk_auth
import sys
import urllib
import json
import time


API_RETRY_COUNT = 15


config = configparser.ConfigParser()
config.read('config.ini')


class VkApi:
    token = config.get('auth', 'token', fallback=None)
    user_id = config.get('auth', 'user_id', fallback=None)
    login = config.get('auth', 'login', fallback=None)
    password = config.get('auth', 'password', fallback=None)
    app_id = config.get('auth', 'appid')

    def initialize(self):
        if self.token is None or self.user_id is None:
            # trying to auth with login and password
            if self.login is None or self.password is None:
                # ask user to authorize in browser
                sys.stdout.write("You need to authorize this script to access your private messages on vk.com.\n"
                                 "To do it, you need to:\n1. Open the following url in your browser:\n"
                                 + vk_auth.get_auth_url(self.app_id, 'messages') +
                                 "\n2. Give access to the application.\n"
                                 "3. Copy access_token and user_id from the url of next page and paste it into config.ini file\n"
                                 "4. Start this script again.\n"
                                 )
                input("Now press Enter to open auth page in your default browser, or Ctrl+C to exit")
                vk_auth.auth_in_browser(self.app_id, 'messages')
                return False

            try:
                sys.stdout.write('Trying to authenticate with your login and password...\n')
                self.token, self.user_id = vk_auth.auth(self.login, self.password, self.app_id, 'messages')
            except RuntimeError:
                sys.stdout.write("Authentication failed, maybe login/password are wrong?\n")
                return False

            sys.stdout.write("Authentication successful\n")
        else:
            sys.stdout.write("Authenticating with given token and user_id\n")
        return True

    def call(self, method, params):
        params.append(("access_token", self.token))
        params.append(("v", "5.74"))
        url = "https://api.vk.com/method/%s?%s" % (method, urllib.parse.urlencode(params))

        for j in range(API_RETRY_COUNT):
            try:
                reply = json.loads(urllib.request.urlopen(url, timeout=20).read().decode("utf-8"))
                if 'error' in reply:
                    error_msg = reply['error']['error_msg']
                    if error_msg.endswith('.'):
                        error_msg = error_msg[:-1]
                    raise RuntimeError(error_msg)
                else:
                    return reply['response']
            except Exception as error:
                sys.stdout.write('Got error while requesting api method %s (%s), trying to resume in 5 sec...\n' % (method, str(error)))
                time.sleep(5)

        raise RuntimeError('Failed to call the API\n')
