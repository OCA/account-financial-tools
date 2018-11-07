# -*- coding: utf-8 -*-
# See LICENSE for licensing information

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class BankAccount(models.Model):
    _inherit = 'res.partner.bank'
    _sql_constraints = [('unique_number',
                         'CHECK(1=1)',
                         'Please contact tech@avoin.systems is you see this')]

    override_uniqueness = fields.Boolean(
        "Override Uniqueness",
        help="Overrides bank account number uniqueness constraint",
    )

    @api.constrains('company_id',
                    'sanitized_acc_number',
                    'override_uniqueness')
    def _check_account_uniqueness(self):
        records = self.filtered(lambda x: not x.override_uniqueness)
        errors = []

        for r in records:
            duplicate_count = r.search_count([
                ('company_id', '=', r.company_id.id),
                ('sanitized_acc_number', '=', r.sanitized_acc_number),
                ('id', '!=', r.id),
                ('override_uniqueness', '=', False)])

            if duplicate_count:
                errors.append(r.sanitized_acc_number)

        if errors:
            raise models.ValidationError(
                u'Account number must be unique. '
                u'The following accounts have duplicates: {}'
                .format(", ".join(errors)))
