# -*- coding: utf-8 -*-
# Copyright (C) 2018 Greenbone Networks GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from argparse import Namespace

from gvm import get_version as get_gvm_version
from gvm.protocols.latest import Gmp, Osp
from gvm.transforms import EtreeCheckCommandTransform

from gvmtools import get_version
from gvmtools.helper import authenticate, run_script
from gvmtools.parser import create_parser, create_connection, PROTOCOL_OSP

HELP_TEXT = """
    Command line tool to execute custom GMP (Greenbone Management
    Protocol) and OSP (Open Scanner Protocol) scripts.

    The protocol specifications for GMP and OSP are available at:
      https://docs.greenbone.net/index.html#api_documentation
"""

__version__ = get_version()
__api_version__ = get_gvm_version()


def main():
    parser = create_parser(description=HELP_TEXT, logfilename='gvm-script.log')

    parser.add_protocol_argument()

    parser.add_argument(
        'scriptname',
        metavar="SCRIPT",
        help='Path to script to be executed (example: myscript.gmp)',
    )
    parser.add_argument(
        'scriptargs', nargs='*', metavar="ARG", help='Arguments for the script'
    )

    args = parser.parse_args()

    print(args)

    if 'socket' in args.connection_type and args.sockpath:
        print(
            'The --sockpath parameter has been deprecated. Please use '
            '--socketpath instead',
            file=sys.stderr,
        )

    connection = create_connection(**vars(args))

    transform = EtreeCheckCommandTransform()

    global_vars = {
        '__version__': __version__,
        '__api_version__': __api_version__,
    }

    username = None
    password = None

    if args.protocol == PROTOCOL_OSP:
        protocol = Osp(connection, transform=transform)
        global_vars['osp'] = protocol
        global_vars['__name__'] = '__osp__'
    else:
        protocol = Gmp(connection, transform=transform)
        global_vars['gmp'] = protocol
        global_vars['__name__'] = '__gmp__'

        if args.gmp_username:
            (username, password) = authenticate(
                protocol, username=args.gmp_username, password=args.gmp_password
            )

    argv = [os.path.abspath(args.scriptname), *args.scriptargs]

    shell_args = Namespace(
        username=username,
        password=password,
        argv=argv,
        # for backwards compatibility we add script here
        script=argv,
    )

    global_vars['args'] = shell_args

    run_script(args.scriptname, global_vars)


if __name__ == '__main__':
    main()