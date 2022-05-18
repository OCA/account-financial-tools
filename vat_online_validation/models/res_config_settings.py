from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    must_validate_vat = fields.Boolean(
        "Mandatory online VAT number verification?",
        related="company_id.must_validate_vat",
        readonly=False,
        help="If enabled, the system validates "
        "VAT number online and shows error "
        "message if given VAT number of "
        "partner/customer is not valid.",
    )
