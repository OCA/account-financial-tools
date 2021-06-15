# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _name = "account.asset.category"
    _description = "Asset Category"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'complete_name'
    _order = 'parent_left'

    name = fields.Char('Name', index=True, required=True, translate=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('account.asset.category', 'Parent Category', index=True, ondelete='cascade')
    child_id = fields.One2many('account.asset.category', 'parent_id', 'Child Categories')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    asset_count = fields.Integer(
        '# Assets', compute='_compute_asset_count',
        help="The number of assets under this category (Does not consider the children categories)")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self._default_company_id())

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.asset')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_asset_count(self):
        read_group_res = self.env['account.asset'].read_group([('category_id', 'child_of', self.ids)], ['category_id'], ['category_id'])
        group_data = dict((data['category_id'][0], data['category_id_count']) for data in read_group_res)
        for categ in self:
            product_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.id)]).ids:
                product_count += group_data.get(sub_categ_id, 0)
            categ.product_count = product_count

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]
