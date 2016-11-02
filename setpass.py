from flask import Flask
from flask import request, abort, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)


class PasswordAlreadyChangedException(Exception):
    pass


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
    changed = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, token, password, changed=False):
        self.user_id = user_id
        self.token = token
        self.password = password
        self.changed = changed

    def __repr__(self):
        return '<User %r, Token %r>' % (self.user_id, self.token)

    @staticmethod
    def find(token):
        return User.query.filter_by(token=token).first()


@app.route('/', methods=['GET'])
def view_form():
    return render_template('password_form.html')


@app.route('/', methods=['POST'])
def set_password():
    token = request.args.get('token')
    password = request.form['password']

    if not token or not password:
        raise BadRequestException

    _set_password(token, password)


def _set_password(token, password):
    # Find user for token
    user = User.find(token)

    if user is None:
        raise TokenNotFoundException

    if user.changed:
        raise PasswordAlreadyChangedException

    user.changed = True
    db.session.commit()
    # Login with old_password and set_password in OpenStack to the new one
    pass


db.create_all()

if __name__ == '__main__':
    app.run()
