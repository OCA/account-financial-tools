# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Fiscal Year',
    'version': '9.0.0.1.0',
    'category': 'Accounting',
    'summary': """
    Extend date.range.type to add fiscal_year flag.

    Override official res_company.compute_fiscal_year_dates to get the
    fiscal year date start / date end for any given date.
    That methods first looks for a date range of type fiscal year that
    encloses the give date.
    If it does not find it, it falls back on the standard Odoo
    technique based on the day/month of end of fiscal year.

    """,
    'author': 'Camptocamp SA,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
        'date_range'
    ],
    'data': [
        'data/date_range_type.xml',
        'views/date_range_type.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
