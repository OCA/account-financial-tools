# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Invoice Force Currency Rate",
    "summary": "Allows select other currency rate than the default one.",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://factorlibre.com/",
    "author": "FactorLibre, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_invoice_view.xml",
    ]
}
