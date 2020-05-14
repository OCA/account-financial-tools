# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.api import Environment, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    account_move_obj = env['account.move']
    account_move = account_move_obj.search([])
    for move in account_move:
        origin = account_move_obj.search([('ref', '=', move.name)])
        #_logger.info("ORIGIN %s" % origin)
        if origin:
            origin.origin_move_id = move
