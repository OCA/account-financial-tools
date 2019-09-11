# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountDocuments(models.Model):
    _inherit = "account.documents"

    comment_template_id = fields.Many2one('base.comment.template',
                                           string='Comment Template', domain="[('position', '=', 'documents')]")
    note = fields.Html('Top Comment')

    @api.onchange('comment_template_id')
    def _set_note(self):
        comment = self.comment_template_id
        if comment and comment.use and not self.note:
            self.note = comment.get_value()


class BaseCommentTemplate(models.Model):
    _inherit = "base.comment.template"

    position = fields.Selection([('documents', 'Use in documents descriptions')])
