# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    method_number = fields.Integer(
        string='Number',
        help="The meaning of this parameter depends on the Time Method.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             "  * Number of Depreciations: Fix the number of "
             "depreciation lines and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations "
             "and the date the depreciations won't go beyond.")

    method_time = fields.Selection(
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             "  * Number of Depreciations: Fix the number of "
             "depreciation lines and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations "
             "and the date the depreciations won't go beyond.")
