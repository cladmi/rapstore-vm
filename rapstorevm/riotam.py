# -*- coding:utf-8 -*-
"""RIOT AppMarket

Project repository: https://github.com/HendrikVE/riotam
"""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import os.path

from fabric.api import task, sudo, put, execute
from fabric.contrib.files import sed

from . import common


@task
def setup():
    """Setup RIOT AppMarket"""
    common.apt_install('python-mysqldb')
    execute(setup_apache)


@task
def setup_apache():
    """Setup apache server."""
    site = '000-default.conf'
    document_root = '/var/www/riotam-website'
    riotamconf = '/etc/apache2/sites-available/%s' % site

    common.apt_install('apache2')
    sudo('a2enmod cgi')

    put(common.template('riotam/apache2/%s' % site), riotamconf, use_sudo=True)
    sed(riotamconf, 'DOCUMENT_ROOT', document_root, use_sudo=True)
    sudo('a2ensite %s' % site)

    sudo('mkdir -p %s' % document_root)
    put(common.template('riotam/apache2/riotam_default_index.py'),
        os.path.join(document_root, 'index.py'), use_sudo=True,
        mode=0o0755)

    sudo('systemctl restart apache2')
