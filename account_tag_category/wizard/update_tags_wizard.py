# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountTagCategoryUpdateTags(models.TransientModel):

    _name = 'account.tag.category.update.tags'

    _description = 'Update account tags on account tag category'

    tag_ids = fields.Many2many('account.account.tag', string='Tags',
                               domain=[('applicability', '=', 'accounts')])
    # TODO support applicability for taxes in domain

    tag_category_id = fields.Many2one('account.account.tag.category',
                                      string='Tag category')

    @api.model
    def default_get(self, fields):
        res = super(AccountTagCategoryUpdateTags, self).default_get(fields)
        if 'tag_ids' in fields and not res.get('tag_ids'):
            res['tag_ids'] = self.env['account.account.tag'].search(
                [('tag_category_id', '=', res.get('tag_category_id'))]).ids
        return res

    @api.multi
    def save_tags_to_category(self):

        categorized_tags = self.tag_ids.filtered(
            lambda t: t.tag_category_id and
            t.tag_category_id != self.tag_category_id)
        if categorized_tags:
            tags_error = ["- %s (%s)" % (t.name, t.tag_category_id.name)
                          for t in categorized_tags]
            raise ValidationError(_('Following tags are already defined on '
                                    'another tag category : \n %s') %
                                  "\n".join(tags_error)
                                  )

        self.tag_category_id.write({
            'tag_ids': [(6, False, self.tag_ids.ids)]
        })

        return
