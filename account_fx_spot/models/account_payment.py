# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class AccountFxSpot(models.Model):
    _inherit = "account.payment"

    fx_spot_ids = fields.Many2many(
        comodel_name="account.fx.spot",
        relation="account_fx_spot_payment_rel",
        column1="payment_id", column2="fx_spot_id",
        string="Foreign Exchange Spot Transaction",
        copy=False, readonly=True,
    )
    has_fx_spots = fields.Boolean(
        compute="_compute_has_fx_spots",
        help="Technical field for usability purposes",
    )

    @api.multi
    @api.depends('fx_spot_ids')
    def _compute_has_fx_spots(self):
        for rec in self:
            rec.has_fx_spots = bool(rec.fx_spot_ids)

    def _create_payment_entry(self, amount):
        res = super(AccountFxSpot, self)._create_payment_entry(amount)
        if self.fx_spot_ids:
            counterpart_aml = res.line_ids.filtered(
                lambda r: r.account_id.internal_type in
                ('receivable', 'payable'))
            self.fx_spot_ids.register_payment(counterpart_aml)
        return res

    @api.multi
    def button_fx_spot(self):
        return {
            'name': _('Paid FX Spot Transactions'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.fx.spot',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.fx_spot_ids.ids)],
        }
