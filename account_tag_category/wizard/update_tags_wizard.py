# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountTagCategoryUpdateTags(models.TransientModel):

    _name = 'account.tag.category.update.tags'

    _description = 'Update account tags on account tag category'

    tag_ids = fields.Many2many('account.account.tag',
                               domain=[('applicability', '=', 'accounts')])
    # TODO support applicability for taxes in domain

    tag_category_id = fields.Many2one('account.account.tag.category')

    @api.model
    def default_get(self, fields):
        res = super(AccountTagCategoryUpdateTags, self).default_get(fields)
        if 'tag_ids' in fields and not res.get('tag_ids'):
            res['tag_ids'] = self.env['account.account.tag'].search(
                [('tag_category_id', '=', res.get('tag_category_id'))]).ids
        return res

    @api.multi
    def save_tags_to_category(self):

        self.tag_category_id.write({
            'tag_ids': [(6, False, self.tag_ids.ids)]
        })

        return
