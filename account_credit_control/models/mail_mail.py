# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class Mail(models.Model):
    _inherit = 'mail.mail'

    # use HTML fields instead of text
    body_html = fields.Html(
        string='Rich-text Contents',
        help="Rich-text/HTML message",
    )
