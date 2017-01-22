# -*- coding: utf-8 -*-
# © 2014-2016 Acsone SA/NV (http://www.acsone.eu)
# @author: Adrien Peiffer
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Constraint Chronology",
    "version": "8.0.1.0.1",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainer": "ACSONE SA/NV",
    "website": "http://www.acsone.eu",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account"],
    "data": ["view/account_journal.xml"],
    "post_init_hook": "update_chronology_sale_journals",
    "licence": "AGPL-3",
    "installable": True,
    "application": True,
}
