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
import json
import uuid

from flask import Response
from flask import request, render_template
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from setpass import config
from setpass import model
from setpass import wsgi
from setpass import exception

CONF = config.CONF

@wsgi.app.route('/', methods=['GET'])
def view_form():
    return render_template('password_form.html')


@wsgi.app.route('/', methods=['POST'])
def set_password():
    token = request.args.get('token')
    password = request.form['password']
    pin = request.form['pin']

    if not token or not password or not pin:
        return Response(response='Missing token/pin/password!', status=400)

    try:
        _set_password(token, pin, password)
    except exception.TokenNotFoundException:
        return Response(response='Token not found', status=404)
    except exception.TokenExpiredException:
        return Response(response='Token expired', status=403)
    except exception.WrongPinException:
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
    user = model.User.find(token=token)

    if user is None:
        raise exception.TokenNotFoundException

    if pin != user.pin:
        raise exception.WrongPinException

    delta = datetime.datetime.utcnow() - user.updated_at
    if delta.total_seconds() > CONF['token_expiration']:
        raise exception.TokenExpiredException

    # _set_openstack_password(user.user_id, user.password, password)

    model.db.session.delete(user)
    model.db.session.commit()


@wsgi.app.route('/token/<user_id>', methods=['PUT'])
def add(user_id):
    payload = json.loads(request.data)

    user = model.User.find(user_id=user_id)
    if user:
        if 'pin' in payload:
            user.pin = payload['pin']
        if 'password' in payload:
            user.password = payload['password']

        user.token = str(uuid.uuid4())
        user.update_timestamp()
    else:
        user = model.User(
            user_id=user_id,
            token=str(uuid.uuid4()),
            pin=payload['pin'],
            password=payload['password']
        )
        model.db.session.add(user)

    model.db.session.commit()
    return Response(response=user.token, status=200)