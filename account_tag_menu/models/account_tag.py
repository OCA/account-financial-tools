# Copyright 2018 FOREST AND BIOMASS ROMANIA SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    code = fields.Char("Code", index=True, copy=False)
    account_ids = fields.Many2many('account.account', 'account_account_account_tag', string='Accounts',
        help="Assigned accounts for custom reporting")
    tax_ids = fields.Many2many('account.tax', 'account_tax_account_tag', string='Taxes',
        help="Assigned taxes for custom reporting")

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
    color = fields.Integer('Color Index', compute='_compute_color_index', store=True)

    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', index=True, ondelete='cascade')
    child_ids = fields.One2many('account.account.tag', 'parent_id', string='Child Tags')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account.tag'))
    
    type_taxes = fields.Selection([
                            ('0', _('Tax base')),
                            ('2', _('Tax base (debit)')),
                            ('3', _('Tax base (credit)')),
                            ('1', _('Coupled tax')),
                            ('98', _('Boot Tax base and tax EU deals')),
                            ('99', _('Boot Tax base and tax')),
                            ])
    type_info = fields.Selection([
                            ('period', 'Fiscal period'),
                            ('vat', 'Get partner VAT'),
                            ('name', 'Get partner name'),
                            ('vatcompany', 'Get company VAT'),
                            ('namecompany', 'Get company name'),
                            ('addresscompany', 'Get company address'),
                            ('movenumber', 'Get account move number'),
                            ('date', 'Get account move date'),
                            ('narration', 'Get account move narration'),
                            ('ref', 'Get account move ref'),
                          ])

    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for tag in self:
            if self._context.get('only_code'):
                tag.display_name = "%s" % tag.code
            if tag.code and tag.name:
                tag.display_name = "[%s] %s" % (tag.code, tag.name)
            elif tag.code and not tag.name:
                tag.display_name = "%s" % tag.code
            elif tag.name and not tag.code:
                tag.display_name = "%s" % tag.code
            else:
                tag.display_name = "%s" % tag.code

    @api.depends('color_picker')
    def _compute_color_index(self):
        for tag in self:
            if tag.parent_id:
                color = tag.parent_id.color_picker
            else:
                color = tag.color_picker
            tag.color = int(color)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You can not create recursive tags.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.multi
    def name_get(self):
        """ Return the tags' display name, including their direct
            parent by default.

            If ``context['account_tag_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('account_tag_display') == 'short':
            return super(AccountAccountTag, self).name_get()

        res = []
        for tag in self:
            names = []
            current = tag
            while current:
                names.append("[%s] %s" % (current.code, current.name))
                current = current.parent_id
            res.append((tag.id, ' / '.join(reversed(names))))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()
