#  Copyright 2020 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class AccountFiscalYear(models.Model):
    _name = "account.fiscal.year"
    _description = "Fiscal Year"

    name = fields.Char(
        required=True,
    )
    date_from = fields.Date(
        string="Start Date",
        required=True,
        help="Start Date, included in the fiscal year.",
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
        help="Ending Date, included in the fiscal year.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.constrains("date_from", "date_to", "company_id")
    def _check_dates(self):
        """Check intersection with existing fiscal years."""
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.date_from
            date_to = fy.date_to
            if date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )

            domain = fy._get_overlapping_domain()
            overlapping_fy = self.search(domain, limit=1)
            if overlapping_fy:
                raise ValidationError(
                    _(
                        "This fiscal year '{fy}' "
                        "overlaps with '{overlapping_fy}'.\n"
                        "Please correct the start and/or end dates "
                        "of your fiscal years."
                    ).format(
                        fy=fy.display_name,
                        overlapping_fy=overlapping_fy.display_name,
                    )
                )

    def _get_overlapping_domain(self):
        """Get domain for finding fiscal years overlapping with self.

        The domain will search only among fiscal years of this company.
        """
        self.ensure_one()
        # Compare with other fiscal years defined for this company
        company_domain = [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
        ]

        date_from = self.date_from
        date_to = self.date_to
        # Search fiscal years intersecting with current fiscal year.
        # This fiscal year's `from` is contained in another fiscal year
        # other.from <= fy.from <= other.to
        intersection_domain_from = [
            "&",
            ("date_from", "<=", date_from),
            ("date_to", ">=", date_from),
        ]
        # This fiscal year's `to` is contained in another fiscal year
        # other.from <= fy.to <= other.to
        intersection_domain_to = [
            "&",
            ("date_from", "<=", date_to),
            ("date_to", ">=", date_to),
        ]
        # This fiscal year completely contains another fiscal year
        # fy.from <= other.from (or other.to) <= fy.to
        intersection_domain_contain = [
            "&",
            ("date_from", ">=", date_from),
            ("date_from", "<=", date_to),
        ]
        intersection_domain = expression.OR(
            [
                intersection_domain_from,
                intersection_domain_to,
                intersection_domain_contain,
            ]
        )

        return expression.AND(
            [
                company_domain,
                intersection_domain,
            ]
        )
