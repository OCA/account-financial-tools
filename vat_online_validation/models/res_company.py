from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    must_validate_vat = fields.Boolean(
        "Mandatory online VAT number verification?",
        help="If enabled, the system validates "
        "VAT number online and shows error "
        "message if given VAT number of "
        "partner/customer is not valid.",
    )
