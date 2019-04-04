# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Mail(models.Model):
    _inherit = 'mail.mail'

    body_html = fields.Html(
        string='Rich-text Contents',
        help="Rich-text/HTML message",
    )
