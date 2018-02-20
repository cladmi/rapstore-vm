#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import (unicode_literals)

import os

SERVER = 'IP_ADDRESS'

SSH_USER = 'SSH_USER'

WWW_HOME = '/var/www'

GITHUB_SECRET_KEY = 'SECRET_KEY'

RAPSTORE_WEBSITE_ROOT = os.path.join(WWW_HOME, 'rapstore-website')
RAPSTORE_WEBSITE_DOCUMENT_ROOT = os.path.join(RAPSTORE_WEBSITE_ROOT, 'rapstore_website')
RAPSTORE_WEBSITE_REPO = 'https://github.com/HendrikVE/rapstore-website'
RAPSTORE_WEBSITE_DB_PASSWORD = 'PASSWORD_WEBSITE'

RAPSTORE_BACKEND = os.path.join(WWW_HOME, 'rapstore-backend')
RAPSTORE_BACKEND_REPO = 'https://github.com/HendrikVE/rapstore-backend'
RAPSTORE_BACKEND_DB_PASSWORD = 'PASSWORD_BACKEND'

RAPSTORE_DJANGO = os.path.join(WWW_HOME, 'rapstore-django')
RAPSTORE_DJANGO_REPO = 'https://github.com/riot-appstore/rapstore-django'

DB_USER = 'root'
DB_PASSWORD = 'PASSWORD_DB_ROOT'
