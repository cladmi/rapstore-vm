#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import (unicode_literals)

import os

SERVER = 'IP_ADDRESS'

SSH_USER = 'SSH_USER'

WWW_HOME = '/var/www'

RAPSTORE_DJANGO = os.path.join(WWW_HOME, 'rapstore-django')
RAPSTORE_DJANGO_REPO = 'https://github.com/riot-appstore/rapstore-django'
