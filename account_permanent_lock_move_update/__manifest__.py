# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Permanent Lock Move Update',
    'summary': """
        Allow an Account adviser to update permanent lock date without
        having access to all technical settings""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account_lock_date_update',
        'account_permanent_lock_move',
    ],
    'data': [
        'wizards/account_update_lock_date.xml',
    ],
}
