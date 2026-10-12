from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        """Create lines with sync disabled when targeting frozen entries."""
        entry_move_ids = {
            vals.get("move_id") for vals in vals_list if vals.get("move_id")
        }
        if entry_move_ids:
            entry_moves = (
                self.env["account.move"]
                .browse(entry_move_ids)
                .filtered(lambda m: m.is_entry() and m.no_tax_recompute)
            )
            if entry_moves:
                return super(
                    AccountMoveLine,
                    self.with_context(
                        skip_invoice_sync=True, skip_no_tax_recompute_sync=True
                    ),
                ).create(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        """Disable sync on frozen lines while preserving regular line behavior."""
        frozen_lines = self.filtered(
            lambda line: line.move_id.is_entry() and line.move_id.no_tax_recompute
        )
        if frozen_lines and not self.env.context.get("skip_no_tax_recompute_sync"):
            regular_lines = self - frozen_lines
            super(
                AccountMoveLine,
                frozen_lines.with_context(
                    skip_invoice_sync=True, skip_no_tax_recompute_sync=True
                ),
            ).write(vals)
            if regular_lines:
                super(AccountMoveLine, regular_lines).write(vals)
            return True
        return super().write(vals)
