# -*- coding:utf-8 -*-
"""Installation for the builder.

HACK it is currently run on the host.
TODO It should be updated to a docker container with
     all the build dependencies.

* Install builder and virtualenv in `/home/builder` as root.
* Run as `builder` in a `tmux` context (its cheating I know)
* Logs go to /home/builder/logs
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time

from fabric.api import task
from fabric.api import run, sudo
from fabric.context_managers import cd

from rapstorevm import common


BUILDER_USER = 'builder'
BUILDER_HOME = '/home/{user}'.format(user=BUILDER_USER)
BUILDER_REPO = 'https://github.com/riot-appstore/rapstore-builder'
BUILDER_DIR = '{home}/rapstore-builder'.format(home=BUILDER_HOME)
BUILDER_VENV = '{home}/venv'.format(home=BUILDER_HOME)
BUILDER_LOGDIR = '{home}/logs'.format(home=BUILDER_HOME)

TMUX_SESSION = 'rapstore-builder'

# TODO Do not listen on all interfaces… (not eth0)
# Should be solved when using docker no need to do iptables
BUILDER_LISTEN_ADDR = '0.0.0.0'
BUILDER_PORT = '8080'


@task
def setup(branch='master'):
    """Setup the builder service.

    * Lazy create builder user
    * Stop builder if was running
    * Install builder and virtualenv in `/home/builder` as root.
    * Run as `builder` in a `tmux` context (its cheating I know)
    * Logs go to /home/builder/logs
    """
    _create_builder_user()
    _stop_builder_tmux()
    _setup_builder(branch)
    _start_builder_tmux()


@task
def start():
    """Start builder. Should be stopped"""
    _start_builder_tmux()


@task
def stop():
    """Stop builder."""
    _stop_builder_tmux()


def _start_builder_tmux():
    """Start builder in a tmux session."""
    # TODO replace by a real start mechanism in docker
    command = ('source {venv}/bin/activate &&'
               ' rapstore-builder {addr} {port} --logdir={logdir};'
               ' read WAIT_FOR_DEBUG')
    command = command.format(addr=BUILDER_LISTEN_ADDR, port=BUILDER_PORT,
                             venv=BUILDER_VENV, logdir=BUILDER_LOGDIR)

    cmd = 'tmux new-session -d -s {s} "bash -c \'{cmd}\'"'
    sudo(cmd.format(s=TMUX_SESSION, cmd=command),
         user=BUILDER_USER, pty=False)
    # Test server is running
    time.sleep(5)  # Hard 5 seconds wait
    run('curl http://localhost:{port}/hello'.format(port=BUILDER_PORT))


def _stop_builder_tmux():
    """Stop builder."""
    sudo('tmux kill-session -t {s}'.format(s=TMUX_SESSION),
         user=BUILDER_USER, warn_only=True)


def _create_builder_user():
    """Create a 'builder' user on the host.

    Created as 'normal' user because its required for tmux...
    """
    cmd = 'useradd -m -d {home} {user}'.format(user=BUILDER_USER,
                                               home=BUILDER_HOME)
    sudo(cmd, warn_only=True)


def _setup_builder(branch):
    common.clone_repo(BUILDER_REPO, BUILDER_DIR, branch, run_as_user='root')
    _setup_virtualenv(BUILDER_VENV, BUILDER_DIR)
    sudo('mkdir -p {logdir}'.format(logdir=BUILDER_LOGDIR), user=BUILDER_USER)


def _setup_virtualenv(venvdir, setupdir, python='python3'):
    """Setup a virtualenv in `venvdir` and install package from `setupdir`.

    Installation is done as `root`.
    """
    # Install as root (not modifiable by BUILDER_USER by user)
    sudo('virtualenv --python={p} {env}'.format(env=venvdir, p=python))
    with cd(setupdir):  # pylint:disable=not-context-manager
        cmd = 'source {env}/bin/activate && pip install {repo}'
        sudo(cmd.format(env=venvdir, repo=setupdir))
