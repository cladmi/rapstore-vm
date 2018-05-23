# -*- coding:utf-8 -*-
"""Rapstore

Project repository: https://github.com/riot-appstore/rapstore
"""


from __future__ import (absolute_import, division, print_function, unicode_literals)

import os.path
from io import BytesIO

from fabric.api import task, sudo, put, execute
from fabric.context_managers import cd

from . import common
from .config import server_config as config

CUR_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = "/home/root"


GITCONFIG = '''\
[user]
\temail = {user}@localhost
\tname = {title} {title}
'''


@task
def setup_www_data():
    """Setup www-data .gitconfig for compiling packages (using git am)."""
    user = 'www-data'
    gitconfig = GITCONFIG.format(user=user, title=user.title())
    config = BytesIO(gitconfig.encode('utf-8'))
    put(config, '/var/www/.gitconfig', use_sudo=True)
    sudo('chown -R www-data:www-data /var/www/')


@task
def setup_nginx():

    put("nginx", "/var/www", use_sudo=True)
    sudo('chown -R www-data:www-data /var/www')

    with cd("/var/www/nginx"):
        sudo('cp /etc/letsencrypt/live/demo.riot-apps.net/$(readlink /etc/letsencrypt/live/demo.riot-apps.net/fullchain.pem) /home/root/ssl/fullchain.pem')
        sudo('cp /etc/letsencrypt/live/demo.riot-apps.net/$(readlink /etc/letsencrypt/live/demo.riot-apps.net/privkey.pem) /home/root/ssl/privkey.pem')
        sudo('docker stop nginx || true')
        sudo('docker rm nginx || true')
        sudo('docker build -t nginx .')
        sudo('docker run -d -v /home/root/ssl:/etc/nginx/certs --net=host --name nginx -t nginx')


def _deploy_rapstore(branch_name, env_file, folder_name=None, dirty=None):

    execute(setup_www_data)
    folder_name = folder_name if folder_name else branch_name
    folder = os.path.join(config.WWW_HOME,folder_name)
    sudo('mkdir -p %s' % folder)
    sudo('chown www-data %s' % folder)

    with cd(folder):
        common.pull_or_clone(config.RAPSTORE_DJANGO_REPO, 'rapstore-django', branch_name, '', run_as_user='www-data')
        if not dirty:
            put('docker-compose.yml', os.path.join(folder, "docker-compose.yml"), use_sudo=True)
            put(env_file, os.path.join(folder, ".env"), use_sudo=True)
            sudo("cat {0}/.oauth.{1} >> .env ".format(ROOT_DIR, folder_name))
            common.docker_refresh()


def _populate_db(folder_name):

    folder = os.path.join(config.WWW_HOME,folder_name)

    with cd(folder):
        sudo('docker-compose exec web python manage.py populate_db')


def _createsuperuser(folder_name):

    folder=os.path.join(config.WWW_HOME,folder_name)

    with cd(folder):
        sudo('docker-compose exec web python manage.py createsuperuser')


def _validate_folder(folder_name):

    if folder_name not in ["develop", "master", "staging"]:
        return False

    return True


@task
def populate_db(folder="develop"):

    if _validate_folder(folder):
        _populate_db(folder)


@task
def createsuperuser(folder="develop"):

    if _validate_folder(folder):
        _createsuperuser(folder)
