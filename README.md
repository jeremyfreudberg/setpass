# setpass

Microservice that provides users with a easy interface to set their first
OpenStack password.

When registering for the cloud service (registration not included in this
script) the user provides a secret 4-digit pin. They need to remember this
pin as it will be used as the second factor when authenticating for the first
time.

The administrator receives and approves the registration request, and
creates an OpenStack account with a random password. The administrator then
adds the user_id and password to setpass, receiving a token in response. This
will be the first factor of authentication, and its time validity is set in
the configuration file.

This token is sent to the user as part of a url, for example:

``https://example.com/?token=c35ee31e-3ee2-4a38-9eae-e738bafdccb5``

The user will input the his 4-digit pin, and his desired password.

What setpass then does, is use the random admin assigned password to login to
the OpenStack Identity service and change the password to the user-provided
one.

## Usage

To run it:

```
# Possibly in a virtual environment
$ pip install -r requirements.txt
$ python -m setpass.api
```

### Adding a new user:

| URL      | /token/<user_id>                               |
|----------|------------------------------------------------|
| Method   | PUT                                            |
| Headers  | X-Auth-Token                                   |
| Body     | {password: <random_pass>, pin: <user_pin>}     |
| Response | Token

Please note, to authorize the request to add a new user, setpass checks for a
valid token in ``x-auth-token``. If it is able to use this token to scope to
the admin project, then the call is authorized.

The response to this call is the token that will be sent to the user. Please
note, this is not a valid OpenStack token. This is only to authenticate back
to the setpass service.

This call is idempotent, and can be repeated to set a new pin or password.
In each of these cases (including the case with empty json body), a new token
will be generated. So this can be used to renew the token if they expire.

Alternatively, to make the call through the API, you can instantiate a new
keystoneauth session:

```python
from keystoneauth1.identity import v3
from keystoneauth1 import session

# Create a new keystoneauth auth object, it doesn't need to be scoped to
# any project, but the user needs to have a role in the admin project.
auth = v3.Password(auth_url=<https://example.com:5000/v3>,
                   username=<admin_username>,
                   user_domain_id='default',
                   password=<admin_password>)

sess = session.Session(auth=auth)

body = json.dumps({ 'password': <openstack_password>, 'pin': <user_pin> })
r = sess.post('https://example.com/token/%s' % <user_id>, body=body)

# this is the token that will be sent to the user
token = r.text
```
