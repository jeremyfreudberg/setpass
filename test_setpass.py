import pytest
import uuid

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
        r = app.put('/token/%s' % user_id, data=password)
        assert r.status_code == 200
        token = r.data

        # Ensure we get a match
        user = setpass.User.find(token)
        assert user.user_id == user_id
        assert user.password == password

    def test_set_pass(self, app, user):
        r = app.post('/?token=%s' % user.token, data={'password': 'NEW_PASS'})
        assert r.status_code == 200

        user = setpass.User.find(token=user.token)
        assert user is None

    def test_set_password_twice(self, app, user):
        r = app.post('/?token=%s' % user.token, data={'password': 'NEW_PASS'})
        assert r.status_code == 200

        r = app.post('/?token=%s' % user.token, data={'password': 'NEW_PASS'})
        assert r.status_code == 404

    def test_wrong_token(self, app):
        r = app.post('/?token=%s' % 'WRONG_TOKEN', data={'password': 'NEW_PASS'})
        assert r.status_code == 404

    def test_no_arguments(self, app):
        r = app.post('/?token=%s' % 'TOKEN')
        assert r.status_code == 400

        r = app.post('/', data={'password': 'NEW_PASS'})
        assert r.status_code == 400
