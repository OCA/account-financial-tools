from odoo import fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _create_date_range_seq(self, date):
        # Fix issue creating new date range for future dates
        # It assigns more than one month
        # TODO: Remove if odoo merge the following PR:
        # https://github.com/odoo/odoo/pull/91019
        date_obj = fields.Date.from_string(date)
        sequence_range = self.env["ir.sequence.date_range"]
        prefix_suffix = f"{self.prefix} {self.suffix}"
        if "%(range_day)s" in prefix_suffix:
            date_from = date_obj
            date_to = date_obj
        elif "%(range_month)s" in prefix_suffix:
            date_from = fields.Date.start_of(date_obj, "month")
            date_to = fields.Date.end_of(date_obj, "month")
        else:
            date_from = fields.Date.start_of(date_obj, "year")
            date_to = fields.Date.end_of(date_obj, "year")
        date_range = sequence_range.search(
            [
                ("sequence_id", "=", self.id),
                ("date_from", ">=", date),
                ("date_from", "<=", date_to),
            ],
            order="date_from desc",
            limit=1,
        )
        if date_range:
            date_to = fields.Date.subtract(date_range.date_from, days=1)
        date_range = sequence_range.search(
            [
                ("sequence_id", "=", self.id),
                ("date_to", ">=", date_from),
                ("date_to", "<=", date),
            ],
            order="date_to desc",
            limit=1,
        )
        if date_range:
            date_to = fields.Date.add(date_range.date_to, days=1)
        sequence_range_vals = {
            "date_from": date_from,
            "date_to": date_to,
            "sequence_id": self.id,
        }
        seq_date_range = sequence_range.sudo().create(sequence_range_vals)
        return seq_date_range
