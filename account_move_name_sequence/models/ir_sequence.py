from dateutil.relativedelta import relativedelta

from odoo import fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _create_date_range_seq(self, date):
        # Fix issue creating new date range for future dates
        # It assigns more than one month
        # TODO: Remove if odoo merge the following PR:
        # https://github.com/odoo/odoo/pull/91019
        date_obj = fields.Date.from_string(date)
        prefix_suffix = "%s %s" % (self.prefix, self.suffix)
        if "%(range_day)s" in prefix_suffix:
            date_from = date_obj
            date_to = date_obj
        elif "%(range_month)s" in prefix_suffix:
            date_from = date_obj + relativedelta(day=1)
            date_to = date_obj + relativedelta(day=31)
        else:
            date_from = date_obj + relativedelta(day=1, month=1)
            date_to = date_obj + relativedelta(day=31, month=12)
        date_range = self.env["ir.sequence.date_range"].search(
            [
                ("sequence_id", "=", self.id),
                ("date_from", ">=", date),
                ("date_from", "<=", date_to),
            ],
            order="date_from desc",
            limit=1,
        )
        if date_range:
            date_to = date_range.date_from + relativedelta(days=-1)
        date_range = self.env["ir.sequence.date_range"].search(
            [
                ("sequence_id", "=", self.id),
                ("date_to", ">=", date_from),
                ("date_to", "<=", date),
            ],
            order="date_to desc",
            limit=1,
        )
        if date_range:
            date_from = date_range.date_to + relativedelta(days=1)
        seq_date_range = (
            self.env["ir.sequence.date_range"]
            .sudo()
            .create(
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "sequence_id": self.id,
                }
            )
        )
        return seq_date_range
