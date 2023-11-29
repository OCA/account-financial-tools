# Copyright 2016-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    spread_id = fields.Many2one("account.spread", string="Spread Board", copy=False)
    spread_check = fields.Selection(
        [
            ("linked", "Linked"),
            ("unlinked", "Unlinked"),
            ("unavailable", "Unavailable"),
        ],
        compute="_compute_spread_check",
    )

    @api.depends("spread_id", "move_id.state")
    def _compute_spread_check(self):
        for line in self:
            if line.spread_id:
                line.spread_check = "linked"
            elif line.move_id.state == "draft":
                line.spread_check = "unlinked"
            else:
                line.spread_check = "unavailable"

    def spread_details(self):
        """Button on the invoice lines tree view of the invoice
        form to show the spread form view."""
        if not self:
            # In case the widget clicked before the creation of the line
            return

        if self.spread_id:
            return {
                "name": _("Spread Details"),
                "view_mode": "form",
                "res_model": "account.spread",
                "type": "ir.actions.act_window",
                "target": "current",
                "readonly": False,
                "res_id": self.spread_id.id,
            }

        # In case no spread board is linked to the invoice line
        # open the wizard to link them
        ctx = dict(
            self.env.context,
            default_invoice_line_id=self.id,
            default_company_id=self.move_id.company_id.id,
            allow_spread_planning=self.move_id.company_id.allow_spread_planning,
        )
        return {
            "name": _("Link Invoice Line with Spread Board"),
            "view_mode": "form",
            "res_model": "account.spread.invoice.line.link.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": ctx,
        }

    @api.constrains("spread_id", "account_id")
    def _check_spread_account_balance_sheet(self):
        for line in self:
            if not line.spread_id:
                pass
            elif line.move_id.move_type in ("out_invoice", "in_refund"):
                if line.account_id != line.spread_id.debit_account_id:
                    raise ValidationError(
                        _(
                            "The account of the invoice line does not correspond "
                            "to the Balance Sheet (debit account) of the spread"
                        )
                    )
            elif line.move_id.move_type in ("in_invoice", "out_refund"):
                if line.account_id != line.spread_id.credit_account_id:
                    raise ValidationError(
                        _(
                            "The account of the invoice line does not correspond "
                            "to the Balance Sheet (credit account) of the spread"
                        )
                    )

    def write(self, vals):
        if vals.get("spread_id"):
            spread = self.env["account.spread"].browse(vals.get("spread_id"))
            if spread.invoice_type in ["out_invoice", "in_refund"]:
                vals["account_id"] = spread.debit_account_id.id
            else:
                vals["account_id"] = spread.credit_account_id.id
        return super().write(vals)

    def _check_spread_reconcile_validity(self):
        # Improve error messages of standard Odoo
        reconciled_lines = self.filtered(lambda l: l.reconciled)
        msg_line = _(
            "Move line: %(line_id)s (%(line_name)s), account code: %(account_code)s\n"
        )
        if reconciled_lines:
            msg = _("Cannot reconcile entries that are already reconciled:\n")
            for line in reconciled_lines:
                msg += msg_line % {
                    "line_id": line.id,
                    "line_name": line.name,
                    "account_code": line.account_id.code,
                }
            raise ValidationError(msg)
        if len(self.mapped("account_id").ids) > 1:
            msg = _("Some entries are not from the same account:\n")
            for line in self:
                msg += msg_line % {
                    "line_id": line.id,
                    "line_name": line.name,
                    "account_code": line.account_id.code,
                }
            raise ValidationError(msg)

    def create_auto_spread(self):
        """Create auto spread table for each invoice line, when needed"""

        def _filter_line(aline, iline):
            """Find matching template auto line with invoice line"""
            if aline.product_id and iline.product_id != aline.product_id:
                return False
            if aline.account_id and iline.account_id != aline.account_id:
                return False
            if (
                aline.analytic_account_id
                and iline.account_analytic_id != aline.analytic_account_id
            ):
                return False
            return True

        # Skip create new template when create move on spread lines
        if self.env.context.get("skip_create_template"):
            return
        for line in self:
            if line.spread_check == "linked":
                continue
            spread_type = (
                "sale"
                if line.move_id.move_type in ["out_invoice", "out_refund"]
                else "purchase"
            )
            spread_auto = self.env["account.spread.template.auto"].search(
                [
                    ("template_id.auto_spread", "=", True),
                    ("template_id.spread_type", "=", spread_type),
                ]
            )
            matched = spread_auto.filtered(lambda a, i=line: _filter_line(a, i))
            template = matched.mapped("template_id")
            if not template:
                continue
            elif len(template) > 1:
                raise UserError(
                    _(
                        "Too many auto spread templates (%(len_template)s) matched with the "
                        "invoice line, %(line_name)s"
                    )
                    % {"len_template": len(template), "line_name": line.display_name}
                )
            # Found auto spread template for this invoice line, create it
            wizard = self.env["account.spread.invoice.line.link.wizard"].new(
                {
                    "invoice_line_id": line.id,
                    "company_id": line.company_id.id,
                    "spread_action_type": "template",
                    "template_id": template.id,
                }
            )
            wizard.confirm()
