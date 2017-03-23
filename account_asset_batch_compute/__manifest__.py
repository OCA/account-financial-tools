# -*- coding: utf-8 -*-
# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Asset Batch Compute',
    'summary': """
        Add the possibility to compute assets in batch""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'www.acsone.eu',
    'depends': [
        'account_asset_management',
        'queue_job',
    ],
    'data': [
        'wizards/asset_depreciation_confirmation_wizard.xml',
    ],
}
