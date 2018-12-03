# hydra_login2f

**hydra_login2f** is a secure login provider for [ORY
Hydra](https://github.com/ory/hydra) Auth2 server. *hydra_login2f*
supports two-factor authentication via email. It can be deployed
directly from docker images.


## Installation

You can find a working example in the `example/` directory.


## Configuration varialble

``` shell
PORT = 8000

SECRET_KEY = 'dummy-secret'
SITE_TITLE = 'My site name'
LANGUAGES = 'en'  # separated by a comma, for example 'en,bg'
USE_RECOVERY_CODE = True
ABOUT_URL = 'https://github.com/epandurski/hydra_login2f'
STYLE_URL = ''
LOGIN_PATH = '/login'
CONSENT_PATH = '/consent'

HYDRA_ADMIN_URL = 'http://hydra:4445'

REDIS_URL = 'redis://localhost:6379/0'

SQLALCHEMY_DATABASE_URI = ''

MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = None  # for example "My Site Name <no-reply@my-site.com>"

RECAPTCHA_PUBLIC_KEY = '6Lc902MUAAAAAJL22lcbpY3fvg3j4LSERDDQYe37'
RECAPTCHA_PIVATE_KEY = '6Lc902MUAAAAAN--r4vUr8Vr7MU1PF16D9k2Ds9Q'
RECAPTCHA_REQUEST_TIMEOUT_SECONDS = 5
```
