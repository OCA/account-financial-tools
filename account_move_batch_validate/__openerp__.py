# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Author: Leonardo Pistone
#   Copyright 2014 Camptocamp SA
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
{
    'name': "Account Move Batch Validate",
    'version': '0.1',
    'author': 'Camptocamp',
    'maintainer': 'Camptocamp',
    'category': 'Finance',
    'complexity': 'normal',
    'depends': [
        'account',
        'account_default_draft_move',
        'connector',
    ],
    'description': """
        Account Move Batch Validate

        This module provides a wizard to post many Journal Entries in batch. it
        uses the queue system introduces by the OpenERP Connector to handle a
        big quantity of moves in batch.
    """,
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [
        'account_view.xml',
        'wizard/move_marker_view.xml',
    ],
    'demo_xml': [],
    'test': [
        'test/batch_validate.yml'
    ],
    'installable': True,
    'images': [],
    'license': 'AGPL-3',
}
