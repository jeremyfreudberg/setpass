import datetime
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

    def test_internal_wrong_token(self, user):
        wrong_token = 'wrong_token'
        assert wrong_token != user.token

        with pytest.raises(setpass.TokenNotFoundException):
            setpass._set_password(wrong_token, 'password2')

    def test_internal_set_password_twice(self, user):
        setpass._set_password(user.token, 'new_password')
        with pytest.raises(setpass.TokenNotFoundException):
            setpass._set_password(user.token, 'another_new_password')

    # API Tests
    def test_add(self, app):
        # Create a new user
        user_id = str(uuid.uuid4())
        password = str(uuid.uuid4())

        with freezegun.freeze_time("2016-01-01"):
            timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user_id, data=password)
        assert r.status_code == 200
        token = r.data

        # Ensure we get a match
        user = setpass.User.find(token=token)
        assert user.user_id == user_id
        assert user.password == password
        assert timestamp == user.updated_at

        # Calling add again should update the record...
        password = 'NEW_NEW_PASS'

        with freezegun.freeze_time("2016-01-10"):
            new_timestamp = datetime.datetime.utcnow()
            r = app.put('/token/%s' % user_id, data=password)

        assert user.user_id == user_id
        assert user.password == password
        assert user.token == r.data
        assert r.status_code == 200
        assert user.updated_at != timestamp
        assert user.updated_at == new_timestamp

        # ...and old token should be invalidated
        r = app.post('/?token=%s' % token, data={'password': 'NEW_NEW_PASS'})
        assert r.status_code == 404

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
        expired_time = user.updated_at + \
                       datetime.timedelta(seconds=setpass.EXPIRES_AFTER_SECONDS + 5)

        # Set time to 5 seconds after token expiration
        with freezegun.freeze_time(expired_time):
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
