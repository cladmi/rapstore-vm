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
