# -*- coding:utf-8 -*-
"""Fabric file to setup rapstore virtual machine.

The script is meant to be safe to run againts an already setup server.
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)


import os.path
import os
from fabric.api import env, task, execute
from fabric.api import run, sudo
from fabric.contrib.files import append
from fabric.context_managers import cd
import fabric.utils

from rapstorevm import common
from rapstorevm import rapstore
from rapstorevm.config import server_config as config

# Make 'builder' tasks visible here
from rapstorevm import builder

# Disable warnings for 'cd'
# pylint:disable=not-context-manager


OPTBASHRC = '/opt/bashrc'

env.host_string = config.SERVER
env.user = config.SSH_USER


@task
def setup():
    """Setup the virtual machine."""
    run('echo "Running setup..."')
    execute(setup_known_hosts)
    execute(setup_python)
    execute(setup_git)
    execute(setup_docker)
    execute(setup_riot_build_tools)
    execute(builder.setup)


@task
def pull_or_clone_django():
    env_branch=os.environ.get('BRANCH')
    branch= env_branch if env_branch is not None else 'master'
    execute(rapstore.setup_www_data)
    with cd(config.WWW_HOME):
        common.pull_or_clone(config.RAPSTORE_DJANGO_REPO, 'rapstore-django', branch, '', run_as_user='www-data')


@task
def deploy_docker():
    execute(pull_or_clone_django)

    with cd(config.RAPSTORE_DJANGO):
        common.docker_refresh()


@task
def deploy_prod():
    rapstore._deploy_rapstore('master', '.env.prod')


@task
def deploy_staging(dirty=None):
    rapstore._deploy_rapstore('master', '.env.staging', folder_name='staging', dirty=dirty)


@task
def deploy_dev(branch, dirty=None):
    rapstore._deploy_rapstore(branch, '.env.dev', folder_name='develop', dirty=dirty)


@task
def create_superuser():
    with cd(config.RAPSTORE_DJANGO):
        run('echo "Creating superusers"')
        common.docker_shell('web', 'python manage.py createsuperuser')


@task
def populate_db():
    with cd(config.RAPSTORE_DJANGO):
        run('echo "Populating DB"')
        common.docker_shell('web', 'python manage.py populate_db')


GITHUB_RSA_KEY = (
    'AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYP'
    'CPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNl'
    'GEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5'
    'QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmp'
    'aaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy2'
    '8G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ=='
)
# Generate these with 'ssh -o HashKnownHosts=no {host} -p {port}'
# and check known_hosts file
HOSTS = (
    ('github.com,192.30.253.113', 'ssh-rsa', GITHUB_RSA_KEY),
    ('github.com,192.30.253.112', 'ssh-rsa', GITHUB_RSA_KEY),
)


@task
def setup_known_hosts(hosts=HOSTS):
    """Setup .ssh/known_hosts file.

    Allows doing ssh/git without having to validate server host key.
    """
    for host_tuple in hosts:
        fabric.utils.puts('Registering Host {0}'.format(host_tuple[0]))
        append('.ssh/known_hosts', ' '.join(host_tuple))


@task
def setup_python():
    """Install python dependencies."""
    common.apt_install('python')


@task
def setup_git():
    """Install git."""
    common.apt_install('git')


@task
def setup_docker():
    """Install Docker."""
    common.apt_install('docker')
    common.apt_install('docker-compose')


@task
def setup_riot_build_tools():
    """Install riot build tools."""
    common.apt_install('build-essential')
    common.apt_install('unzip')
    _install_riot_native_build()
    _install_arm_gcc()
    _install_msp430()
    _install_mips_gcc()
    _install_avr()


def _install_riot_native_build():
    """Install build tools for native."""
    common.apt_install('libc6-dev-i386')


def _install_arm_gcc():
    """Install arm gcc from launchpad ppa."""
    sudo('add-apt-repository -uy ppa:team-gcc-arm-embedded/ppa')
    common.apt_install('gcc-arm-embedded')


def _install_msp430():
    """Install msp430 gcc.

    Use the repository version as sourceforge one is tricky to install
    and the newest version is not yet supported.
    """
    common.apt_install('gcc-msp430')


MIPS_GCC = ('https://community.imgtec.com/?do-download='
            'linux-x64-mti-bare-metal-{version}')


def _install_mips_gcc(version='2016.05-03'):
    """Install mips gcc."""
    url_version = version.replace('.', '-')
    url = MIPS_GCC.format(version=url_version)

    archive = 'mips-gcc-%s.tar.gz' % url_version
    archive_out = 'mips-mti-elf'
    bindir = os.path.join('/opt', archive_out, version, 'bin')

    with cd('/opt'):
        sudo('wget -c %s -O %s' % (url, archive))
        sudo('tar xvf %s' % archive)
        sudo('chmod -R a+r %s' % archive_out)
    append(OPTBASHRC, 'export PATH="%s:${PATH}"' % bindir, use_sudo=True)


def _install_avr():
    """Install avr gcc."""
    common.apt_install('gcc-avr avr-libc')
