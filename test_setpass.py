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
            password=str(uuid.uuid4()),
            changed=False
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

    def test_wrong_token(self, user):
        wrong_token = 'wrong_token'
        assert wrong_token != user.token

        with pytest.raises(setpass.TokenNotFoundException):
            setpass._set_password(wrong_token, 'password2')

    def test_set_password(self, user):
        assert not user.changed

        # Calling set password sets the changed value to true
        setpass._set_password(user.token, 'new_password')
        assert user.changed

        # You can't change password twice
        with pytest.raises(setpass.PasswordAlreadyChangedException):
            setpass._set_password(user.token, 'another_new_password')

