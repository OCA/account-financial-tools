from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends("order_line.invoice_lines.move_id")
    def _compute_journal_entries(self):
        for order in self:
            journal_entries = order.mapped("order_line.invoice_lines.move_id").filtered(
                lambda r: r.move_type == "entry"
            )
            order.journal_entry_ids = journal_entries
            order.journal_entries_count = len(journal_entries)

    journal_entries_count = fields.Integer(compute="_compute_journal_entries")
    journal_entry_ids = fields.Many2many(
        comodel_name="account.move",
        relation="journal_entries_ids_purchase_order",
        compute="_compute_journal_entries",
        string="Journal Entries",
    )

    @api.depends("order_line.invoice_lines.move_id")
    def _compute_invoice(self):
        """Overwritten compute to avoid show all Journal Entries with
        purchase_order_line as invoice_lines One2many would take them into account."""
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda m: m.is_invoice(include_receipts=True)
            )
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    def action_view_journal_entries(self, invoices=False):
        """This function returns an action that display existing journal entries of
        given purchase order ids. When only one found, show the journal entry
        immediately.
        """
        if not invoices:
            self.sudo()._read(["journal_entry_ids"])
            invoices = self.journal_entry_ids

        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_journal_line"
        )
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref("account.view_move_form", False)
            form_view = [(res and res.id or False, "form")]
            if "views" in result:
                result["views"] = form_view + [
                    (state, view) for state, view in result["views"] if view != "form"
                ]
            else:
                result["views"] = form_view
            result["res_id"] = invoices.id
        else:
            result = {"type": "ir.actions.act_window_close"}

        return result
