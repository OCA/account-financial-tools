# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class ResCompany(models.Model):
    _inherit = "res.company"

    # the native method _validate_fiscalyear_lock() is called at the beginning of
    # write()
    def _validate_fiscalyear_lock(self, values):
        if "fiscalyear_lock_date" in values:
            new_fy_lock_date = values["fiscalyear_lock_date"]
            for company in self:
                if company.fiscalyear_lock_date:
                    if not new_fy_lock_date:
                        raise UserError(
                            _(
                                "You cannot remove the 'Lock Date for All Users' "
                                "on company '%s'."
                            )
                            % company.display_name
                        )
                    else:
                        if isinstance(new_fy_lock_date, str):
                            new_fy_lock_date = fields.Date.from_string(new_fy_lock_date)
                    if new_fy_lock_date < company.fiscalyear_lock_date:
                        raise UserError(
                            _(
                                "On company '%s', the current 'Lock Date for All Users' "
                                "is %s: you cannot set it backwards to %s."
                            )
                            % (
                                company.display_name,
                                format_date(self.env, company.fiscalyear_lock_date),
                                format_date(self.env, new_fy_lock_date),
                            )
                        )
        super()._validate_fiscalyear_lock(values)
