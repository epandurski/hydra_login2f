from .extensions import db


class User(db.Model):
    user_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    recovery_code_hash = db.Column(db.String(128), nullable=True)
    two_factor_login = db.Column(db.Boolean, nullable=False)


class UserUpdateSignal(db.Model):
    user_update_signal_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)
    email = db.Column(db.String(255), nullable=True)

    user = db.relationship('User')

    def send_signalbus_message(self):
        """Inform the other services that user's email has changed."""

        ##############################################
        # Send a message over your message bus here! #
        ##############################################
