from odoo import _, fields, models


class SaleUnreconciledExceededWiz(models.TransientModel):
    _name = "sale.unreconciled.exceeded.wiz"
    _description = "Sale Unreconciled Exceeded Wizard"

    sale_id = fields.Many2one(
        comodel_name="sale.order", readonly=True, string="Order Number"
    )
    exception_msg = fields.Text(readonly=True)
    origin_reference = fields.Reference(
        lambda self: [(m.model, m.name) for m in self.env["ir.model"].search([])],
        string="Object",
    )
    continue_method = fields.Char()

    def action_show(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sale unreconciled exceeded"),
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
