# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

column_renames = {
    'account_invoice': [
        ('cc_amount_tax', 'amount_tax_signed'),
    ],
}

column_copies = {
    'account_invoice': [
        ('cc_amount_untaxed', 'amount_untaxed_signed', None),
        ('cc_amount_total', 'amount_total_company_signed', None),
    ],
}


def migrate(cr, version):
    openupgrade.rename_columns(cr, column_renames)
    openupgrade.copy_columns(cr, column_copies)
