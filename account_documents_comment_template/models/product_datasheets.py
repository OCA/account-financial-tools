# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountDocuments(models.Model):
    _inherit = "product.manufacturer.datasheets"

    comment_template_id = fields.Many2one('base.comment.template',
                                           string='Comment Template', domain="[('position', '=', 'datasheets')]")
    note = fields.Html('Top Comment')

    @api.onchange('comment_template_id')
    def _set_note(self):
        comment = self.comment_template_id
        if comment and comment.use and not self.note:
            self.note = comment.get_value()

    @api.onchange('manufacturer_id', 'comment_template_id')
    def _onchange_manufacturer_id(self):
        if not self.name and self.comment_template_id and self.manufacturer_id:
            self.name = "%s_%s" % (self.comment_template_id.name, self.manufacturer_id.manufacturer_pref)
        if not self.name and self.is_date and self.comment_template_id and self.manufacturer_id:
            self.name = "%s: %s/%s expr. %s" % (self.comment_template_id.name, self.iso_number, self.date_issue, self.date_expiry)


class BaseCommentTemplate(models.Model):
    _inherit = "base.comment.template"

    position = fields.Selection(selection_add=[('datasheets', 'Use in datasheets descriptions'),
                                               ('prints', 'Use on print forms')])
