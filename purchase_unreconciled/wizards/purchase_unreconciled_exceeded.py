from odoo import _, fields, models


class PurchaseUnreconciledExceededWiz(models.TransientModel):
    _name = "purchase.unreconciled.exceeded.wiz"
    _description = "Purchase Unreconciled Exceeded Wizard"

    purchase_id = fields.Many2one(
        comodel_name="purchase.order", readonly=True, string="Order Number"
    )
    exception_msg = fields.Text(readonly=True)
    origin_reference = fields.Reference(
        lambda self: [
            (m.model, m.name) for m in self.env["ir.model"].sudo().search([])
        ],
        string="Object",
    )
    continue_method = fields.Char()

    def action_show(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase unreconciled exceeded"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def button_continue(self):
        self.ensure_one()
        return getattr(
            self.origin_reference.with_context(bypass_unreconciled=True),
            self.continue_method,
        )()
