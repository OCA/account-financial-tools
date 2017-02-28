# -*- coding: utf-8 -*-
# © 2017 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Constraints Banking',
    'version': '7.0.1.0.0',
    'depends': [
        'account_constraints',
        'account_banking',
    ],
    'author': "Therp BV,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'category': 'Generic Modules/Accounting',
    'description': """
Account Constraints Banking
===========================

This is a glue module between account_constraints and account_banking.

account_constraints prevents unlinking (or even changing) moves that are
linked to a bank statement, directing the user to instead apply changes
on the bank statement directly. Without this module changes on the
bank statement, like cancelling a transaction, are also prevented.

  Contributors
  * Ronald Portier (Therp BV)  <ronald@therp.nl>

    """,
    'website': 'https://therp.nl',
    'data': [],
    'installable': True,
    'auto_install': True,
}
