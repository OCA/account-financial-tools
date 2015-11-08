# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

{
    "name": "Account Journal Period Close",
    "version": "8.0.1.0.0",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainer": "ACSONE SA/NV",
    "website": "http://www.acsone.eu",
    "license": "AGPL-3",
    "images": [],
    "category": "Accounting",
    "depends": [
                "account"],
    "description": """
Close period per journal
========================

This module allows fine grained control of period closing.
Each journal can be closed independently for any period
(using buttons on the fiscal period view).

A common use case is letting accountants close the sale
and purchase journals when the VAT declaration is done for
a given period, while leaving the miscellaneous journal open.

From a technical standpoint, the module leverages the
account.journal.period model that is present in Odoo core.
""",
    "data": ['view/account_period_view.xml'],
    "demo": [],
    "test": [],
    "licence": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
