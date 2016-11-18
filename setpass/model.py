#   Copyright 2016 Massachusetts Open Cloud
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import datetime

from flask_sqlalchemy import SQLAlchemy

from setpass import wsgi
from setpass import config

CONF = config.CONF

wsgi.app.config['SQLALCHEMY_DATABASE_URI'] = CONF['database']
db = SQLAlchemy(wsgi.app)


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
