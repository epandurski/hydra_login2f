from urllib.parse import urljoin, quote_plus
import requests
from flask import current_app
from .redis import increment_key_with_limit, UserLoginsHistory, ExceededValueLimitError


def get_subject(user_id):
    return current_app.config['SUBJECT_PREFIX'] + str(user_id)


def invalidate_credentials(user_id):
    UserLoginsHistory(user_id).clear()
    subject = quote_plus(get_subject(user_id))
    timeout = current_app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']
    hydra_consents_base_url = urljoin(current_app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/sessions/consent')
    hydra_logins_base_url = urljoin(current_app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/sessions/login')
    requests.delete(f'{hydra_consents_base_url}?subject={subject}', timeout=timeout)
    requests.delete(f'{hydra_logins_base_url}?subject={subject}', timeout=timeout)


class LoginRequest:
    LOGIN_COUNT_SUBJECT_PREFIX = 'logins:'

    class TooManyLogins(Exception):
        """Too many login attempts."""

    def __init__(self, challenge_id):
        self.challenge_id = quote_plus(challenge_id)
        self.timeout = current_app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']
        base_url = urljoin(current_app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/')
        self.fetch_url = urljoin(base_url, 'login')
        self.accept_url = urljoin(base_url, 'login/accept')
        self.reject_url = urljoin(base_url, 'login/reject')

    def register_successful_login(self, subject):
        key = self.LOGIN_COUNT_SUBJECT_PREFIX + subject
        try:
            increment_key_with_limit(key, limit=current_app.config['MAX_LOGINS_PER_MONTH'], period_seconds=2600000)
        except ExceededValueLimitError:
            raise self.TooManyLogins()

    def fetch(self):
        """Return the subject if already logged, `None` otherwise."""

        r = requests.get(f'{self.fetch_url}?login_challenge={self.challenge_id}', timeout=self.timeout)
        r.raise_for_status()
        fetched_data = r.json()
        return fetched_data['subject'] if fetched_data['skip'] else None

    def accept(self, subject, remember=False, remember_for=1000000000):
        """Accept the request unless the limit is reached, return an URL to redirect to."""

        try:
            self.register_successful_login(subject)
        except self.TooManyLogins:
            return self.reject()
        r = requests.put(f'{self.accept_url}?login_challenge={self.challenge_id}', timeout=self.timeout, json={
            'subject': subject,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']

    def reject(self):
        """Reject the request, return an URL to redirect to."""

        r = requests.put(f'{self.reject_url}?login_challenge={self.challenge_id}', timeout=self.timeout, json={
            'error': 'too_many_logins',
            'error_description': 'Too many login attempts have been made in a given period of time.',
            'error_hint': 'Try again later.',
        })
        r.raise_for_status()
        return r.json()['redirect_to']


class ConsentRequest:
    def __init__(self, challenge_id):
        self.challenge_id = quote_plus(challenge_id)
        self.timeout = current_app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']
        base_url = urljoin(current_app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/')
        self.fetch_url = urljoin(base_url, 'consent')
        self.accept_url = urljoin(base_url, 'consent/accept')

    def fetch(self):
        """Return the list of requested scopes, or an empty list if no consent is required."""

        r = requests.get(f'{self.fetch_url}?consent_challenge={self.challenge_id}', timeout=self.timeout)
        r.raise_for_status()
        fetched_data = r.json()
        return [] if fetched_data['skip'] else fetched_data['requested_scope']

    def accept(self, grant_scope, remember=False, remember_for=0):
        """Approve the request, return an URL to redirect to."""

        r = requests.put(f'{self.accept_url}?consent_challenge={self.challenge_id}', timeout=self.timeout, json={
            'grant_scope': grant_scope,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']
