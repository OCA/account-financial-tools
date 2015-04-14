# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 Bringsvor Consulting AS. All rights reserved.
#    @author Torvald B. Bringsvor
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models, fields, _


class account_move_line(models.Model):
    _inherit = "account.move.line"

    def check_foced_tax_code(self, account, values):
        if values['tax_code_id'] != account.force_tax_id.id:
            tax = self.env['account.tax.code'].search([('id', '=', values['tax_code_id'])])[0]
            raise Warning(_('Wrong value'), _(
                'Account %s is set to force tax code "%s" but got a moveline with "%s"' % (
                account.code, account.force_tax_id.name, tax.name)))

    @api.model
    def create(self, values):
        if not 'account_id' in values:
            raise Warning(_('Missing value'), _('Account must be set on accounting move lines.'))
        accounts = self.env['account.account'].search([('id','=',values['account_id'])])

        if len(accounts)==0:
            raise Warning(_('Missing value'), _('Account must be set on accounting move lines.'))
        account = accounts[0]
        if account.force_tax_id:
            if not 'tax_code_id' in values:
                raise Warning(_('Missing value'), _('Tax code must be set on accounting move lines on account %s' % account.code))
            self.check_foced_tax_code(account, values)

        return super(account_move_line, self).create(values)

    def write(self, cr, uid, ids, values, context=None, check=True, update_check=True):
        """
        I intended to use the new api here too, but somehow I got an error saying
        that there were multiple instances of the keyword argument check.
        """
        for moveline in self.browse(cr, uid, ids):
            if 'account_id' in values:
                accounts = moveline.env['account.account'].search([('id','=',values['account_id'])])
                if len(accounts)==0:
                    raise Warning(_('Missing value'), _('Account must be set on accounting move lines.'))
                account = accounts[0]
            else:
                account = moveline.account_id

            if account.force_tax_id:
                if 'tax_code_id' in values:
                    moveline.check_foced_tax_code(account, values)

        return super(account_move_line, self).write(cr, uid, ids, values, context, check, update_check)

class account_account(models.Model):
    _inherit = 'account.account'

    force_tax_id = fields.Many2one('account.tax.code', string='Forced tax')
