import time
import hashlib
from sqlalchemy.exc import IntegrityError
from flask import current_app
from . import utils
from .models import User, UserUpdateSignal
from .extensions import db, redis_store


def _get_user_verification_code_failures_redis_key(user_id):
    return 'vcfails:' + str(user_id)


def _register_user_verification_code_failure(user_id):
    expiration_seconds = max(current_app.config['LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS'], 24 * 60 * 60)
    key = _get_user_verification_code_failures_redis_key(user_id)
    with redis_store.pipeline() as p:
        p.incrby(key)
        p.expire(key, expiration_seconds)
        num_failures = int(p.execute()[0] or '0')
    return num_failures


def _clear_user_verification_code_failures(user_id):
    redis_store.delete(_get_user_verification_code_failures_redis_key(user_id))


class UserLoginsHistory:
    """Contain identification codes from the last logins of a given user."""

    REDIS_PREFIX = 'cc:'

    def __init__(self, user_id):
        self.max_count = current_app.config['LOGIN_VERIFIED_DEVICES_MAX_COUNT']
        self.key = self.REDIS_PREFIX + str(user_id)

    @staticmethod
    def calc_hash(s):
        return hashlib.sha224(s.encode('ascii')).hexdigest()

    def contains(self, element):
        emement_hash = self.calc_hash(element)
        return emement_hash in redis_store.zrevrange(self.key, 0, self.max_count - 1)

    def add(self, element):
        emement_hash = self.calc_hash(element)
        with redis_store.pipeline() as p:
            p.zremrangebyrank(self.key, 0, -self.max_count)
            p.zadd(self.key, {emement_hash: time.time()})
            p.execute()

    def clear(self):
        redis_store.delete(self.key)


class RedisSecretHashRecord:
    class ExceededMaxAttempts(Exception):
        """Too many failed attempts to enter the correct code."""

    @property
    def key(self):
        return self.REDIS_PREFIX + self.secret

    @classmethod
    def create(cls, _secret=None, **data):
        instance = cls()
        instance.secret = _secret or utils.generate_random_secret()
        instance._data = data
        with redis_store.pipeline() as p:
            p.hmset(instance.key, data)
            p.expire(instance.key, current_app.config[cls.EXPIRATION_SECONDS_CONFIG_FIELD])
            p.execute()
        return instance

    @classmethod
    def from_secret(cls, secret):
        instance = cls()
        instance.secret = secret
        instance._data = dict(zip(cls.ENTRIES, redis_store.hmget(instance.key, cls.ENTRIES)))
        return instance if instance._data.get(cls.ENTRIES[0]) is not None else None

    def delete(self):
        redis_store.delete(self.key)

    def __getattr__(self, name):
        return self._data[name]


def increment_key_with_limit(key, limit=None, period_seconds=1):
    if redis_store.ttl(key) < 0:
        redis_store.set(key, '1', ex=period_seconds)
        value = 1
    else:
        value = redis_store.incrby(key)
    if limit is not None and int(value) > limit:
        raise ExceededValueLimitError()
    return value


class ExceededValueLimitError(Exception):
    """The maximum value of a key has been exceeded."""


class LoginVerificationRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS_CONFIG_FIELD = 'LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS'
    REDIS_PREFIX = 'vcode:'
    ENTRIES = ['user_id', 'code', 'challenge_id', 'email', 'remember_me']

    @classmethod
    def create(cls, **data):
        # We register a "code failure" after the creation of each
        # login verification request. This prevents maliciously
        # creating huge numbers of them.
        instance = super().create(**data)
        instance.register_code_failure()
        return instance

    def is_correct_recovery_code(self, recovery_code):
        user = User.query.filter_by(user_id=int(self.user_id)).one()
        normalized_recovery_code = utils.normalize_recovery_code(recovery_code)
        return user.recovery_code_hash == utils.calc_crypt_hash(user.salt, normalized_recovery_code)

    def register_code_failure(self):
        num_failures = _register_user_verification_code_failure(self.user_id)
        if num_failures > current_app.config['SECRET_CODE_MAX_ATTEMPTS']:
            self.delete()
            raise self.ExceededMaxAttempts()

    def accept(self, clear_failures=False):
        if clear_failures:
            _clear_user_verification_code_failures(self.user_id)
        self.delete()


class SignUpRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS_CONFIG_FIELD = 'SIGNUP_REQUEST_EXPIRATION_SECONDS'
    REDIS_PREFIX = 'signup:'
    ENTRIES = ['email', 'cc', 'recover', 'has_rc']

    def is_correct_recovery_code(self, recovery_code):
        user = User.query.filter_by(email=self.email).one()
        normalized_recovery_code = utils.normalize_recovery_code(recovery_code)
        return user.recovery_code_hash == utils.calc_crypt_hash(user.salt, normalized_recovery_code)

    def register_code_failure(self):
        num_failures = int(redis_store.hincrby(self.key, 'fails'))
        if num_failures >= current_app.config['SECRET_CODE_MAX_ATTEMPTS']:
            self.delete()
            raise self.ExceededMaxAttempts()

    def accept(self, password):
        self.delete()
        if self.recover:
            recovery_code = None
            user = User.query.filter_by(email=self.email).one()
            user.password_hash = utils.calc_crypt_hash(user.salt, password)

            # After changing the password, we "forget" past login
            # verification failures, thus guaranteeing that the user
            # will be able to log in immediately.
            _clear_user_verification_code_failures(user.user_id)
        else:
            salt = utils.generate_password_salt(current_app.config['PASSWORD_HASHING_METHOD'])
            if current_app.config['USE_RECOVERY_CODE']:
                recovery_code = utils.generate_recovery_code()
                recovery_code_hash = utils.calc_crypt_hash(salt, recovery_code)
            else:
                recovery_code = None
                recovery_code_hash = None
            user = User(
                email=self.email,
                salt=salt,
                password_hash=utils.calc_crypt_hash(salt, password),
                recovery_code_hash=recovery_code_hash,
                two_factor_login=True,
            )
            db.session.add(user)
            if current_app.config['SEND_USER_UPDATE_SIGNAL']:
                db.session.add(UserUpdateSignal(user=user, email=user.email))
        db.session.commit()
        self.user_id = user.user_id
        return recovery_code


class ChangeEmailRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS_CONFIG_FIELD = 'CHANGE_EMAIL_REQUEST_EXPIRATION_SECONDS'
    REDIS_PREFIX = 'setemail:'
    ENTRIES = ['email', 'old_email', 'user_id']

    class EmailAlredyRegistered(Exception):
        """The new email is already registered."""

    def accept(self):
        self.delete()
        user_id = int(self.user_id)
        user = User.query.filter_by(user_id=user_id, email=self.old_email).one()
        user.email = self.email
        if current_app.config['SEND_USER_UPDATE_SIGNAL']:
            db.session.add(UserUpdateSignal(user=user, email=self.email))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise self.EmailAlredyRegistered()


class ChangeRecoveryCodeRequest(RedisSecretHashRecord):
    EXPIRATION_SECONDS_CONFIG_FIELD = 'CHANGE_RECOVERY_CODE_REQUEST_EXPIRATION_SECONDS'
    REDIS_PREFIX = 'changerc:'
    ENTRIES = ['email']

    def accept(self):
        self.delete()
        recovery_code = utils.generate_recovery_code()
        user = User.query.filter_by(email=self.email).one()
        user.recovery_code_hash = utils.calc_crypt_hash(user.salt, recovery_code)
        db.session.commit()
        return recovery_code
