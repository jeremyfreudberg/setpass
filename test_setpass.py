import datetime
import json
import uuid

import pytest
import freezegun

import setpass

setpass.db.create_all()


class TestSetpass(object):
    @staticmethod
    def create(changed=False):
        user = setpass.User(
            user_id=str(uuid.uuid4()),
            token=str(uuid.uuid4()),
            pin='1234',
            password=str(uuid.uuid4())
        )
        setpass.db.session.add(user)
        setpass.db.session.commit()
        return user

    @staticmethod
    def delete(user):
        assert isinstance(user, setpass.User)
        setpass.db.session.delete(user)
        setpass.db.session.commit()

    @pytest.fixture
    def user(self):
        user = self.create()
        yield user
        self.delete(user)

    @pytest.fixture()
    def app(self):
        return setpass.app.test_client()

    @staticmethod
    def _get_expired_time(timestamp):
        return timestamp + \
               datetime.timedelta(seconds=setpass.EXPIRES_AFTER_SECONDS + 5)

    # Internal method tests
    def test_internal_wrong_token(self, user):
        wrong_token = 'wrong_token'
        assert wrong_token != user.token

        with pytest.raises(setpass.TokenNotFoundException):
            setpass._set_password(wrong_token, 'password2')

    def test_internal_set_password_twice(self, user):
        setpass._set_password(user.token, 'new_password')
        with pytest.raises(setpass.TokenNotFoundException):
            setpass._set_password(user.token, 'another_new_password')

    def test_internal_expired_token(self, user):
        with freezegun.freeze_time(self._get_expired_time(user.updated_at)):
            with pytest.raises(setpass.TokenExpiredException):
                setpass._set_password(user.token, 'new_password')

    # API Tests
    def test_add_new_user(self, app):
        user_id = str(uuid.uuid4())
        pin = '1234'
        password = str(uuid.uuid4())
        payload = json.dumps({'password': password, 'pin': pin})

        with freezegun.freeze_time("2016-01-01"):
            timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user_id, data=payload)

        user = setpass.User.find(token=r.data)
        assert user.user_id == user_id
        assert user.password == password
        assert user.pin == pin
        assert timestamp == user.updated_at
        assert r.status_code == 200

    def test_add_update_pin(self, app, user):
        old_token = user.token
        new_pin = '9876'
        payload = {'pin': new_pin}

        with freezegun.freeze_time("2016-01-01"):
            timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user.user_id, data=json.dumps(payload))

        assert user.pin == new_pin
        assert user.token != old_token
        assert timestamp == user.updated_at
        assert r.data == user.token
        assert r.status_code == 200

    def test_add_update_password(self, app, user):
        old_token = user.token
        new_password = str(uuid.uuid4())
        payload = {'password': new_password}

        with freezegun.freeze_time("2016-01-01"):
            timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user.user_id, data=json.dumps(payload))

        assert user.password == new_password
        assert user.token != old_token
        assert timestamp == user.updated_at
        assert r.data == user.token
        assert r.status_code == 200

    def test_add_update_pin_and_password(self, app, user):
        pin = '1234'
        password = str(uuid.uuid4())
        payload = json.dumps({'password': password, 'pin': pin})

        with freezegun.freeze_time("2016-01-01"):
            timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user.user_id, data=payload)

        assert user.password == password
        assert user.pin == pin
        assert timestamp == user.updated_at
        assert r.status_code == 200

    def test_set_pass(self, app, user):
        # Change password
        token = user.token
        r = app.post('/?token=%s' % token, data={'password': 'NEW_PASS'})
        assert r.status_code == 200

        # Ensure user record is deleted
        user = setpass.User.find(token=token)
        assert user is None

        # Ensure we get a 404 when reusing the token
        r = app.post('/?token=%s' % token, data={'password': 'NEW_NEW_PASS'})
        assert r.status_code == 404

    def test_set_pass_expired(self, app, user):
        # Set time to after token expiration
        with freezegun.freeze_time(self._get_expired_time(user.updated_at)):
            r = app.post('/?token=%s' % user.token, data={'password': 'NEW_PASS'})

        assert r.status_code == 403

    def test_wrong_token(self, app, user):
        r = app.post('/?token=%s' % 'WRONG_TOKEN', data={'password': 'NEW_PASS'})
        assert r.status_code == 404

    def test_no_arguments(self, app):
        # Token but no password
        r = app.post('/?token=%s' % 'TOKEN')
        assert r.status_code == 400

        # Password but no token
        r = app.post('/', data={'password': 'NEW_PASS'})
        assert r.status_code == 400
