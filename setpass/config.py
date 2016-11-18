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

from os import path

from oslo_config import cfg

CONF = cfg.CONF

default_opts = [
    cfg.StrOpt('database',
               default='sqlite:///',
               help='Database uri'),

    cfg.IntOpt('port',
               default=5001,
               help='Web server port number.'),

    cfg.StrOpt('auth_url',
               default='http://localhost:5000',
               help='Identity service authentication url.'),

    cfg.IntOpt('token_expiration',
               default=False,
               help='Time in seconds that a token is valid.'),
]

CONF.register_opts(default_opts)


def load_config():
    """Load parameters from the proxy's config file."""
    conf_files = [f for f in ['setpass.conf',
                              'etc/setpass.conf',
                              '/etc/setpass.conf'] if path.isfile(f)]
    if conf_files is not []:
        CONF(default_config_files=conf_files)


load_config()
