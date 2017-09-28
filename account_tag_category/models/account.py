# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAccountTag(models.Model):

    _inherit = 'account.account.tag'

    tag_category_id = fields.Many2one('account.account.tag.category',
                                      string='Tag category',
                                      ondelete='set null')

    category_color = fields.Integer(related='tag_category_id.color')

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        # This function is used to read from category_color field instead of
        # color without having to change anything on the client side.
        if 'color' in fields:
            fields.append('category_color')
            if 'tag_category_id' not in fields:
                fields.append('tag_category_id')
        result = super(AccountAccountTag, self).read(fields, load)
        for rec in result:
            if 'category_color' in rec and rec.get('tag_category_id', False):
                color = rec.pop('category_color')
                rec['color'] = color
        return result


class AccountAccountTagCategory(models.Model):

    _name = 'account.account.tag.category'

    _description = 'Account Tag Category'

    name = fields.Char(required=True)

    color = fields.Integer('Color Index', compute='_compute_color_index',
                           store=True)

    color_picker = fields.Selection([('0', 'Grey'),
                                     ('1', 'Green'),
                                     ('2', 'Yellow'),
                                     ('3', 'Orange'),
                                     ('4', 'Red'),
                                     ('5', 'Purple'),
                                     ('6', 'Blue'),
                                     ('7', 'Cyan'),
                                     ('8', 'Aquamarine'),
                                     ('9', 'Pink')], string='Tags Color',
                                    required=True, default='0')

    enforce_policy = fields.Selection(
        [('required', 'Required'), ('optional', 'Optional')],
        required=True, default='optional',
        help='If required, this option enforces the use of a tag from this '
             'category. If optional, the user is not required to use a tag '
             'from this category.')

    tag_ids = fields.One2many('account.account.tag', 'tag_category_id',
                              string='Tags',)

    # TODO support applicability for taxes

    applicability = fields.Selection([
        ('accounts', 'Accounts'),
        # ('taxes', 'Taxes'),
    ], default='accounts', required=True)

    @api.depends('color_picker')
    def _compute_color_index(self):
        for category in self:
            category.color = int(category.color_picker)

    @api.constrains('tag_ids', 'applicability')
    def _check_tags_applicability(self):
        self.ensure_one()
        for tag in self.tag_ids:
            if tag.applicability != self.applicability:
                raise ValidationError(_('Selected tag must be applicable on '
                                        'the same model as this category (%s)'
                                        ) % self.applicability)

    @api.multi
    def name_get(self):
        return [(cat.id, cat.name) for cat in self]


class AccountAccount(models.Model):

    _inherit = 'account.account'

    # field name is constrained to ensure this method is called on create
    @api.constrains('tag_ids', 'name')
    def _check_tags_categories(self):
        self.ensure_one()
        self._check_required_categories()
        self._check_unique_tag_per_category()

    def _check_unique_tag_per_category(self):
        used_categories_ids = []
        for tag in self.tag_ids:
            if not tag.tag_category_id:
                continue
            tag_id = tag.tag_category_id.id
            if tag_id in used_categories_ids:
                raise ValidationError(_('There is more than one tag from the '
                                        'same category which is used'))
            else:
                used_categories_ids.append(tag_id)

    def _check_required_categories(self):
        required_categories = self.env['account.account.tag.category'].search(
            [('applicability', '=', 'accounts'),
             ('enforce_policy', '=', 'required')])
        errors = []
        for category in required_categories:
            found = False
            for tag in self.tag_ids:
                if tag in category.tag_ids:
                    found = True
            if not found:
                errors.append(category.name)
        if errors:
            text_error = '\n'.join(errors)
            raise ValidationError(_('Following tag categories are set as '
                                    'required, but there is no tag from these '
                                    'categories : \n %s') % text_error)
