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
    'version': '0.2',
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
        uses the queue system introduced by the OpenERP Connector to handle a
        big quantity of moves in batch.

        The module account_default_draft_move introdoces a workflow where the
        Journal Entries are always entered in OpenERP in draft state, and the
        posting happens later, for example at the end of the period. The core
        account module provides a wizard to post all the moves in the period,
        but that is problematic when there are many moves.

        The posting of a move takes some time, and doing that synchronously,
        in one transaction is problematic.

        In this module, we leverage the power of the queue system of the
        OpenERP Connector, that can be very well used without other concepts
        like Backends and Bindings.

        This approach provides many advantages, similar to the ones we get
        using that connector for e-commerce:

        - Asynchronous: the operation is done in background, and users can
          continue to work.
        - Dedicated workers: the queued jobs are performed by specific workers
          (processes). This is good for a long task, since the main workers are
          busy handling HTTP requests and can be killed if operations take
          too long, for example.
        - Multiple transactions: this is an operation that doesn't need to be
          atomic, and if a line out of 100,000 fails, it is possible to catch
          it, see the error message, and fix the situation. Meanwhile, all
          other jobs can proceed.

    """,
    'website': 'http://www.camptocamp.com',
    'data': [
        'account_view.xml',
        'wizard/move_marker_view.xml',
    ],
    'test': [
        'test/batch_validate.yml',
        'test/batch_validate_then_unmark.yml',
        'test/batch_validate_then_delete_move.yml',
    ],
    'installable': True,
    'images': [],
    'license': 'AGPL-3',
}
