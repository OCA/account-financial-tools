from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    no_tax_recompute = fields.Boolean(
        string="No Recompute Taxes",
        help="When enabled on journal entries, dynamic tax synchronization is skipped.",
    )

    def _should_skip_dynamic_sync_for_no_tax_recompute(self, vals):
        """Return True when dynamic sync must be skipped for this move."""
        self.ensure_one()
        if not self.is_entry():
            return False

        final_value = vals.get("no_tax_recompute", self.no_tax_recompute)
        return bool(final_value)

    @api.model_create_multi
    def create(self, vals_list):
        frozen_vals = [
            vals
            for vals in vals_list
            if vals.get("move_type", "entry") == "entry"
            and vals.get("no_tax_recompute")
        ]
        regular_vals = [vals for vals in vals_list if vals not in frozen_vals]

        moves = self.env["account.move"]

        if frozen_vals:
            moves |= super(
                AccountMove,
                self.with_context(
                    skip_invoice_sync=True,
                    skip_no_tax_recompute_sync=True,
                ),
            ).create(frozen_vals)

        if regular_vals:
            moves |= super().create(regular_vals)

        return moves

    def write(self, vals):
        """Bypass dynamic tax sync only for frozen journal entries."""
        if self.env.context.get("skip_no_tax_recompute_sync") or "line_ids" not in vals:
            return super().write(vals)

        move_to_skip = self.filtered(
            lambda m: m._should_skip_dynamic_sync_for_no_tax_recompute(vals)
        )
        regular_moves = self - move_to_skip

        if move_to_skip:
            super(
                AccountMove,
                move_to_skip.with_context(
                    skip_invoice_sync=True, skip_no_tax_recompute_sync=True
                ),
            ).write(vals)

        if regular_moves:
            super(AccountMove, regular_moves).write(vals)

        return True

    def copy(self, default=None):
        """Duplicate frozen entries without triggering dynamic tax sync."""
        self.ensure_one()
        default = dict(default or {})

        if self.is_entry() and self.no_tax_recompute:
            default.setdefault("no_tax_recompute", True)
            return super(
                AccountMove,
                self.with_context(
                    skip_invoice_sync=True, skip_no_tax_recompute_sync=True
                ),
            ).copy(default)

        return super().copy(default)
