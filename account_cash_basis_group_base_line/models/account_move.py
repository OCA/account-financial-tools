from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _get_tax_cash_basis_base_key(self, tax, move, line):
        account_id = self._get_tax_cash_basis_base_account(line, tax)
        tax_rep_lines = (
            tax.refund_repartition_line_ids
            if line.move_id.type in ("in_refund", "out_refund")
            else tax.invoice_repartition_line_ids
        )
        original_base_tags = tax_rep_lines.filtered(
            lambda x: x.repartition_type == "base"
        ).tag_ids
        base_tags = tuple(line._convert_tags_for_cash_basis(original_base_tags).ids)
        return (
            move.id,
            account_id.id,
            tax.id,
            line.tax_repartition_line_id.id,
            base_tags,
            line.currency_id.id,
            line.partner_id.id,
            line.move_id.type,
        )

    def _get_tax_cash_basis_base_common_vals(self, key, new_move):
        self.ensure_one()
        # pylint: disable=W0612
        (
            move,
            account_id,
            tax_id,
            tax_repartition_line_id,
            base_tags,
            currency_id,
            partner_id,
            move_type,
        ) = key
        move = self.env["account.move"].browse(move)
        return {
            "name": move.name,
            "account_id": account_id,
            "journal_id": new_move.journal_id.id,
            "tax_exigible": True,
            "tax_ids": [(6, 0, [tax_id])],
            "tag_ids": [(6, 0, base_tags)],
            "move_id": new_move.id,
            "currency_id": currency_id,
            "partner_id": partner_id,
            "tax_repartition_line_id": tax_repartition_line_id,
        }
