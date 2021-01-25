
from odoo import api, fields, models, _


class AccountBankStatementLine(models.Model):
        _inherit = "account.bank.statement.line"

        def _prepare_reconciliation_move(self, move_ref):
                data = super(AccountBankStatementLine, self)._prepare_reconciliation_move(move_ref)
                if self.company_id.fiscalyear_lock_date and self.date <= self.company_id.fiscalyear_lock_date:
                        first_day_date, last_day_date = self.company_id._check_last_lock_date()
                        old_date = data["date"]
                        data.update(date=first_day_date)
                        data.update(ref=data['ref'] + " " + _("Moved from {} to {}").format(old_date, data["date"]))
                return data
