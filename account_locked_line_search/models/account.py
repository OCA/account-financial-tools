# -*- coding: utf-8 -*-
# Copyright 2017 Access Bookings Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    locked = fields.Boolean(related='move_id.locked')
