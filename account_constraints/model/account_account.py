from openerp import fields, models, _

__author__ = 'tbri'


class account_account(models.Model):
    _inherit = 'account.account'

    force_tax_id = fields.Many2one('account.tax.code', string=_('Forced tax'))
