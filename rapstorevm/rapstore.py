# -*- coding:utf-8 -*-
"""Rapstore

Project repository: https://github.com/riot-appstore/rapstore
"""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import os.path

from io import BytesIO

from fabric.api import task, run, sudo, put, execute
from fabric.contrib.files import sed
from fabric.context_managers import cd

from . import common
from .config import server_config as config

CUR_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = "/home/root"


@task
def setup():
    """Setup RIOT AppMarket"""
    common.apt_install('python-mysqldb')
    common.apt_install('python-pip')

    run('pip install pycrypto')
    execute(setup_apache)
    execute(setup_www_data)

    # Debugging library
    run('pip install q')


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

@task
def setup_apache():
    """Setup apache server."""
    site = '000-default.conf'
    rapstore_conf = '/etc/apache2/sites-available/%s' % site

    common.apt_install('apache2')
    sudo('a2enmod cgi')
    sudo('a2enmod proxy_http')

    put(common.template('rapstore/apache2/%s' % site), config.RAPSTORE_WEBSITE_ROOT, use_sudo=True)
    sed(rapstore_conf, 'DOCUMENT_ROOT', config.RAPSTORE_WEBSITE_DOCUMENT_ROOT, use_sudo=True)
    sed(rapstore_conf, 'RESOURCES_ROOT', config.RAPSTORE_WEBSITE_ROOT, use_sudo=True)
    sudo('a2ensite %s' % site)

    execute(setup_rapstore)
    execute(setup_database)
    execute(update_database)

    sudo('systemctl restart apache2')


@task
def setup_rapstore():
    """Setup RIOT AM application."""
    _setup_rapstore_website_repository()
    _setup_rapstore_backend()


def _setup_rapstore_website_repository(directory=config.RAPSTORE_WEBSITE_ROOT, version='master'):
    """Clone website."""
    common.clone_repo(config.RAPSTORE_WEBSITE_REPO, directory, version, run_as_user='www-data')

    # setup config file with password
    path_to_config = os.path.join(directory, 'rapstore_website', 'config')
    config_file = os.path.join(path_to_config, 'config.py')
    sudo('cp {src} {dst}'.format(src=os.path.join(path_to_config, 'config_EXAMPLE.py'),
                                 dst=config_file))

    # replace password in config file inline
    common.replace_word_in_file(config_file, 'PASSWORD_WEBSITE', config.RAPSTORE_WEBSITE_DB_PASSWORD)
    common.replace_word_in_file(config_file, 'YOUR_SECRET_KEY', config.GITHUB_SECRET_KEY)

    writeable_dirs = ['log']
    with cd(directory):
        dirs = ' '.join(writeable_dirs)
        sudo('mkdir -p %s' % dirs)
        sudo('chown www-data %s' % dirs)

    put(os.path.join(CUR_DIR, os.pardir,'website.pem'), directory, use_sudo=True)

    path_website_key = os.path.join(directory, 'website.pem')

    sudo('chmod 600 %s' % path_website_key)
    sudo('chown www-data:www-data %s' % path_website_key)


def _deploy_rapstore(branch_name, env_file, folder_name=None, dirty=None):
    execute(setup_www_data)
    folder_name = folder_name if folder_name else branch_name
    folder=os.path.join(config.WWW_HOME,folder_name)
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
    folder=os.path.join(config.WWW_HOME,folder_name)
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
    if(_validate_folder(folder)):
        _populate_db(folder)

@task
def createsuperuser(folder="develop"):
    if(_validate_folder(folder)):
        _createsuperuser(folder)

def _setup_rapstore_backend(directory=config.RAPSTORE_BACKEND, version='master'):
    """Clone backend which clones RIOT.

    Setup write permissions on required directories.
    """
    common.clone_repo(config.RAPSTORE_BACKEND_REPO, directory, version, '--recursive', run_as_user='www-data')
    sudo('chmod -R g-w %s' % directory)  # TODO: fixup in the repository

    # setup config file with password
    config_file_config = os.path.join(os.path.join(directory, 'rapstore_backend', 'config', 'config.py'))
    config_file_setup = os.path.join(os.path.join(directory, 'rapstore_backend', 'setup', 'db_config.py'))

    sudo('cp {src} {dst}'.format(src=os.path.join(directory, 'rapstore_backend', 'config', 'config_EXAMPLE.py'),
                                 dst=config_file_config))

    sudo('cp {src} {dst}'.format(src=os.path.join(directory, 'rapstore_backend', 'setup', 'db_config_EXAMPLE.py'),
                                 dst=config_file_setup))

    # replace password in config file inline
    common.replace_word_in_file(config_file_config, 'PASSWORD_BACKEND', config.RAPSTORE_BACKEND_DB_PASSWORD)
    common.replace_word_in_file(config_file_config, 'PASSWORD_WEBSITE', config.RAPSTORE_WEBSITE_DB_PASSWORD)

    common.replace_word_in_file(config_file_setup, 'PASSWORD_BACKEND', config.RAPSTORE_BACKEND_DB_PASSWORD)
    common.replace_word_in_file(config_file_setup, 'PASSWORD_WEBSITE', config.RAPSTORE_WEBSITE_DB_PASSWORD)

    common.replace_word_in_file(config_file_setup, 'USER_PRIVILEGED', config.DB_USER)
    common.replace_word_in_file(config_file_setup, 'PASSWORD_PRIVILEGED', config.DB_PASSWORD)

    _setup_riot_stripped(os.path.join(directory, 'rapstore_backend'))
    _setup_rapstore_backend_writeable_directories(directory)


def _setup_riot_stripped(directory):
    """Create RIOT_stripped for the backend."""
    with cd(directory):
        sudo('python strip_riot_repo.py')


def _setup_rapstore_backend_writeable_directories(directory):
    """Setup the writeable directories required by the backend."""
    # TODO set this configurable somehow
    writeable_dirs = ['tmp', 'log', 'RIOT/generated_by_rapstore']
    with cd(directory):
        dirs = ' '.join(writeable_dirs)
        sudo('mkdir -p %s' % dirs)
        sudo('chown www-data %s' % dirs)


@task
def setup_database():
    """Setup database.

    Install and init tables.
    """
    common.apt_install('mysql-server')

    # Scripts expects to be run from the setup directory
    with cd(os.path.join(config.RAPSTORE_BACKEND, 'rapstore_backend', 'setup')):

        sudo('python %s' % 'db_create.py')
        sudo('python %s' % 'db_setup.py')


@task
def update_database():
    """Update database with RIOT information."""
    with cd(os.path.join(config.RAPSTORE_BACKEND, 'rapstore_backend', 'tasks', 'database')):
        sudo('python %s' % 'db_update.py')
