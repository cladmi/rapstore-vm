#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import (unicode_literals)

import os

SERVER = 'IP_ADDRESS'

SSH_USER = 'SSH_USER'

WWW_HOME = '/var/www'

RIOTAM_ROOT = os.path.join(WWW_HOME, 'riotam-website')
RIOTAM_WEBSITE_REPO = 'https://github.com/HendrikVE/riotam-website'
RIOTAM_WEBSITE_DB_PASSWORD = 'PASSWORD_WEBSITE'

RIOTAM_BACKEND = os.path.join(WWW_HOME, 'riotam-backend')
RIOTAM_BACKEND_REPO = 'https://github.com/HendrikVE/riotam-backend'
RIOTAM_BACKEND_DB_PASSWORD = 'PASSWORD_BACKEND'

DB_USER = 'root'
DB_PASSWORD = 'PASSWORD_DB_ROOT'
