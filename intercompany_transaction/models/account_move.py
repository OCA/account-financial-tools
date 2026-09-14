# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from typing import Any

from odoo import Command, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_intercompany_journal_entry = fields.Boolean(copy=False, readonly=True)
    intercompany_source_account_move_id = fields.Many2one(
        "account.move",
        help="Field to link created intercompany journal entries with source entry",
        copy=False,
        readonly=True,
        index=True,
    )

    def _get_company_users_from_user_role(
        self, user_role_rec: models.Model, company_rec: models.Model
    ) -> models.Model:
        """Get users from role filtered by company access."""
        return user_role_rec.users.filtered(lambda x: company_rec in x.company_ids)

    def _prepare_intercompany_move_vals(
        self, move_line_ids: models.Model, config: models.Model
    ) -> dict[str, Any]:
        """Prepare intercompany journal entry values."""
        self.ensure_one()
        partner_id = self.company_id.partner_id.id

        line_ids = []
        for line in move_line_ids:
            line_ids.extend(
                [
                    Command.create(
                        {
                            "name": line.name,
                            "account_id": config.to_company_debit_account_id.id,
                            "partner_id": partner_id,
                            "debit": line.debit,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": line.name,
                            "account_id": config.to_company_credit_account_id.id,
                            "partner_id": partner_id,
                            "debit": 0.0,
                            "credit": line.debit,
                        }
                    ),
                ]
            )

        return {
            "date": self.date,
            "invoice_date": self.invoice_date,
            "ref": f"{self.name} ({self.company_id.name})",
            "journal_id": config.to_company_journal_id.id,
            "company_id": config.to_company_id.id,
            "is_intercompany_journal_entry": True,
            "move_type": self.move_type,
            "invoice_payment_term_id": self.invoice_payment_term_id.id,
            "payment_reference": self.payment_reference,
            "partner_id": self.partner_id.id,
            "intercompany_source_account_move_id": self.id,
            "line_ids": line_ids,
        }

    def _handle_intercompany_users_notifications(
        self, notify_user_data_dict: dict, mail_template_id: models.Model
    ) -> None:
        """Send notifications to intercompany users."""
        self.ensure_one()
        from_company_name = self.company_id.name
        email_from = self.env.user.email_formatted

        for to_company_id, move_user_dict in notify_user_data_dict.items():
            account_move_recs = move_user_dict["account_move_recs"]
            notify_user_recs = move_user_dict["notify_user_recs"]
            notify_partner_ids = notify_user_recs.partner_id.ids

            if notify_partner_ids:
                to_company_name = to_company_id.name
                email_to_partner_ids_str = ",".join(map(str, notify_partner_ids))

                for account_move_rec in account_move_recs:
                    mail_template_id.sudo().with_context(
                        email_from=email_from,
                        email_to_partner_ids=email_to_partner_ids_str,
                        from_company_name=from_company_name,
                        to_company_name=to_company_name,
                        to_move_id=str(account_move_rec.id),
                    ).send_mail(account_move_rec.id, force_send=False)

    def _post(self, soft: bool = True) -> Any:
        """Post account moves and create intercompany entries."""
        res = super()._post(soft)

        account_manager_role = self.sudo().env.ref("account.group_account_manager")
        mail_template = self.env.ref(
            "intercompany_transaction."
            "intercompany_transaction_entry_creation_mail_template"
        )

        intercompany_moves = self.filtered(
            lambda x: (
                x.is_intercompany_journal_entry
                and not x.intercompany_source_account_move_id
                and x.move_type == "entry"
            )
        )

        if not intercompany_moves:
            return res

        all_lines_with_transfer = intercompany_moves.line_ids.filtered(
            lambda x: x.transfer_to_company_id
        )

        if not all_lines_with_transfer:
            return res

        needed_configs = set()
        for move in intercompany_moves:
            from_co = move.company_id.id
            to_cos = move.line_ids.mapped("transfer_to_company_id").ids
            for to_co in to_cos:
                needed_configs.add((from_co, to_co))

        from_company_ids = intercompany_moves.company_id.ids
        to_company_ids = all_lines_with_transfer.mapped("transfer_to_company_id").ids

        configs = self.env["intercompany.transaction.config"].search(
            [
                ("from_company_id", "in", from_company_ids),
                ("to_company_id", "in", to_company_ids),
            ]
        )

        # Map (from, to) -> config record
        config_map = {(c.from_company_id.id, c.to_company_id.id): c for c in configs}

        for move in intercompany_moves:
            lines_with_transfer = move.line_ids.filtered(
                lambda x: x.transfer_to_company_id
            )

            for line in lines_with_transfer:
                line._get_move_line_intercompany_transaction_config(
                    config_cache=config_map
                )

            transfer_companies = lines_with_transfer.mapped("transfer_to_company_id")
            move_vals_list = []
            notify_user_data_dict = {}

            for transfer_company in transfer_companies:
                company_lines = lines_with_transfer.filtered(
                    lambda y, tc=transfer_company: y.transfer_to_company_id == tc
                ).sorted(key=lambda r: r.id)

                cache_key = (move.company_id.id, transfer_company.id)
                config = config_map.get(cache_key)
                if not config:
                    continue

                move_vals_list.append(
                    (
                        transfer_company,
                        move._prepare_intercompany_move_vals(company_lines, config),
                    )
                )

            AccountMoveEnv = self.env["account.move"]
            ResUsers = self.env["res.users"]

            for transfer_company, move_vals in move_vals_list:
                account_move_rec = (
                    AccountMoveEnv.sudo()
                    .with_company(transfer_company)
                    .with_context(intercompany_entry_creation=True)
                    .create(move_vals)
                )

                if transfer_company not in notify_user_data_dict:
                    notify_user_data_dict[transfer_company] = {
                        "account_move_recs": AccountMoveEnv,
                        "notify_user_recs": ResUsers,
                    }

                notify_user_data_dict[transfer_company]["account_move_recs"] |= (
                    account_move_rec
                )
                notify_user_data_dict[transfer_company]["notify_user_recs"] |= (
                    move._get_company_users_from_user_role(
                        account_manager_role, transfer_company
                    )
                )

            move._handle_intercompany_users_notifications(
                notify_user_data_dict, mail_template
            )

        return res

    def button_draft(self) -> Any:
        """Reset to draft and handle intercompany entries."""
        res = super().button_draft()

        account_manager_role = self.sudo().env.ref("account.group_account_manager")
        mail_template = self.env.ref(
            "intercompany_transaction."
            "intercompany_transaction_entry_cancellation_mail_template"
        )

        intercompany_moves = self.filtered(
            lambda x: (
                x.is_intercompany_journal_entry
                and not x.intercompany_source_account_move_id
                and x.move_type == "entry"
            )
        )

        if not intercompany_moves:
            return res

        for move in intercompany_moves:
            transfer_companies = move.line_ids.mapped("transfer_to_company_id")
            if not transfer_companies:
                continue

            notify_user_data_dict = {}
            AccountMoveEnv = self.env["account.move"]
            ResUsers = self.env["res.users"]

            related_moves = AccountMoveEnv.sudo().search(
                [
                    ("intercompany_source_account_move_id", "=", move.id),
                    ("company_id", "in", transfer_companies.ids),
                    ("is_intercompany_journal_entry", "=", True),
                    ("move_type", "=", "entry"),
                    ("state", "!=", "cancel"),
                ]
            )

            posted_moves = related_moves.filtered(lambda x: x.state == "posted")
            if posted_moves:
                raise ValidationError(
                    self.env._(
                        "The linked intercompany journal entry in the target "
                        "company(Transfer To) is already posted\n"
                        "You cannot reset journal entry "
                        "%(from_intercompany_entry)s to Draft\n\n"
                        "Posted Journal Entry:\n"
                        "%(posted_account_moves)s",
                        from_intercompany_entry=move.name,
                        posted_account_moves="\n".join(
                            [
                                f"{posted_move.name} "
                                f"({posted_move.company_id.name})"
                                for posted_move in posted_moves
                            ]
                        ),
                    )
                )

            if related_moves:
                related_moves.button_cancel()

                # Notify
                # Group by company for notification
                for company in transfer_companies:
                    company_moves = related_moves.filtered(
                        lambda m, c=company: m.company_id == c
                    )
                    if not company_moves:
                        continue

                    if company not in notify_user_data_dict:
                        notify_user_data_dict[company] = {
                            "account_move_recs": AccountMoveEnv,
                            "notify_user_recs": ResUsers,
                        }
                    notify_user_data_dict[company]["account_move_recs"] |= company_moves
                    notify_user_data_dict[company]["notify_user_recs"] |= (
                        move._get_company_users_from_user_role(
                            account_manager_role, company
                        )
                    )

                move._handle_intercompany_users_notifications(
                    notify_user_data_dict, mail_template
                )

        return res

    def get_record_url(self, record_id: int, action: str) -> str:
        """Generate URL for account move record."""
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return (
            f"{base_url}/web#id={record_id}&view_type=form&"
            f"model=account.move&action={action}"
        )

    def _has_am_missing_cost_center(self, field_to_check: str) -> bool:
        """Override to skip cost center validation for intercompany entries."""
        self.ensure_one()
        if self.env.context.get("intercompany_entry_creation", False):
            return False
        return super()._has_am_missing_cost_center(field_to_check)
