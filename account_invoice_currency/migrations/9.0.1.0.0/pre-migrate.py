# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    from openupgradelib import openupgrade
except ImportError:
    openupgrade = False

column_renames = {
    'account_invoice': [
        ('cc_amount_tax', 'amount_tax_signed'),
        # These columns already exists in vanilla Odoo, but we preserve them
        # for checks and other uses
        ('cc_amount_untaxed', None),
        ('cc_amount_total', None),
    ],
}


def migrate(cr, version):
    if not version or not openupgrade:
        return
    openupgrade.rename_columns(cr, column_renames)
