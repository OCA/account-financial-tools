# -*- coding: utf-8 -*-
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    def _xls_acquisition_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start', 'asset_value',
            'salvage_value',
        ]

    def _xls_active_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start',
            'asset_value', 'salvage_value',
            'fy_start_value', 'fy_depr', 'fy_end_value',
            'fy_end_depr',
            'method', 'method_number', 'prorata',
        ]

    def _xls_removal_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_remove', 'asset_value',
            'salvage_value',
        ]

    def _xls_acquisition_template(self):
        """
        Template updates

        """
        return {}

    def _xls_active_template(self):
        """
        Template updates

        """
        return {}

    def _xls_removal_template(self):
        """
        Template updates

        """
        return {}
