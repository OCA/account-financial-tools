# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
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
##############################################################################
{
    "name": "Currency Rate Update",
    "version": "0.7",
    "author": "Camptocamp",
    "website": "http://camptocamp.com",
    "category": "Financial Management/Configuration",
    "depends": [
        "base",
        "account",  # Added to ensure account security groups are present
    ],
    "data": [
        "view/service_cron_data.xml",
        "view/currency_rate_update.xml",
        "view/company_view.xml",
        "security/security.xml",
    ],
    "demo": [],
    "active": False,
    'installable': True
}
