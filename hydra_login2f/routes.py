from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, render_template, abort,\
    make_response, current_app, Blueprint
from flask_babel import gettext, get_locale
import user_agents
from . import utils, captcha, emails, hydra
from .redis import SignUpRequest, LoginVerificationRequest, ChangeEmailRequest,\
    ChangeRecoveryCodeRequest, UserLoginsHistory
from .models import User
from .extensions import babel

login = Blueprint('login', __name__, template_folder='templates', static_folder='static')
consent = Blueprint('consent', __name__, template_folder='templates', static_folder='static')


@babel.localeselector
def select_locale():
    language = request.cookies.get(current_app.config['LANGUAGE_COOKE_NAME'])
    language_choices = [choices[0] for choices in current_app.config['LANGUAGE_CHOICES']]
    if language in language_choices:
        return language
    return request.accept_languages.best_match(language_choices)


@babel.timezoneselector
def select_timezone():
    return None


@login.after_app_request
def set_cache_control_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache'
    return response


@login.after_app_request
def set_frame_options_header(response):
    response.headers['X-Frame-Options'] = 'DENY'
    return response


@login.app_context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)


def verify_captcha():
    """Verify captcha if required."""

    if current_app.config['SHOW_CAPTCHA_ON_SIGNUP']:
        captcha_response = request.form.get(current_app.config['CAPTCHA_RESPONSE_FIELD_NAME'], '')
        captcha_solution = captcha.verify(captcha_response, request.remote_addr)
        captcha_passed = captcha_solution.is_valid
        captcha_error_message = captcha_solution.error_message
        if not captcha_passed and captcha_error_message is None:
            captcha_error_message = gettext('Incorrect captcha solution.')
    else:
        captcha_passed = True
        captcha_error_message = None
    return captcha_passed, captcha_error_message


def get_user_agent():
    return str(user_agents.parse(request.headers.get('User-Agent', '')))


def get_change_password_link(email):
    return urljoin(request.host_url, url_for('.signup', email=email, recover='true'))


def get_choose_password_link(signup_request):
    return urljoin(request.host_url, url_for('.choose_password', secret=signup_request.secret))


def get_change_email_address_link(change_email_request):
    return urljoin(request.host_url, url_for('.change_email_address', secret=change_email_request.secret))


def get_generate_recovery_code_link(change_recovery_code_request):
    return urljoin(request.host_url, url_for('.generate_recovery_code', secret=change_recovery_code_request.secret))


def get_computer_code():
    return request.cookies.get(current_app.config['COMPUTER_CODE_COOKE_NAME']) or utils.generate_random_secret()


def set_computer_code_cookie(response, computer_code):
    response.set_cookie(
        current_app.config['COMPUTER_CODE_COOKE_NAME'],
        computer_code,
        max_age=1000000000,
        httponly=True,
        path=current_app.config['LOGIN_PATH'],
        secure=not current_app.config['DEBUG'],
    )


@login.route('/language/<lang>')
def set_language(lang):
    response = redirect(request.args['to'])
    response.set_cookie(
        current_app.config['LANGUAGE_COOKE_NAME'],
        lang,
        path=current_app.config['LOGIN_PATH'],
        max_age=1000000000,
    )
    return response


@login.route('/signup', methods=['GET', 'POST'])
def signup():
    email = request.args.get('email', '')
    is_new_user = 'recover' not in request.args
    if request.method == 'POST':
        captcha_passed, captcha_error_message = verify_captcha()
        email = request.form['email'].strip()
        if utils.is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = get_computer_code()
            computer_code_hash = utils.calc_sha256(computer_code)
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    emails.send_duplicate_registration_email(email)
                else:
                    r = SignUpRequest.create(
                        email=email,
                        cc=computer_code_hash,
                        recover='yes',
                        has_rc='yes' if user.recovery_code_hash else 'no',
                    )
                    emails.send_change_password_email(email, get_choose_password_link(r))
            else:
                if is_new_user:
                    r = SignUpRequest.create(email=email, cc=computer_code_hash)
                    emails.send_confirm_registration_email(email, get_choose_password_link(r))
                else:
                    # We are asked to change the password of a non-existing user. In this case
                    # we fail silently, so as not to reveal if the email is registered or not.
                    pass
            response = redirect(url_for(
                '.report_sent_email',
                email=email,
                login_url=request.args.get('login_url'),
                login_challenge=request.args.get('login_challenge'),
            ))
            set_computer_code_cookie(response, computer_code)
            return response

    title = gettext('Create a New Account') if is_new_user else gettext('Change Account Password')
    return render_template(
        'signup.html',
        email=email,
        title=title,
        display_captcha=captcha.display_html,
    )


@login.route('/email')
def report_sent_email():
    email = request.args['email']
    return render_template('report_sent_email.html', email=email)


