# hydra_login2f

*hydra_login2f* is a secure login provider for [ORY Hydra Auth2
Server](https://github.com/ory/hydra). *hydra_login2f* implements
two-factor authentication via email.


## Installation

*hydra_login2f* can be deployed directly from a [docker
image](https://hub.docker.com/r/epandurski/hydra_login2f/). You can
find a working example in the `example/` directory.


## Configuration

*hydra_login2f*'s behavior can be tuned with environment
variables. Here are the most important settings with their default
values:

``` shell
# The port on which `hydra_login2f` will run.
PORT = 8000

# The path to the login page (ORY Hydra's `OAUTH2_LOGIN_URL`):
LOGIN_PATH = '/login'

# The path to the dummy consent page (ORY Hydra's `OAUTH2_CONSENT_URL`).
# `hydra_login2f` implements a dummy consent page, which accepts all
# consent requests unconditionally without showing any UI to the user.
# This is sometimes useful, especially during testing.
CONSENT_PATH = '/consent'

# Set this to a random, long string, and keep it secret.
SECRET_KEY = 'dummy-secret'

# Set this to the name of your site, as it is known to your users.
SITE_TITLE = 'My site name'

# Set this to an URL that tells more about your site.
ABOUT_URL = 'https://github.com/epandurski/hydra_login2f'

# Optional URL for a custom CSS style-sheet:
STYLE_URL = ''

# Whether to give users recovery codes for additional security:
USE_RECOVERY_CODE = True

# Set this to the URL for ORY Hydra's admin API.
HYDRA_ADMIN_URL = 'http://hydra:4445'

# Set this to the URL for your Redis server instance.
REDIS_URL = 'redis://localhost:6379/0'

# Set this to the URL for your SQL database server instance. PostgreSQL
# and MySQL are supported out of the box.
SQLALCHEMY_DATABASE_URI = ''

# SMTP server connection parameters. You should set `MAIL_DEFAULT_SENDER`
# to the email address from which you send your outgoing emails to users,
# "My Site Name <no-reply@my-site.com>" for example.
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = None

# Parameters for Google reCAPTCHA 2. You should obtain your own public/private
# key pair from www.google.com/recaptcha, and put it here.
RECAPTCHA_PUBLIC_KEY = '6Lc902MUAAAAAJL22lcbpY3fvg3j4LSERDDQYe37'
RECAPTCHA_PIVATE_KEY = '6Lc902MUAAAAAN--r4vUr8Vr7MU1PF16D9k2Ds9Q'

# Set this to the number of worker processes for handling requests -- a
# positive integer generally in the 2-4 * $NUM_CORES range.
GUNICORN_WORKERS=2

# Set this to the number of worker threads for handling requests. (Runs
# each worker with the specified number of threads.)
GUNICORN_THREADS=1
```
