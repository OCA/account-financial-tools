# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Asset Maintenance',
    'summary': 'Add relation between assets and equipments',
    'author': 'Onestein',
    'website': 'http://www.onestein.eu',
    'category': 'Accounting & Finance',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_asset',
        'maintenance',
        'mail',
    ],
    'data': [
        'views/account_asset.xml',
        'views/maintenance_equipment.xml',
        'views/account_config_setting_views.xml',
        'wizard/scrap_equipment.xml',
    ],
}
