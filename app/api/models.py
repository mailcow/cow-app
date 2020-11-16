# *-* coding: utf-8 *-*
# Ahmet Küçük <ahmetkucuk4@gmail.com>
# Zekeriya Akgül <zkry.akgul@gmail.com>

from app import db
import hashlib

class Base(db.Model):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Account(Base):
    __tablename__ = 'account'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(192),  nullable=False)
    is_main = db.Column(db.Boolean,  default=False)
    uuid = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<Account %s >' % (self.uuid)

    def check_password(self, password):
        return self.password == hashlib.sha256(password.encode()).hexdigest()

class User(Base):
    __tablename__ = 'user'

    name = db.Column(db.String(128), nullable=True)
    surname = db.Column(db.String(128), nullable=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    accounts = db.relationship('Account', backref="user", lazy=True)

    def __repr__(self):
        return '<User %s %s>' % (self.name, self.surname)

    def has_account(self, email):
        for account in self.accounts:
            if email == account.email:
                return True
        return False

    @property
    def get_accounts(self):
        ret = []
        for account in self.accounts:
            ret.append({"email": account.email, "id": account.id, "is_main": account.is_main})
        return ret
    
    @property
    def main_account(self):
        return Account.query.filter_by(user_id = self.id).filter_by(is_main=True).one()