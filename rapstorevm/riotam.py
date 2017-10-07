# -*- coding:utf-8 -*-
"""RIOT AppMarket

Project repository: https://github.com/HendrikVE/riotam
"""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import os.path

from io import BytesIO

from fabric.api import task, sudo, put, execute
from fabric.contrib.files import sed
from fabric.context_managers import cd

from . import common


WWW_HOME = '/var/www'

RIOTAM_ROOT = os.path.join(WWW_HOME, 'riotam-website')
RIOTAM_WEBSITE_REPO = 'https://github.com/HendrikVE/riotam-website'
RIOTAM_WEBSITE_DB_PASSWORD = 'xuEw2m9De32k'

RIOTAM_BACKEND = os.path.join(WWW_HOME, 'riotam-backend')
RIOTAM_BACKEND_REPO = 'https://github.com/HendrikVE/riotam-backend'
RIOTAM_BACKEND_DB_PASSWORD = '7BdACfnQmWhq'


@task
def setup():
    """Setup RIOT AppMarket"""
    common.apt_install('python-mysqldb')
    execute(setup_apache)
    execute(setup_www_data)


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
def setup_apache():
    """Setup apache server."""
    site = '000-default.conf'
    riotamconf = '/etc/apache2/sites-available/%s' % site

    common.apt_install('apache2')
    sudo('a2enmod cgi')

    put(common.template('riotam/apache2/%s' % site), riotamconf, use_sudo=True)
    sed(riotamconf, 'DOCUMENT_ROOT', RIOTAM_ROOT, use_sudo=True)
    sudo('a2ensite %s' % site)

    execute(setup_riotam)
    execute(setup_database)
    execute(update_database)

    sudo('systemctl restart apache2')


@task
def setup_riotam():
    """Setup RIOT AM application."""
    _setup_riotam_website_repository()
    _setup_riotam_backend()


def _setup_riotam_website_repository(directory=RIOTAM_ROOT, version='master'):
    """Clone website."""
    common.clone_repo(RIOTAM_WEBSITE_REPO, directory, version, run_as_user='www-data')

    # setup config file with password
    config_file = os.path.join(directory, "config", "db_config.py")
    sudo('cp {src} {dst}'.format(src=os.path.join(directory, "config", "db_config_EXAMPLE.py"),
                                 dst=config_file))

    # replace password in config file inline
    common.replace_word_in_file(config_file, 'PASSWORD_WEBSITE', RIOTAM_WEBSITE_DB_PASSWORD)

    writeable_dirs = ['log']
    with cd(directory):
        dirs = ' '.join(writeable_dirs)
        sudo('mkdir -p %s' % dirs)
        sudo('chown www-data %s' % dirs)


def _setup_riotam_backend(directory=RIOTAM_BACKEND, version='master'):
    """Clone backend which clones RIOT.

    Setup write permissions on required directories.
    """
    common.clone_repo(RIOTAM_BACKEND_REPO, directory, version, '--recursive', run_as_user='www-data')
    sudo('chmod -R g-w %s' % directory)  # TODO: fixup in the repository

    # setup config file with password
    config_file_config = os.path.join(os.path.join(directory, "config", "db_config.py"))
    config_file_setup = os.path.join(os.path.join(directory, "setup", "db_config.py"))

    sudo('cp {src} {dst}'.format(src=os.path.join(directory, "config", "db_config_EXAMPLE.py"),
                                 dst=config_file_config))

    sudo('cp {src} {dst}'.format(src=os.path.join(directory, "setup", "db_config_EXAMPLE.py"),
                                 dst=config_file_setup))

    # replace password in config file inline
    common.replace_word_in_file(config_file_config, 'PASSWORD_BACKEND', RIOTAM_BACKEND_DB_PASSWORD)
    common.replace_word_in_file(config_file_config, 'PASSWORD_WEBSITE', RIOTAM_WEBSITE_DB_PASSWORD)

    common.replace_word_in_file(config_file_setup, 'PASSWORD_BACKEND', RIOTAM_BACKEND_DB_PASSWORD)
    common.replace_word_in_file(config_file_setup, 'PASSWORD_WEBSITE', RIOTAM_WEBSITE_DB_PASSWORD)

    _setup_riot_stripped(directory)
    _setup_riotam_backend_writeable_directories(directory)


def _setup_riot_stripped(directory):
    """Create RIOT_stripped for the backend."""
    with cd(directory):
        sudo('python strip_riot_repo.py')


def _setup_riotam_backend_writeable_directories(directory):
    """Setup the writeable directories required by the backend."""
    # TODO set this configurable somehow
    writeable_dirs = ['tmp', 'log', 'RIOT/generated_by_riotam']
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
    with cd(os.path.join(RIOTAM_BACKEND, 'setup')):
        sudo('python %s' % 'db_create.py')
        sudo('python %s' % 'db_setup.py')


@task
def update_database():
    """Update database with RIOT information."""
    with cd(RIOTAM_BACKEND):
        sudo('python %s' % 'db_update.py')
