import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from flask_babel import lazy_gettext
from flask import current_app


ERROR_MESSAGE = lazy_gettext('You did not solve the "reCAPTCHA" challenge.')


class CaptchaResponse:
    def __init__(self, is_valid, error_message=None):
        self.is_valid = is_valid
        self.error_message = error_message


def display_html(lang='en'):
    """Gets the HTML to display for reCAPTCHA."""

    return """
    <script src="{challenge_url}?hl={lang}" async defer></script>
    <div class="g-recaptcha" data-sitekey="{public_key}"></div>
    """.format(
        challenge_url=current_app.config['RECAPTCHA_CHALLENGE_URL'],
        public_key=current_app.config['RECAPTCHA_PUBLIC_KEY'],
        lang=lang,
    )


def verify(captcha_response, remote_ip):
    """
    Submits a reCAPTCHA request for verification, returns `CaptchaResponse`.

    captcha_response -- The value of `g-recaptcha-response` field from the form
    remoteip -- user's IP address
    """

    if not captcha_response:
        return CaptchaResponse(is_valid=False, error_message=ERROR_MESSAGE)

    http_request = Request(
        url=current_app.config['RECAPTCHA_VERIFY_URL'],
        data=urlencode({
            'secret': current_app.config['RECAPTCHA_PIVATE_KEY'],
            'response': captcha_response,
            'remoteip': remote_ip,
        }).encode('ascii'),
        headers={
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Python"
        },
    )
    timeout_seconds = current_app.config['RECAPTCHA_REQUEST_TIMEOUT_SECONDS']
    with urlopen(http_request, timeout=timeout_seconds) as http_response:
        response_object = json.loads(http_response.read().decode())
    if (response_object["success"]):
        return CaptchaResponse(is_valid=True)
    else:
        return CaptchaResponse(is_valid=False, error_message=ERROR_MESSAGE)
