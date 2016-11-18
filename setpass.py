import datetime
import json
import uuid

from flask import Flask, Response
from flask import request, abort, render_template
from flask_sqlalchemy import SQLAlchemy

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)


EXPIRES_AFTER_SECONDS = 24 * 3600


class TokenNotFoundException(Exception):
    pass


class TokenExpiredException(Exception):
    pass


class WrongPinException(Exception):
    pass


class InvalidPinException(Exception):
    pass


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True)
    token = db.Column(db.String(64), unique=True)
    pin = db.Column(db.String(4), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, token, pin, password):
        self.user_id = user_id
        self.token = token
        self.pin = pin
        self.password = password
        self.update_timestamp()

    def update_timestamp(self):
        self.updated_at = datetime.datetime.utcnow()

    def __repr__(self):
        return '<User %r, Token %r>' % (self.user_id, self.token)

    @staticmethod
    def find(**kwargs):
        return User.query.filter_by(**kwargs).first()


db.create_all()


@app.route('/', methods=['GET'])
def view_form():
    return render_template('password_form.html')


@app.route('/', methods=['POST'])
def set_password():
    token = request.args.get('token')
    password = request.form['password']
    pin = request.form['pin']

    if not token or not password or not pin:
        return Response(response='Missing token/pin/password!', status=400)

    try:
        _set_password(token, pin, password)
    except TokenNotFoundException:
        return Response(response='Token not found', status=404)
    except TokenExpiredException:
        return Response(response='Token expired', status=403)
    except WrongPinException:
        return Response(response='Wrong pin', status=403)

    return Response(status=200)


def _set_openstack_password(user_id, old_password, new_password):
    auth = v3.Password(auth_url='https://my.keystone.com:5000/v3',
                       user_id=user_id,
                       password=old_password,
                       project_id='project_id')

    sess = session.Session(auth=auth)
    keystone = client.Client(session=sess)

    keystone.users.update_password(old_password, new_password)


def _set_password(token, pin, password):
    # Find user for token
    user = User.find(token=token)

    if user is None:
        raise TokenNotFoundException

    if pin != user.pin:
        raise WrongPinException

    delta = datetime.datetime.utcnow() - user.updated_at
    if delta.total_seconds() > EXPIRES_AFTER_SECONDS:
        raise TokenExpiredException

    #_set_openstack_password(user.user_id, user.password, password)

    db.session.delete(user)
    db.session.commit()


@app.route('/token/<user_id>', methods=['PUT'])
def add(user_id):
    payload = json.loads(request.data)

    user = User.find(user_id=user_id)
    if user:
        if 'pin' in payload:
            user.pin = payload['pin']
        if 'password' in payload:
            user.password = payload['password']

        user.token = str(uuid.uuid4())
        user.update_timestamp()
    else:
        user = User(
            user_id=user_id,
            token=str(uuid.uuid4()),
            pin=payload['pin'],
            password=payload['password']
        )
        db.session.add(user)

    db.session.commit()
    return Response(response=user.token, status=200)


if __name__ == '__main__':
    app.run()
