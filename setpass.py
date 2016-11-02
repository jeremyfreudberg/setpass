import json
import uuid

from flask import Flask, Response
from flask import request, abort, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)


class TokenNotFoundException(Exception):
    pass


class BadRequestException(Exception):
    pass


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True)
    token = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    def __init__(self, user_id, token, password):
        self.user_id = user_id
        self.token = token
        self.password = password

    def __repr__(self):
        return '<User %r, Token %r>' % (self.user_id, self.token)

    @staticmethod
    def find(token):
        return User.query.filter_by(token=token).first()


db.create_all()


@app.route('/', methods=['GET'])
def view_form():
    return render_template('password_form.html')


@app.route('/', methods=['POST'])
def set_password():
    token = request.args.get('token')
    password = request.form['password']

    if not token or not password:
        return Response(response='Not token/password in request', status=400)

    try:
        _set_password(token, password)
    except TokenNotFoundException:
        return Response(response='Token not found', status=404)

    return Response(status=200)


def _set_openstack_password(user_id, old_password, new_password):
    pass


def _set_password(token, password):
    # Find user for token
    user = User.find(token)

    if user is None:
        raise TokenNotFoundException

    _set_openstack_password(user.user_id, user.password, password)

    db.session.delete(user)
    db.session.commit()


@app.route('/token/<user_id>', methods=['PUT'])
def add(user_id):
    password = request.data

    user = User(
        user_id=user_id,
        token=str(uuid.uuid4()),
        password=password
    )

    db.session.add(user)
    db.session.commit()

    return Response(response=user.token, status=200)


if __name__ == '__main__':
    app.run()
