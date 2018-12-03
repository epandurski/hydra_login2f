# hydra_login2f

**hydra_login2f** is a secure login provider for [ORY
Hydra](https://github.com/ory/hydra) Auth2 server. *hydra_login2f*
implements two-factor authentication via email, and can be deployed
directly from a docker image.


## Installation

You can find a working example in the `example/` directory.


## Configuration varialble

``` shell
PORT = 8000

SECRET_KEY = 'dummy-secret'  # must be set to a random, long string
SITE_TITLE = 'My site name'  # the name of your site, as it is known to your users
LANGUAGES = 'en'  # separated by a comma, for example 'en,bg'
USE_RECOVERY_CODE = True  # whether to issue users recovery codes for additional security
ABOUT_URL = 'https://github.com/epandurski/hydra_login2f'  # URL that tells more about your site
STYLE_URL = ''  # optional custom CSS style-sheet
LOGIN_PATH = '/login'  # the path to your login page (ORY Hydra's OAUTH2_LOGIN_URL)
CONSENT_PATH = '/consent'  # the path to your consent page (ORY Hydra's OAUTH2_CONSENT_URL)

HYDRA_ADMIN_URL = 'http://hydra:4445'  # the URL for ORY Hydra's admin API

REDIS_URL = 'redis://localhost:6379/0'  # the URL for your Redis server instance

SQLALCHEMY_DATABASE_URI = ''  # the URL for your PostgreSQL server instance

# SMTP server connection parameters
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = None  # for example "My Site Name <no-reply@my-site.com>"

# Parameters for Google reCAPTCHA 2. You should obtain your own public/private key pair
# from www.google.com/recaptcha, and put it here
RECAPTCHA_PUBLIC_KEY = '6Lc902MUAAAAAJL22lcbpY3fvg3j4LSERDDQYe37'
RECAPTCHA_PIVATE_KEY = '6Lc902MUAAAAAN--r4vUr8Vr7MU1PF16D9k2Ds9Q'
```
