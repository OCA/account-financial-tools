# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Account Tax Adjustments extend",
    'version': '11.0.1.0.0',
    'category': 'Generic Modules/Accounting',
    'summary': "Extend functionality in tax adjustment",
    'author': "Rosen Vladimirov, "
              "BioPrint Ltd."
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'date_range',
        'account_fiscal_month',
        'account_fiscal_year',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/tax_adjustment_template.xml',
        'wizards/wizard_tax_adjustments_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
