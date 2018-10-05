# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
_render = AbstractReportXlsx._render


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    @api.model
    def _xls_acquisition_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start', 'depreciation_base',
            'salvage_value',
        ]

    @api.model
    def _xls_active_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start',
            'depreciation_base', 'salvage_value',
            'fy_start_value', 'fy_depr', 'fy_end_value',
            'fy_end_depr',
            'method', 'method_number', 'prorata',
        ]

    @api.model
    def _xls_removal_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_remove', 'depreciation_base',
            'salvage_value',
        ]

    @api.model
    def _xls_asset_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_acquisition_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_active_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_removal_template(self):
        """
        Template updates

        """
        return {}
