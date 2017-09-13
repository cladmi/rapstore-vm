#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""Default example from

https://www.linux.com/blog/configuring-apache2-run-python-scripts
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import cgitb
cgitb.enable()

print('Content-Type: text/html;charset=utf-8')
print()
print('Hello World!')
