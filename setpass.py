from flask import Flask
from flask import request, abort, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True)
    token = db.Column(db.String(64), nullable=False)
    old_password = db.Column(db.String(64), nullable=False)
    changed = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, token, changed=False):
        self.user_id = user_id
        self.token = token
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
        abort(400)

    # Find user for token
    user = User.find(token)
    if user and not user.changed:
        # Login with old_password and set_password in OpenStack to the new one
        pass


if __name__ == '__main__':
    db.create_all()

    u1 = User('id1', 'token1')
    u2 = User('id2', 'token2', changed=False)
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()

    app.run()
