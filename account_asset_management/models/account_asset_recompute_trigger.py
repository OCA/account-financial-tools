# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetRecomputeTrigger(models.Model):
    _name = 'account.asset.recompute.trigger'
    _description = "Asset table recompute triggers"

    reason = fields.Char(
        string='Reason', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True)
    date_trigger = fields.Datetime(
        'Trigger Date',
        readonly=True,
        help="Date of the event triggering the need to "
             "recompute the Asset Tables.")
    date_completed = fields.Datetime(
        'Completion Date', readonly=True)
    state = fields.Selection(
        selection=[('open', 'Open'), ('done', 'Done')],
        string='State', default='open',
        readonly=True)
