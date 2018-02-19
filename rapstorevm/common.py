# -*- coding:utf-8 -*-
"""Common functions."""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
from fabric.api import sudo, runs_once, execute


TEMPLATE_DIR = 'rapstorevm/template'


def template(*args):
    """Template file path."""
    return os.path.join(TEMPLATE_DIR, *args)


@runs_once
def apt_update():
    """apt-get update"""
    sudo('apt-get update -yqq')


def apt_install(packages, options=''):
    """Install packages in non-interactive mode."""
    execute(apt_update)
    install = 'DEBIAN_FRONTEND=noninteractive apt-get install {0} -yqq {1}'
    sudo(install.format(options, packages))


def clone_repo(repo, directory='', branch='master', options='', run_as_user=None):
    """Clone repository.

    Currently delete it before cloning.
    """
    sudo('rm -rf %s' % directory)
    
    cmd = 'git clone {options} --quiet {repo} --branch {branch} {dir}'.format(repo=repo, branch=branch, dir=directory, options=options)
    sudo(cmd, user=run_as_user)

def pull_or_clone(repo, directory='', branch='master', options='', run_as_user=None):
    cmd = 'git -C {dir} pull --quiet 2>/dev/null || git clone {options} --quiet {repo} --branch {branch} {dir}'.format(repo=repo, branch=branch, dir=directory, options=options)
    sudo(cmd, user=run_as_user)

def replace_word_in_file(file, original, replacement):
    """Replace a pattern with another word, using sed"""
    sudo('sed -i "s/{original}/{replacement}/g" {file}'.format(original=original,
                                                               replacement=replacement,
                                                               file=file))

def docker_refresh():
    sudo('docker-compose  stop || true')
    sudo('docker-compose rm --force')
    sudo('docker-compose build')
    sudo('docker-compose up')
