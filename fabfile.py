# -*- coding:utf-8 -*-
"""Fabric file to setup rapstore virtual machine.

The script is meant to be safe to run againts an already setup server.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


from fabric.api import env, task, execute
from fabric.api import run, sudo
from fabric.contrib.files import append
import fabric.utils

from rapstorevm import common
from rapstorevm import riotam


SERVER = '141.22.28.91'

env.host_string = SERVER


@task
def setup():
    """Setup the virtual machine."""
    run('echo "Hello World"')
    execute(setup_known_hosts)
    execute(setup_python)
    execute(setup_git)
    execute(setup_riot_build_tools)
    execute(riotam.setup)


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
def setup_riot_build_tools():
    """Install riot build tools."""
    common.apt_install('build-essential')
    common.apt_install('unzip')
    _install_arm_gcc()


def _install_arm_gcc():
    sudo('add-apt-repository -uy ppa:team-gcc-arm-embedded/ppa')
    common.apt_install('gcc-arm-embedded')
