# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.fields import Date
from datetime import datetime, timedelta


class MoveLocking(common.TransactionCase):

    def setUp(self):
        super(MoveLocking, self).setUp()
        self.cust_invoices_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('code', '=', 'INV')
        ])
        self.entries = self.env['account.move'].search([
            ('journal_id', '=', self.cust_invoices_journal.id)
        ])

    def test_locking(self):
        vals = {
            'journal_ids': [(4, self.cust_invoices_journal.id, 0)],
            'date_start': Date.to_string(datetime.now() - timedelta(days=365)),
            'date_end': Date.today(),
        }
        lock_wiz = self.env['lock.account.move'].create(vals)
        lock_wiz.lock_move({})
        for move in self.entries:
            self.assertTrue(move.locked)