@login.route('/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_request = SignUpRequest.from_secret(secret)
    if not signup_request:
        return render_template('report_expired_link.html')
    is_password_recovery = signup_request.recover == 'yes'
    require_recovery_code = (is_password_recovery
                             and signup_request.has_rc == 'yes'
                             and current_app.config['USE_RECOVERY_CODE'])

    if request.method == 'POST':
        recovery_code = request.form.get('recovery_code', '')
        password = request.form['password']
        min_length = current_app.config['PASSWORD_MIN_LENGTH']
        max_length = current_app.config['PASSWORD_MAX_LENGTH']
        if len(password) < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif len(password) > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif password != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        elif require_recovery_code and not signup_request.is_correct_recovery_code(recovery_code):
            try:
                signup_request.register_code_failure()
            except signup_request.ExceededMaxAttempts:
                abort(403)
            flash(gettext('Incorrect recovery code'))
        else:
            new_recovery_code = signup_request.accept(password)
            if is_password_recovery:
                hydra.invalidate_credentials(signup_request.user_id)
                UserLoginsHistory(signup_request.user_id).add(signup_request.cc)
                emails.send_change_password_success_email(
                    signup_request.email,
                    get_change_password_link(signup_request.email),
                )
                return render_template(
                    'report_recovery_success.html',
                    email=signup_request.email,
                )
            else:
                UserLoginsHistory(signup_request.user_id).add(signup_request.cc)
                response = make_response(render_template(
                    'report_signup_success.html',
                    email=signup_request.email,
                    recovery_code=utils.split_recovery_code_in_blocks(new_recovery_code),
                ))
                response.headers['Cache-Control'] = 'no-store'
                return response

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@login.route('/change-email', methods=['GET', 'POST'])
def change_email_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == utils.calc_crypt_hash(user.salt, password):
            try:
                # We create a new login verification request without a
                # verification code. This request can only be used to
                # set a new email address for the account.
                login_verification_request = LoginVerificationRequest.create(
                    user_id=user.user_id,
                    email=email,
                    challenge_id=request.args.get('login_challenge'),
                )
            except LoginVerificationRequest.ExceededMaxAttempts:
                abort(403)
            emails.send_change_email_address_request_email(
                email,
                get_change_password_link(email),
            )
            return redirect(url_for('.choose_new_email', secret=login_verification_request.secret))
        flash(gettext('Incorrect email or password'))

    return render_template('change_email_login.html')


@login.route('/choose-email/<secret>', methods=['GET', 'POST'])
def choose_new_email(secret):
    verification_request = LoginVerificationRequest.from_secret(secret)
    if not verification_request:
        return render_template('report_expired_link.html')
    user = User.query.filter_by(user_id=int(verification_request.user_id)).one()
    require_recovery_code = user.recovery_code_hash and current_app.config['USE_RECOVERY_CODE']
    if not require_recovery_code:
        # Allowing the user to change her account email address
        # without supplying a recovery code is a bad idea, because in
        # this case her account could be hijacked when her password is
        # known. (Instead of only when her email is being read.)
        return render_template('report_missing_recovery_code.html')

    if request.method == 'POST':
        captcha_passed, captcha_error_message = verify_captcha()
        email = request.form['email'].strip()
        recovery_code = request.form.get('recovery_code', '')
        if utils.is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        elif not verification_request.is_correct_recovery_code(recovery_code):
            try:
                verification_request.register_code_failure()
            except verification_request.ExceededMaxAttempts:
                abort(403)
            flash(gettext('Incorrect recovery code'))
        else:
            verification_request.accept()
            r = ChangeEmailRequest.create(
                user_id=user.user_id,
                email=email,
                old_email=verification_request.email,
            )
            emails.send_change_email_address_email(email, get_change_email_address_link(r))
            return redirect(url_for(
                '.report_sent_email',
                email=email,
                login_challenge=verification_request.challenge_id,
            ))

    response = make_response(render_template(
        'choose_new_email.html',
        require_recovery_code=True,
        display_captcha=captcha.display_html,
    ))
    response.headers['Cache-Control'] = 'no-store'
    return response


@login.route('/change-email/<secret>', methods=['GET', 'POST'])
def change_email_address(secret):
    change_email_request = ChangeEmailRequest.from_secret(secret)
    if not change_email_request:
        return render_template('report_expired_link.html')

    if request.method == 'POST':
        email = change_email_request.old_email
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == utils.calc_crypt_hash(user.salt, password):
            try:
                change_email_request.accept()
            except change_email_request.EmailAlredyRegistered:
                return redirect(url_for('.report_email_change_failure', new_email=change_email_request.email))
            hydra.invalidate_credentials(int(change_email_request.user_id))
            return redirect(url_for(
                '.report_email_change_success',
                new_email=change_email_request.email,
                old_email=change_email_request.old_email,
            ))
        flash(gettext('Incorrect password'))

    return render_template('enter_password.html', title=gettext('Change Email Address'))


@login.route('/change-email-failure')
def report_email_change_failure():
    return render_template('report_email_change_failure.html', new_email=request.args['new_email'])


@login.route('/change-email-success')
def report_email_change_success():
    return render_template(
        'report_email_change_success.html',
        old_email=request.args['old_email'],
        new_email=request.args['new_email'],
    )


@login.route('/change-recovery-code', methods=['GET', 'POST'])
def change_recovery_code():
    if not current_app.config['USE_RECOVERY_CODE']:
        abort(404)
    email = request.args.get('email', '')
    if request.method == 'POST':
        captcha_passed, captcha_error_message = verify_captcha()
        email = request.form['email'].strip()
        if utils.is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            r = ChangeRecoveryCodeRequest.create(email=email)
            emails.send_change_recovery_code_email(email, get_generate_recovery_code_link(r))
            return redirect(url_for(
                '.report_sent_email',
                email=email,
                login_challenge=request.args.get('login_challenge'),
            ))

    return render_template(
        'signup.html',
        email=email,
        title=gettext('Change Recovery Code'),
        display_captcha=captcha.display_html,
    )


@login.route('/recovery-code/<secret>', methods=['GET', 'POST'])
def generate_recovery_code(secret):
    change_recovery_code_request = ChangeRecoveryCodeRequest.from_secret(secret)
    if not change_recovery_code_request:
        return render_template('report_expired_link.html')

    if request.method == 'POST':
        email = change_recovery_code_request.email
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == utils.calc_crypt_hash(user.salt, password):
            new_recovery_code = change_recovery_code_request.accept()
            response = make_response(render_template(
                'report_recovery_code_change.html',
                email=email,
                recovery_code=utils.split_recovery_code_in_blocks(new_recovery_code),
            ))
            response.headers['Cache-Control'] = 'no-store'
            return response
        flash(gettext('Incorrect password'))

    return render_template('enter_password.html', title=gettext('Change Recovery Code'))


@login.route('/', methods=['GET', 'POST'])
def login_form():
    login_request = hydra.LoginRequest(request.args['login_challenge'])
    subject = login_request.fetch()
    if subject:
        return redirect(login_request.accept(subject))

    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == utils.calc_crypt_hash(user.salt, password):
            user_id = user.user_id
            subject = hydra.get_subject(user_id)
            if not user.two_factor_login:
                return redirect(login_request.accept(subject, remember_me))

            # Two factor login: require a cookie containing a secret
            # "computer code" as well. The cookie proves that there
            # was a previous successful login attempt from this computer.
            computer_code = get_computer_code()
            computer_code_hash = utils.calc_sha256(computer_code)
            user_logins_history = UserLoginsHistory(user_id)
            if user_logins_history.contains(computer_code_hash):
                user_logins_history.add(computer_code_hash)
                return redirect(login_request.accept(subject, remember_me))

            # A two factor login verification code is required.
            verification_code = utils.generate_verification_code()
            verification_cookie = utils.generate_random_secret()
            verification_cookie_hash = utils.calc_sha256(verification_cookie)
            try:
                LoginVerificationRequest.create(
                    _secret=verification_cookie_hash,
                    user_id=user_id,
                    email=email,
                    code=verification_code,
                    remember_me='yes' if remember_me else 'no',
                    challenge_id=login_request.challenge_id,
                )
            except LoginVerificationRequest.ExceededMaxAttempts:
                abort(403)
            emails.send_verification_code_email(
                email,
                verification_code,
                get_user_agent(),
                get_change_password_link(email),
            )
            response = redirect(url_for('.enter_verification_code'))
            response.set_cookie(
                current_app.config['LOGIN_VERIFICATION_COOKE_NAME'],
                verification_cookie,
                httponly=True,
                path=current_app.config['LOGIN_PATH'],
                secure=not current_app.config['DEBUG'],
            )
            set_computer_code_cookie(response, computer_code)
            return response
        flash(gettext('Incorrect email or password'))

    return render_template('login.html')


@login.route('/verify', methods=['GET', 'POST'])
def enter_verification_code():
    verification_cookie = request.cookies.get(current_app.config['LOGIN_VERIFICATION_COOKE_NAME'], '*')
    verification_cookie_hash = utils.calc_sha256(verification_cookie)
    verification_request = LoginVerificationRequest.from_secret(verification_cookie_hash)
    if not verification_request:
        abort(403)

    if request.method == 'POST':
        if request.form['verification_code'].strip() == verification_request.code:
            login_request = hydra.LoginRequest(verification_request.challenge_id)
            user_id = int(verification_request.user_id)
            subject = hydra.get_subject(user_id)
            remember_me = verification_request.remember_me == 'yes'
            verification_request.accept(clear_failures=True)
            computer_code_hash = utils.calc_sha256(get_computer_code())
            UserLoginsHistory(user_id).add(computer_code_hash)
            return redirect(login_request.accept(subject, remember_me))
        try:
            verification_request.register_code_failure()
        except verification_request.ExceededMaxAttempts:
            abort(403)
        flash(gettext('Invalid verification code'))

    return render_template('enter_verification_code.html', secret=verification_cookie_hash)


@consent.route('/', methods=['GET', 'POST'])
def dummy_consent():
    """Always grant consent."""

    consent_request = hydra.ConsentRequest(request.args['consent_challenge'])
    requested_scope = consent_request.fetch()
    return redirect(consent_request.accept(requested_scope))
