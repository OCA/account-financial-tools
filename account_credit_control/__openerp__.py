# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account Credit Control',
    'version': '9.0.1.0.3',
    'author': "Camptocamp, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'category': 'Finance',
    'depends': [
        'base',
        'account',
        'mail',
    ],
    'website': 'http://www.camptocamp.com',
    'data': [
        "security/res_groups.xml",
        "report/report.xml",
        "report/report_credit_control_summary.xml",
        "data/data.xml",
        "views/account_invoice.xml",
        "views/credit_control_line.xml",
        "views/credit_control_policy.xml",
        "views/credit_control_run.xml",
        "views/res_company.xml",
        "views/res_partner.xml",
        "wizards/credit_control_emailer_view.xml",
        "wizards/credit_control_marker_view.xml",
        "wizards/credit_control_printer_view.xml",
        "wizards/credit_control_policy_changer_view.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
}
