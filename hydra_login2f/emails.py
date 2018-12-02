from flask import render_template
from flask_babel import gettext
from flask_mail import Message
from .extensions import mail


def send_duplicate_registration_email(email):
    msg = Message(
        subject=gettext('Duplicate Registration'),
        recipients=[email],
        body=render_template(
            'duplicate_registration.txt',
            email=email,
        ),
    )
    mail.send(msg)


def send_change_password_email(email, choose_password_link):
    msg = Message(
        subject=gettext('Change Account Password'),
        recipients=[email],
        body=render_template(
            'change_password.txt',
            email=email,
            choose_password_link=choose_password_link,
        ),
    )
    mail.send(msg)


def send_change_password_success_email(email, change_password_page):
    msg = Message(
        subject=gettext('Changed Account Password'),
        recipients=[email],
        body=render_template(
            'change_password_success.txt',
            email=email,
            change_password_page=change_password_page,
        ),
    )
    mail.send(msg)


def send_confirm_registration_email(email, register_link):
    msg = Message(
        subject=gettext('Create a New Account'),
        recipients=[email],
        body=render_template(
            'confirm_registration.txt',
            email=email,
            register_link=register_link,
        ),
    )
    mail.send(msg)


def send_verification_code_email(email, verification_code, user_agent, change_password_page):
    msg = Message(
        subject=gettext('New login from %(user_agent)s', user_agent=user_agent),
        recipients=[email],
        body=render_template(
            'verification_code.txt',
            verification_code=verification_code,
            user_agent=user_agent,
            change_password_page=change_password_page,
        ),
    )
    mail.send(msg)


def send_change_email_address_request_email(email, change_password_page):
    msg = Message(
        subject=gettext('Change Email Address'),
        recipients=[email],
        body=render_template(
            'request_email_change.txt',
            change_password_page=change_password_page,
        ),
    )
    mail.send(msg)


def send_change_email_address_email(email, change_email_address_link):
    msg = Message(
        subject=gettext('Change Email Address'),
        recipients=[email],
        body=render_template(
            'change_email_address.txt',
            email=email,
            change_email_address_link=change_email_address_link,
        ),
    )
    mail.send(msg)


def send_change_recovery_code_email(email, change_recovery_code_link):
    msg = Message(
        subject=gettext('Change Recovery Code'),
        recipients=[email],
        body=render_template(
            'change_recovery_code.txt',
            email=email,
            change_recovery_code_link=change_recovery_code_link,
        ),
    )
    mail.send(msg)
