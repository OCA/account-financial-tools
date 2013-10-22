# -*- coding: utf-8 -*-

from openerp.osv import orm

class account_tax(orm.Model):
    _inherit = 'account.tax'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        # unused res = []
        if context and context.get('tax_real_name'):
            return ((record['id'], record['name']) for record in self.read(
                    cr, uid, ids, ['name'], context=context))
        return super(account_tax, self).name_get(cr, uid, ids, context=context)
