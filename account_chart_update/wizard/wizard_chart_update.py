# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#    Copyright (c) 2010 Pexego Sistemas Informáticos S.L. (http://www.pexego.es)
#    @authors: Jordi Esteve (Zikzakmedia), Borja López Soilán (Pexego)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging


def _reopen(self, res_id, model):
    return {
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_type': 'form',
        'res_id': res_id,
        'res_model': self._name,
        'target': 'new',
        # save original model in context, because selecting the list of available
        # templates requires a model in context
        'context': {
            'default_model': model,
        },
    }


class WizardLog:
    """
    *******************************************************************
    Small helper class to store the messages and errors on the wizard.
    *******************************************************************
    """
    def __init__(self):
        self.messages = []
        self.errors = []

    def add(self, message, is_error=False):
        """
        Adds a message to the log.
        """
        logger = logging.getLogger("account_chart_update")
        if is_error:
            logger.warning(u"Log line: %s" % message)
            self.errors.append(message)
        else:
            logger.debug(u"Log line: %s" % message)
        self.messages.append(message)

    def has_errors(self):
        """
        Returns whether errors where logged.
        """
        return self.errors

    def __call__(self):
        return "".join(self.messages)

    def __str__(self):
        return "".join(self.messages)

    def get_errors_str(self):
        return "".join(self.errors)


class wizard_update_charts_accounts(orm.TransientModel):
    _name = 'wizard.update.charts.accounts'

    def _get_lang_selection_options(self, cr, uid, context={}):
        """
        Gets the available languages for the selection.
        """
        obj = self.pool.get('res.lang')
        ids = obj.search(cr, uid, [], context=context)
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res] + [('', '')]

    _columns = {
        'state': fields.selection([
            ('init', 'Step 1'),
            ('ready', 'Step 2'),
            ('done', 'Wizard completed')
        ], 'Status', readonly=True),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True,
            ondelete='set null'
        ),
        'chart_template_id': fields.many2one(
            'account.chart.template',
            'Chart Template',
            ondelete='cascade',
            required=True
        ),
        'code_digits': fields.integer(
            '# of digits',
            required=True,
            help="No. of digits to use for account code. "
                 "Make sure it is the same number as existing accounts."
        ),
        'lang': fields.selection(
            _get_lang_selection_options,
            'Language',
            size=5,
            help="For records searched by name (taxes, tax codes, fiscal positions), "
                 "the template name will be matched against the record name on this language."
        ),
        'update_tax_code': fields.boolean(
            'Update tax codes',
            help="Existing tax codes are updated."
            " Tax codes are searched by name."
        ),
        'update_tax': fields.boolean(
            'Update taxes',
            help="Existing taxes are updated. Taxes are searched by name."
        ),
        'update_account': fields.boolean(
            'Update accounts',
            help="Existing accounts are updated. Accounts are searched by code."
        ),
        'update_fiscal_position': fields.boolean(
            'Update fiscal positions',
            help="Existing fiscal positions are updated. Fiscal positions are searched by name."
        ),
        'update_children_accounts_parent': fields.boolean(
            "Update children accounts parent",
            help="Update the parent of accounts that seem (based on the code)"
                 " to be children of the newly created ones."
                 " If you had an account 430 with a child 4300000, and a 4300 "
                 "account is created, the 4300000 parent will be set to 4300."
        ),
        'continue_on_errors': fields.boolean(
            "Continue on errors",
            help="If set, the wizard will continue to the next step even if "
                 "there are minor errors (for example the parent account "
                 "of a new account couldn't be set)."
        ),
        'tax_code_ids': fields.one2many(
            'wizard.update.charts.accounts.tax.code',
            'update_chart_wizard_id',
            'Tax codes',
            ondelete='cascade'
        ),
        'tax_ids': fields.one2many(
            'wizard.update.charts.accounts.tax',
            'update_chart_wizard_id',
            'Taxes',
            ondelete='cascade'
        ),
        'account_ids': fields.one2many('wizard.update.charts.accounts.account',
                                       'update_chart_wizard_id', 'Accounts', ondelete='cascade'),
        'fiscal_position_ids': fields.one2many('wizard.update.charts.accounts.fiscal.position',
                                               'update_chart_wizard_id', 'Fiscal positions', ondelete='cascade'),
        'new_tax_codes': fields.integer('New tax codes', readonly=True),
        'new_taxes': fields.integer('New taxes', readonly=True),
        'new_accounts': fields.integer('New accounts', readonly=True),
        'new_fps': fields.integer('New fiscal positions', readonly=True),
        'updated_tax_codes': fields.integer('Updated tax codes', readonly=True),
        'updated_taxes': fields.integer('Updated taxes', readonly=True),
        'updated_accounts': fields.integer('Updated accounts', readonly=True),
        'updated_fps': fields.integer('Updated fiscal positions', readonly=True),
        'log': fields.text('Messages and Errors', readonly=True)
    }

    def name_search(self, cr, user, name,
                    args=None, operator='ilike', context=None, limit=80):
        """
        Redefine the search to search by company name.
        """
        if not name:
            name = '%'
        if not args:
            args = []
        if not context:
            context = {}
        args = args[:]
        ids = []
        ids = self.search(
            cr, user, [('company_id', operator, name)] + args, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        """
        Use the company name and template as name.
        """
        if context is None:
            context = {}
        if not len(ids):
            return []
        records = self.browse(cr, uid, ids, context)
        res = []
        for record in records:
            res.append((record.id, record.company_id.name +
                       ' - ' + record.chart_template_id.name))
        return res

    def _get_chart(self, cr, uid, context=None):
        """
        Returns the default chart template.
        """
        if context is None:
            context = {}
        ids = self.pool.get(
            'account.chart.template').search(cr, uid, [], context=context)
        if ids:
            return ids[0]
        return False

    def _get_code_digits(self, cr, uid, context=None, company_id=None):
        """
        Returns the default code size for the accounts.
        To figure out the number of digits of the accounts it look at the
        code size of the default receivable account of the company
        (or user's company if any company is given).
        """
        if context is None:
            context = {}
        property_obj = self.pool.get('ir.property')
        account_obj = self.pool.get('account.account')
        if not company_id:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            company_id = user.company_id.id
        property_ids = property_obj.search(cr, uid, [
            ('name', '=', 'property_account_receivable'),
            ('company_id', '=', company_id),
            ('res_id', '=', False),
            ('value_reference', '!=', False)
        ])
        if not property_ids:
            # Try to get a generic (no-company) property
            property_ids = property_obj.search(cr, uid, [
                ('name', '=', 'property_account_receivable'),
                ('res_id', '=', False),
                ('value_reference', '!=', False)
            ])
            number_digits = 6
        if property_ids:
            prop = property_obj.browse(
                cr, uid, property_ids[0], context=context)
            account_id = prop.value_reference.id
            if account_id:
                code = account_obj.read(
                    cr, uid, account_id, ['code'], context)['code']
                number_digits = len(code)
        return number_digits

    _defaults = {
        'state': 'init',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(
            cr, uid, [uid], context)[0].company_id.id,
        'chart_template_id': _get_chart,
        'update_tax_code': True,
        'update_tax': True,
        'update_account': True,
        'update_fiscal_position': True,
        'update_children_accounts_parent': True,
        'continue_on_errors': False,
        'lang': lambda self, cr, uid, context: context and context.get('lang') or None,
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        """
        Update the code size when the company changes
        """
        res = {
            'value': {
                'code_digits': self._get_code_digits(cr, uid, context=context, company_id=company_id),
            }
        }
        return res

    def action_init(self, cr, uid, ids, context=None):
        """
        Initial action that sets the initial state.
        """
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        self.write(cr, uid, ids, {'state': 'init'}, context)
        return _reopen(self, wizard.id, 'wizard.update.chart.accounts')

    ##########################################################################
    # Helper methods
    ##########################################################################

    def _map_tax_template(self, cr, uid, wizard, tax_templ_mapping,
                          tax_templ, context=None):
        """
        Adds a tax template -> tax id to the mapping.
        """
        if not tax_templ:
            return False
        if tax_templ_mapping.get(tax_templ.id):
            return tax_templ_mapping[tax_templ.id]
        # In other case
        tax_obj = self.pool['account.tax']
        criteria = ['|',
                    ('name', '=', tax_templ.name),
                    ('description', '=', tax_templ.name)]
        if tax_templ.description:
            criteria = (['|', '|'] + criteria +
                        [('description', '=', tax_templ.description),
                         ('name', '=', tax_templ.description)])
        tax_ids = tax_obj.search(cr, uid, criteria, context=context)
        tax_templ_mapping[tax_templ.id] = tax_ids and tax_ids[0] or False
        return tax_templ_mapping[tax_templ.id]

    def _map_tax_code_template(self, cr, uid, wizard,
                               tax_code_templ_mapping, tax_code_template,
                               context=None):
        """
        Adds a tax code template -> tax code id to the mapping.
        """
        if not tax_code_template:
            return False
        if not wizard.chart_template_id:
            return False
        if tax_code_templ_mapping.get(tax_code_template.id):
            return tax_code_templ_mapping[tax_code_template.id]
        # In other case
        tax_code_obj = self.pool['account.tax.code']
        root_tax_code_id = wizard.chart_template_id.tax_code_root_id.id
        tax_code_name = ((tax_code_template.id == root_tax_code_id) and
                         wizard.company_id.name or tax_code_template.name)
        tax_code_ids = tax_code_obj.search(cr, uid, [
            ('name', '=', tax_code_name),
            ('company_id', '=', wizard.company_id.id)
        ], context=context)
        if not tax_code_ids:
            # if we could not match no tax code template name,
            # try to match on tax code template code, if any
            tax_code_code = tax_code_template.code
            if tax_code_code:
                tax_code_ids = tax_code_obj.search(cr, uid, [
                    ('code', '=', tax_code_code),
                    ('company_id', '=', wizard.company_id.id)
                ], context=context)
        tax_code_templ_mapping[tax_code_template.id] = (tax_code_ids and
                                                        tax_code_ids[0] or
                                                        False)
        return tax_code_templ_mapping[tax_code_template.id]

    def _map_account_template(self, cr, uid, wizard, acc_templ_mapping,
                              acc_templ, context=None):
        """
        Adds an account template -> account id to the mapping
        """
        if not acc_templ:
            return False
        if acc_templ_mapping.get(acc_templ.id):
            return acc_templ_mapping[acc_templ.id]
        # In other case
        acc_obj = self.pool['account.account']
        code = acc_templ.code or ''
        if acc_templ.type != 'view':
            if code and len(code) <= wizard.code_digits:
                code = '%s%s' % (code, '0' * (wizard.code_digits - len(code)))
        acc_ids = acc_obj.search(cr, uid,
                                 [('code', '=', code),
                                  ('company_id', '=', wizard.company_id.id)],
                                 context=context)
        acc_templ_mapping[acc_templ.id] = acc_ids and acc_ids[0] or False
        return acc_templ_mapping[acc_templ.id]

    def _map_fp_template(self, cr, uid, wizard, fp_templ_mapping, fp_template, context=None):
        """
        Adds a fiscal position template -> fiscal position id to the mapping.
        """
        if not fp_template:
            return False
        if fp_templ_mapping.get(fp_template.id):
            return fp_templ_mapping[fp_template.id]
        # In other case
        fp_obj = self.pool['account.fiscal.position']
        fp_ids = fp_obj.search(cr, uid,
                               [('name', '=', fp_template.name),
                                ('company_id', '=', wizard.company_id.id)],
                               context=context)
        fp_templ_mapping[fp_template.id] = fp_ids and fp_ids[0] or False
        return fp_templ_mapping[fp_template.id]

    def _find_tax_codes(self, cr, uid, wizard, chart_template_ids,
                        context=None):
        """
        Search for, and load, tax code templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        if not wizard.chart_template_id:
            return {}
        new_tax_codes = 0
        updated_tax_codes = 0
        tax_code_template_mapping = {}
        tax_code_templ_obj = self.pool['account.tax.code.template']
        tax_code_obj = self.pool['account.tax.code']
        wiz_tax_code_obj = self.pool['wizard.update.charts.accounts.tax.code']
        # Remove previous tax codes
        wiz_tax_code_obj.unlink(cr, uid, wiz_tax_code_obj.search(cr, uid, []))
        # Search for new / updated tax codes
        root_tax_code_id = wizard.chart_template_id.tax_code_root_id.id
        children_tax_code_template = tax_code_templ_obj.search(cr, uid, [(
            'parent_id', 'child_of', [root_tax_code_id])], order='id',
            context=context)
        for tax_code_template in tax_code_templ_obj.browse(
                cr, uid,
                children_tax_code_template, context=context):
            # Ensure the tax code template is on the map (search for the mapped
            # tax code id).
            tax_code_id = self._map_tax_code_template(
                cr, uid, wizard,
                tax_code_template_mapping,
                tax_code_template, context=context
            )
            if not tax_code_id:
                new_tax_codes += 1
                wiz_tax_code_obj.create(cr, uid, {
                    'tax_code_id': tax_code_template.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                    'notes': _('Name or code not found.'),
                }, context)
            elif wizard.update_tax_code:
                # Check the tax code for changes.
                modified = False
                notes = ""
                tax_code = tax_code_obj.browse(
                    cr, uid, tax_code_id, context=context)
                if tax_code.code != tax_code_template.code:
                    notes += _("The code field is different.\n")
                    modified = True
                if tax_code.info != tax_code_template.info:
                    notes += _("The info field is different.\n")
                    modified = True
                if tax_code.sign != tax_code_template.sign:
                    notes += _("The sign field is different.\n")
                    modified = True
                # TODO: We could check other account fields for changes...
                if modified:
                    # Tax code to update.
                    updated_tax_codes += 1
                    wiz_tax_code_obj.create(cr, uid, {
                        'tax_code_id': tax_code_template.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_tax_code_id': tax_code_id,
                        'notes': notes,
                    }, context)
        return {
            'new': new_tax_codes,
            'updated': updated_tax_codes,
            'mapping': tax_code_template_mapping
        }

    def _find_taxes(self, cr, uid, wizard, chart_template_ids, context=None):
        """
        Search for, and load, tax templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        new_taxes = 0
        updated_taxes = 0
        tax_templ_mapping = {}
        tax_obj = self.pool['account.tax']
        tax_templ_obj = self.pool['account.tax.template']
        wiz_taxes_obj = self.pool['wizard.update.charts.accounts.tax']
        delay_wiz_tax = []
        # Remove previous taxes
        wiz_taxes_ids = wiz_taxes_obj.search(cr, uid, [], context=context)
        wiz_taxes_obj.unlink(cr, uid, wiz_taxes_ids, context=context)
        # Search for new / updated taxes
        tax_templ_ids = tax_templ_obj.search(
            cr, uid, [('chart_template_id', 'in', chart_template_ids)],
            context=context)
        for tax_templ in tax_templ_obj.browse(cr, uid, tax_templ_ids,
                                              context=context):
            # Ensure tax template is on the map (search for the mapped tax id)
            tax_id = self._map_tax_template(cr, uid, wizard,
                                            tax_templ_mapping,
                                            tax_templ, context=context)
            if not tax_id:
                new_taxes += 1
                vals_wiz = {
                    'tax_id': tax_templ.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                    'notes': _('Name or description not found.'),
                }
                if not tax_templ.parent_id:
                    wiz_taxes_obj.create(cr, uid, vals_wiz, context)
                else:
                    delay_wiz_tax.append(vals_wiz)
            elif wizard.update_tax:
                # Check the tax for changes.
                modified = False
                notes = ""
                tax = tax_obj.browse(cr, uid, tax_id, context=context)
                if tax.sequence != tax_templ.sequence:
                    notes += _("The sequence field is different.\n")
                    modified = True
                if tax.amount != tax_templ.amount:
                    notes += _("The amount field is different.\n")
                    modified = True
                if tax.type != tax_templ.type:
                    notes += _("The type field is different.\n")
                    modified = True
                if tax.applicable_type != tax_templ.applicable_type:
                    notes += _("The applicable type field is different.\n")
                    modified = True
                if tax.domain != tax_templ.domain:
                    notes += _("The domain field is different.\n")
                    modified = True
                if tax.child_depend != tax_templ.child_depend:
                    notes += _("The child depend field is different.\n")
                    modified = True
                if tax.python_compute != tax_templ.python_compute:
                    notes += _("The python compute field is different.\n")
                    modified = True
                # if tax.tax_group != tax_templ.tax_group:
                    # notes += _("The tax group field is different.\n")
                    # modified = True
                if tax.base_sign != tax_templ.base_sign:
                    notes += _("The base sign field is different.\n")
                    modified = True
                if tax.tax_sign != tax_templ.tax_sign:
                    notes += _("The tax sign field is different.\n")
                    modified = True
                if tax.include_base_amount != tax_templ.include_base_amount:
                    notes += _("The include base amount field is different.\n")
                    modified = True
                if tax.type_tax_use != tax_templ.type_tax_use:
                    notes += _("The type tax use field is different.\n")
                    modified = True
                # TODO: We could check other tax fields for changes...
                if modified:
                    # Tax code to update.
                    updated_taxes += 1
                    wiz_taxes_obj.create(cr, uid, {
                        'tax_id': tax_templ.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_tax_id': tax_id,
                        'notes': notes,
                    }, context)
        for delay_vals_wiz in delay_wiz_tax:
            wiz_taxes_obj.create(cr, uid, delay_vals_wiz, context)

        return {'new': new_taxes, 'updated': updated_taxes, 'mapping': tax_templ_mapping}

    def _find_accounts(self, cr, uid, wizard, context=None):
        """
        Search for, and load, account templates to create/update.
        """
        if not wizard.chart_template_id:
            return {}
        new_accounts = 0
        updated_accounts = 0
        acc_templ_mapping = {}
        acc_obj = self.pool['account.account']
        acc_templ_obj = self.pool['account.account.template']
        wiz_accounts = self.pool['wizard.update.charts.accounts.account']
        # Remove previous accounts
        wiz_accounts_ids = wiz_accounts.search(cr, uid, [], context=context)
        wiz_accounts.unlink(cr, uid, wiz_accounts_ids, context=context)
        # Search for new / updated accounts
        root_account_id = wizard.chart_template_id.account_root_id.id
        acc_templ_criteria = [('chart_template_id',
                               '=',
                               wizard.chart_template_id.id)]
        if root_account_id:
            acc_templ_criteria = (
                ['|'] + acc_templ_criteria +
                ['&', ('parent_id', 'child_of', [root_account_id]),
                 ('chart_template_id', '=', False)]
            )
        acc_ids = acc_templ_obj.search(cr, uid, acc_templ_criteria,
                                       context=context)
        acc_ids.sort()
        for acc_templ in acc_templ_obj.browse(cr, uid, acc_ids,
                                              context=context):
            # Ensure the account template is on the map (search for the mapped
            # account id).
            account_id = self._map_account_template(cr, uid, wizard,
                                                    acc_templ_mapping,
                                                    acc_templ,
                                                    context=context)
            if not account_id:
                new_accounts += 1
                wiz_accounts.create(cr, uid, {
                    'account_id': acc_templ.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                    'notes': _('Code not found.'),
                }, context)
            elif wizard.update_account:
                # Check the account for changes.
                modified = False
                notes = ""
                account = acc_obj.browse(cr, uid, account_id, context=context)
                if account.name != acc_templ.name and account.name != wizard.company_id.name:
                    notes += _("The name is different.\n")
                    modified = True
                if account.type != acc_templ.type:
                    notes += _("The type is different.\n")
                    modified = True
                if account.user_type != acc_templ.user_type:
                    notes += _("The user type is different.\n")
                    modified = True
                if account.reconcile != acc_templ.reconcile:
                    notes += _("The reconcile is different.\n")
                    modified = True
                # TODO: We could check other account fields for changes...
                if modified:
                    # Account to update.
                    updated_accounts += 1
                    wiz_accounts.create(cr, uid, {
                        'account_id': acc_templ.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_account_id': account_id,
                        'notes': notes,
                    }, context)
        return {'new': new_accounts,
                'updated': updated_accounts,
                'mapping': acc_templ_mapping}

    def _find_fiscal_positions(self, cr, uid, wizard, chart_template_ids,
                               context=None):
        """
        Search for, and load, fiscal position templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        new_fps = 0
        updated_fps = 0
        fp_templ_mapping = {}
        tax_templ_mapping = {}
        acc_templ_mapping = {}
        fp_templ_obj = self.pool['account.fiscal.position.template']
        fp_obj = self.pool['account.fiscal.position']
        wiz_fp = self.pool['wizard.update.charts.accounts.fiscal.position']
        # Remove previous fiscal positions
        wiz_fp.unlink(cr, uid, wiz_fp.search(cr, uid, []))
        # Search for new / updated fiscal positions
        fp_template_ids = fp_templ_obj.search(cr, uid,
                                              [('chart_template_id',
                                                'in',
                                                chart_template_ids)],
                                              context=context)
        for fp_templ in fp_templ_obj.browse(cr, uid, fp_template_ids,
                                            context=context):
            # Ensure the fiscal position template is on the map (search for the
            # mapped fiscal position id).
            fp_id = self._map_fp_template(cr, uid, wizard, fp_templ_mapping,
                                          fp_templ, context=context)
            if not fp_id:
                # New fiscal position template.
                new_fps += 1
                wiz_fp.create(cr, uid, {
                    'fiscal_position_id': fp_templ.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                    'notes': _('Name not found.'),
                }, context=context)
                continue
            # Check the fiscal position for changes
            modified = False
            notes = ""
            fp = fp_obj.browse(cr, uid, fp_id, context=context)
            # Check fiscal position taxes for changes.
            if fp_templ.tax_ids and fp.tax_ids:
                for fp_tax_templ in fp_templ.tax_ids:
                    found = False
                    tax_src_id = self._map_tax_template(cr, uid, wizard,
                                                        tax_templ_mapping,
                                                        fp_tax_templ.tax_src_id,
                                                        context=None)
                    tax_dest_id = self._map_tax_template(cr, uid, wizard,
                                                         tax_templ_mapping,
                                                         fp_tax_templ.tax_dest_id,
                                                         context=None)
                    for fp_tax in fp.tax_ids:
                        if fp_tax.tax_src_id.id == tax_src_id:
                            if not fp_tax.tax_dest_id:
                                if not tax_dest_id:
                                    found = True
                                    break
                            else:
                                if fp_tax.tax_dest_id.id == tax_dest_id:
                                    found = True
                                    break
                    if not found:
                        notes += _("Tax mapping not found on the fiscal position instance: %s -> %s.\n") % (
                            fp_tax_templ.tax_src_id.name,
                            fp_tax_templ.tax_dest_id and fp_tax_templ.tax_dest_id.name or _('None'))
                        modified = True
            elif fp_templ.tax_ids and not fp.tax_ids:
                notes += _("The template has taxes the fiscal position instance does not.\n")
                modified = True
            # Check fiscal position accounts for changes
            if fp_templ.account_ids and fp.account_ids:
                for fp_acc_templ in fp_templ.account_ids:
                    found = False
                    acc_src_id = self._map_account_template(
                        cr, uid, wizard, acc_templ_mapping,
                        fp_acc_templ.account_src_id, context=context)
                    acc_dest_id = self._map_account_template(
                        cr, uid, wizard, acc_templ_mapping,
                        fp_acc_templ.account_dest_id, context=context)
                    for fp_acc in fp.account_ids:
                        if (fp_acc.account_src_id.id == acc_src_id and
                                fp_acc.account_dest_id.id == acc_dest_id):
                            found = True
                            break
                    if not found:
                        notes += _(
                            "Account mapping not found on the fiscal "
                            "position instance: %s -> %s.\n") \
                            % (fp_acc_templ.account_src_id.name,
                               fp_acc_templ.account_dest_id.name)
                        modified = True
            elif fp_templ.account_ids and not fp.account_ids:
                notes += _("The template has accounts the fiscal position "
                           "instance does not.\n")
                modified = True
            if modified:
                # Fiscal position template to update
                updated_fps += 1
                wiz_fp.create(cr, uid, {
                    'fiscal_position_id': fp_templ.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'updated',
                    'update_fiscal_position_id': fp_id,
                    'notes': notes,
                }, context=context)
        return {'new': new_fps, 'updated': updated_fps, 'mapping': fp_templ_mapping}

    def action_find_records(self, cr, uid, ids, context=None):
        """
        Searchs for records to update/create and shows them
        """
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        if wizard.lang:
            context['lang'] = wizard.lang
        elif context.get('lang'):
            del context['lang']
        # Defaults when calculations are not done
        tax_codes_res = {}
        taxes_res = {}
        accounts_res = {}
        fps_res = {}
        # Get all chart templates involved
        wiz_obj = self.pool['wizard.multi.charts.accounts']
        chart_template_ids = wiz_obj._get_chart_parent_ids(
            cr, uid, wizard.chart_template_id, context=context)
        # Search for, and load, the records to create/update.
        if wizard.update_tax_code:
            tax_codes_res = self._find_tax_codes(cr, uid, wizard,
                                                 chart_template_ids,
                                                 context=context)
        if wizard.update_tax:
            taxes_res = self._find_taxes(cr, uid, wizard, chart_template_ids,
                                         context=context)
        if wizard.update_account:
            accounts_res = self._find_accounts(cr, uid, wizard,
                                               context=context)
        if wizard.update_fiscal_position:
            fps_res = self._find_fiscal_positions(cr, uid, wizard,
                                                  chart_template_ids,
                                                  context=context)
        # Write the results, and go to the next step.
        self.write(cr, uid, [wizard.id], {
            'state': 'ready',
            'new_tax_codes': tax_codes_res.get('new', 0),
            'new_taxes': taxes_res.get('new', 0),
            'new_accounts': accounts_res.get('new', 0),
            'new_fps': fps_res.get('new', 0),
            'updated_tax_codes': tax_codes_res.get('updated', 0),
            'updated_taxes': taxes_res.get('updated', 0),
            'updated_accounts': accounts_res.get('updated', 0),
            'updated_fps': fps_res.get('updated', 0),
        }, context)

        return _reopen(self, wizard.id, 'wizard.update.chart.accounts')

    def _update_tax_codes(self, cr, uid, wizard, log, context=None):
        """
        Search for, and load, tax code templates to create/update.
        """
        taxcodes = self.pool.get('account.tax.code')
        root_tax_code_id = wizard.chart_template_id.tax_code_root_id.id
        new_tax_codes = 0
        updated_tax_codes = 0
        tax_code_template_mapping = {}
        for wiz_tax_code in wizard.tax_code_ids:
            tax_code_template = wiz_tax_code.tax_code_id
            tax_code_name = ((root_tax_code_id == tax_code_template.id) and
                             wizard.company_id.name or tax_code_template.name)
            # Ensure the parent tax code template is on the map.
            self._map_tax_code_template(cr, uid, wizard,
                                        tax_code_template_mapping,
                                        tax_code_template.parent_id,
                                        context=context)
            # Values
            vals = {
                'name': tax_code_name,
                'code': tax_code_template.code,
                'info': tax_code_template.info,
                'parent_id': (tax_code_template.parent_id and
                              tax_code_template_mapping.get(tax_code_template.parent_id.id)),
                'company_id': wizard.company_id.id,
                'sign': tax_code_template.sign,
            }
            tax_code_id = None
            modified = False
            if wiz_tax_code.type == 'new':
                # Create the tax code
                tax_code_id = taxcodes.create(cr, uid, vals)
                log.add(_("Created tax code %s.\n") % tax_code_name)
                new_tax_codes += 1
                modified = True
            elif wizard.update_tax_code and wiz_tax_code.update_tax_code_id:
                # Update the tax code
                tax_code_id = wiz_tax_code.update_tax_code_id.id
                taxcodes.write(cr, uid, [tax_code_id], vals)
                log.add(_("Updated tax code %s.\n") % tax_code_name)
                updated_tax_codes += 1
                modified = True
            else:
                tax_code_id = wiz_tax_code.update_tax_code_id and wiz_tax_code.update_tax_code_id.id
                modified = False
            # Store the tax codes on the map
            tax_code_template_mapping[tax_code_template.id] = tax_code_id
            if modified:
                # Detect errors
                if (tax_code_template.parent_id and
                        not tax_code_template_mapping.get(tax_code_template.parent_id.id)):
                    log.add(
                        _("Tax code %s: The parent tax code %s can not be set.\n") % (
                            tax_code_name, tax_code_template.parent_id.name),
                        True
                    )
        return {
            'new': new_tax_codes,
            'updated': updated_tax_codes,
            'mapping': tax_code_template_mapping
        }

    def _update_taxes(self, cr, uid, wizard, log, tax_code_template_mapping, context=None):
        """
        Search for, and load, tax templates to create/update.
        """
        taxes = self.pool['account.tax']
        new_taxes = 0
        updated_taxes = 0
        tax_template_mapping = {}
        taxes_pending_for_accounts = {}
        for wiz_tax in wizard.tax_ids:
            tax_template = wiz_tax.tax_id
            # Ensure the parent tax template is on the map.
            self._map_tax_template(cr, uid, wizard, tax_template_mapping,
                                   tax_template.parent_id, context)
            # Ensure the referenced tax codes are on the map.
            tax_code_templates_to_find = [
                tax_template.base_code_id,
                tax_template.tax_code_id,
                tax_template.ref_base_code_id,
                tax_template.ref_tax_code_id
            ]
            for tax_code_template in [tmpl for tmpl in tax_code_templates_to_find if tmpl]:
                self._map_tax_code_template(cr, uid, wizard,
                                            tax_code_template_mapping,
                                            tax_code_template, context=context)
            # Values
            vals_tax = {
                'name': tax_template.name,
                'sequence': tax_template.sequence,
                'amount': tax_template.amount,
                'type': tax_template.type,
                'applicable_type': tax_template.applicable_type,
                'domain': tax_template.domain,
                'parent_id': tax_template.parent_id and tax_template_mapping.get(tax_template.parent_id.id),
                'child_depend': tax_template.child_depend,
                'python_compute': tax_template.python_compute,
                'python_compute_inv': tax_template.python_compute_inv,
                'python_applicable': tax_template.python_applicable,
                #'tax_group': tax_template.tax_group,
                'base_code_id': (tax_template.base_code_id and
                                 tax_code_template_mapping.get(tax_template.base_code_id.id)),
                'tax_code_id': (tax_template.tax_code_id and
                                tax_code_template_mapping.get(tax_template.tax_code_id.id)),
                'base_sign': tax_template.base_sign,
                'tax_sign': tax_template.tax_sign,
                'ref_base_code_id': (tax_template.ref_base_code_id and
                                     tax_code_template_mapping.get(tax_template.ref_base_code_id.id)),
                'ref_tax_code_id': (tax_template.ref_tax_code_id and
                                    tax_code_template_mapping.get(tax_template.ref_tax_code_id.id)),
                'ref_base_sign': tax_template.ref_base_sign,
                'ref_tax_sign': tax_template.ref_tax_sign,
                'include_base_amount': tax_template.include_base_amount,
                'description': tax_template.description,
                'company_id': wizard.company_id.id,
                'type_tax_use': tax_template.type_tax_use
            }
            tax_id = None
            modified = False
            if wiz_tax.type == 'new':
                # Create a new tax.
                tax_id = taxes.create(cr, uid, vals_tax)
                log.add(_("Created tax %s.\n") % tax_template.name)
                new_taxes += 1
                modified = True
            elif wizard.update_tax and wiz_tax.update_tax_id:
                # Update a tax.
                tax_id = wiz_tax.update_tax_id.id
                taxes.write(cr, uid, [tax_id], vals_tax)
                log.add(_("Updated tax %s.\n") % tax_template.name)
                updated_taxes += 1
                modified = True
            else:
                tax_id = wiz_tax.update_tax_id and wiz_tax.update_tax_id.id
            # Update the tax template map
            tax_template_mapping[tax_template.id] = tax_id
            if modified:
                # Add to the dict of taxes waiting for accounts.
                taxes_pending_for_accounts[tax_id] = {
                    'account_collected_id': (tax_template.account_collected_id and
                                             tax_template.account_collected_id.id or False),
                    'account_paid_id': (tax_template.account_paid_id and
                                        tax_template.account_paid_id.id or False),
                }
                # Detect errors
                if tax_template.parent_id and not tax_template_mapping.get(tax_template.parent_id.id):
                    log.add(
                        _("Tax %s: The parent tax %s can not be set.\n") % (
                            tax_template.name, tax_template.parent_id.name),
                        True
                    )
                if tax_template.base_code_id and not tax_code_template_mapping.get(tax_template.base_code_id.id):
                    log.add(
                        _("Tax %s: The tax code for the base %s can not be set.\n") % (
                            tax_template.name, tax_template.base_code_id.name),
                        True
                    )
                if tax_template.tax_code_id and not tax_code_template_mapping.get(tax_template.tax_code_id.id):
                    log.add(
                        _("Tax %s: The tax code for the tax %s can not be set.\n") % (
                            tax_template.name, tax_template.tax_code_id.name),
                        True
                    )
                if (tax_template.ref_base_code_id and
                        not tax_code_template_mapping.get(tax_template.ref_base_code_id.id)):
                    log.add(
                        _("Tax %s: The tax code for the base refund %s can not be set.\n") % (
                            tax_template.name, tax_template.ref_base_code_id.name),
                        True
                    )
                if tax_template.ref_tax_code_id and not tax_code_template_mapping.get(tax_template.ref_tax_code_id.id):
                    log.add(
                        _("Tax %s: The tax code for the tax refund %s can not be set.\n") % (
                            tax_template.name, tax_template.ref_tax_code_id.name),
                        True
                    )
        return {
            'new': new_taxes,
            'updated': updated_taxes,
            'mapping': tax_template_mapping,
            'pending': taxes_pending_for_accounts
        }

    def _update_children_accounts_parent(self, cr, uid, wizard, log, parent_account_id, context=None):
        """
        Updates the parent_id of accounts that seem to be children of the
        given account (accounts that start with the same code and are brothers
        of the first account).
        """
        account_account = self.pool.get('account.account')
        parent_account = account_account.browse(
            cr, uid, parent_account_id, context=context)

        if not parent_account.parent_id or not parent_account.code:
            return False

        children_ids = account_account.search(cr, uid, [
            ('company_id', '=',
             parent_account.company_id and parent_account.company_id.id),
            ('parent_id', '=', parent_account.parent_id.id),
            ('code', '=like', "%s%%" % parent_account.code),
            ('id', '!=', parent_account.id),
        ], context=context)

        if children_ids:
            try:
                account_account.write(cr, uid, children_ids, {'parent_id': parent_account.id}, context=context)
            except orm.except_orm, ex:
                log.add(
                    _("Exception setting the parent of account %s children: %s - %s.\n") % (
                        parent_account.code, ex.name, ex.value),
                    True
                )

        return True

    def _update_accounts(self, cr, uid, wizard, log, tax_template_mapping, context=None):
        """
        Search for, and load, account templates to create/update.
        """
        accounts = self.pool.get('account.account')
        root_account_id = wizard.chart_template_id.account_root_id.id
        # Disable the parent_store computing on account_account during the batch
        # processing, we will force _parent_store_compute afterwards.
        self.pool._init = True
        new_accounts = 0
        updated_accounts = 0
        account_template_mapping = {}
        for wiz_account in wizard.account_ids:
            account_template = wiz_account.account_id
            # Ensure the parent account template is on the map.
            self._map_account_template(cr, uid, wizard, account_template_mapping, account_template.parent_id, context)
            # Ensure the related tax templates are on the map.
            for tax_template in account_template.tax_ids:
                self._map_tax_template(cr, uid, wizard, tax_template_mapping,
                                       tax_template, context)
            # Get the tax ids
            tax_ids = [tax_template_mapping[tax_template.id]
                       for tax_template in account_template.tax_ids
                       if tax_template_mapping[tax_template.id]]
            # Calculate the account code (we need to add zeros to non-view
            # account codes)
            code = account_template.code or ''
            if account_template.type != 'view':
                if len(code) > 0 and len(code) <= wizard.code_digits:
                    code = '%s%s' % (
                        code, '0' * (wizard.code_digits - len(code)))
            # Values
            vals = {
                'name': (root_account_id == account_template.id) and wizard.company_id.name or account_template.name,
                #'sign': account_template.sign,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code,
                'type': account_template.type,
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': account_template.reconcile,
                'shortcut': account_template.shortcut,
                'note': account_template.note,
                'parent_id': (account_template.parent_id
                              and account_template_mapping.get(account_template.parent_id.id) or False),
                'tax_ids': [(6, 0, tax_ids)],
                'company_id': wizard.company_id.id,
            }
            account_id = None
            modified = False
            if wiz_account.type == 'new':
                # Create the account
                try:
                    account_id = accounts.create(cr, uid, vals)
                    log.add(_("Created account %s.\n") % code)
                    new_accounts += 1
                    modified = True
                except orm.except_orm, ex:
                    log.add(_("Exception creating account %s: %s - %s.\n")
                            % (code, ex.name, ex.value), True)
            elif wizard.update_account and wiz_account.update_account_id:
                # Update the account
                account_id = wiz_account.update_account_id.id
                try:
                    accounts.write(cr, uid, [account_id], vals)
                    log.add(_("Updated account %s.\n") % code)
                    updated_accounts += 1
                    modified = True
                except orm.except_orm, ex:
                    log.add(_("Exception writing account %s: %s - %s.\n")
                            % (code, ex.name, ex.value), True)
            else:
                account_id = wiz_account.update_account_id and wiz_account.update_account_id.id
            # Store the account on the map
            account_template_mapping[account_template.id] = account_id
            if modified:
                # Detect errors
                if account_template.parent_id and not account_template_mapping.get(account_template.parent_id.id):
                    log.add(
                        _("Account %s: The parent account %s can not be set.\n") % (
                            code, account_template.parent_id.code),
                        True
                    )
                # Set this account as the parent of the accounts that seem to
                # be its children (brothers starting with the same code).
                if wizard.update_children_accounts_parent:
                    self._update_children_accounts_parent(
                        cr, uid, wizard, log, account_id, context=context)
        # Reenable the parent_store computing on account_account
        # and force the recomputation.
        self.pool._init = False
        self.pool.get('account.account')._parent_store_compute(cr)
        return {
            'new': new_accounts,
            'updated': updated_accounts,
            'mapping': account_template_mapping
        }

    def _update_taxes_pending_for_accounts(self, cr, uid, wizard, log,
                                           taxes_pending_for_accounts,
                                           acc_templ_mapping, context=None):
        """
        Updates the taxes (created or updated on previous steps) to set
        the references to the accounts (the taxes where created/updated first,
        when the referenced accounts where still not available).
        """
        taxes = self.pool['account.tax']
        accounts_template = self.pool['account.account.template']
        for key, value in taxes_pending_for_accounts.items():
            # Ensure the related account templates are on the map.
            if value['account_collected_id']:
                acc_templ = accounts_template.browse(
                    cr, uid, value['account_collected_id'], context=context)
                self._map_account_template(cr, uid, wizard, acc_templ_mapping,
                                           acc_templ, context=context)
            if value['account_paid_id']:
                acc_templ = accounts_template.browse(
                    cr, uid, value['account_paid_id'], context=context)
                self._map_account_template(cr, uid, wizard, acc_templ_mapping,
                                           acc_templ, context=context)
            if value['account_collected_id'] or value['account_paid_id']:
                if (acc_templ_mapping.get(value['account_collected_id']) and
                        acc_templ_mapping.get(value['account_paid_id'])):
                    vals = {
                        'account_collected_id': acc_templ_mapping[value['account_collected_id']],
                        'account_paid_id': acc_templ_mapping[value['account_paid_id']],
                    }
                    taxes.write(cr, uid, [key], vals)
                else:
                    tax = taxes.browse(cr, uid, key)
                    if not acc_templ_mapping.get(value['account_collected_id']):
                        log.add(_("Tax %s: The collected account can not be set.\n") % (tax.name), True)
                    if not acc_templ_mapping.get(value['account_paid_id']):
                        log.add(_("Tax %s: The paid account can not be set.\n")
                                % (tax.name), True)

    def _update_fiscal_positions(self, cr, uid, wizard, log, tax_template_mapping, acc_templ_mapping, context=None):
        """
        Search for, and load, fiscal position templates to create/update.
        """
        fiscalpositions = self.pool.get('account.fiscal.position')
        fiscalpositions_taxes = self.pool.get('account.fiscal.position.tax')
        fiscalpositions_account = self.pool.get('account.fiscal.position.account')

        new_fps = 0
        updated_fps = 0

        for wiz_fp in wizard.fiscal_position_ids:
            fp_template = wiz_fp.fiscal_position_id
            fp_id = None
            modified = False
            if wiz_fp.type == 'new':
                # Create a new fiscal position
                vals_fp = {
                    'company_id': wizard.company_id.id,
                    'name': fp_template.name,
                }
                fp_id = fiscalpositions.create(cr, uid, vals_fp)
                new_fps += 1
                modified = True
            elif wizard.update_fiscal_position and wiz_fp.update_fiscal_position_id:
                # Update the given fiscal position (remove the tax and account
                # mappings, that will be regenerated later)
                fp_id = wiz_fp.update_fiscal_position_id.id
                updated_fps += 1
                modified = True
                # Remove the tax mappings
                fp_tax_ids = fiscalpositions_taxes.search(
                    cr, uid, [('position_id', '=', fp_id)])
                fiscalpositions_taxes.unlink(cr, uid, fp_tax_ids)
                # Remove the account mappings
                fp_account_ids = fiscalpositions_account.search(
                    cr, uid, [('position_id', '=', fp_id)])
                fiscalpositions_account.unlink(cr, uid, fp_account_ids)
            else:
                fp_id = wiz_fp.update_fiscal_position_id and wiz_fp.update_fiscal_position_id.id

            if modified:
                # (Re)create the tax mappings
                for fp_tax in fp_template.tax_ids:
                    # Ensure the related tax templates are on the map.
                    self._map_tax_template(cr, uid, wizard, tax_template_mapping, fp_tax.tax_src_id, context)
                    if fp_tax.tax_dest_id:
                        self._map_tax_template(cr, uid, wizard, tax_template_mapping, fp_tax.tax_dest_id, context)
                    # Create the fp tax mapping
                    vals_tax = {
                        'tax_src_id': tax_template_mapping.get(fp_tax.tax_src_id.id),
                        'tax_dest_id': fp_tax.tax_dest_id and tax_template_mapping.get(fp_tax.tax_dest_id.id),
                        'position_id': fp_id,
                    }
                    fiscalpositions_taxes.create(cr, uid, vals_tax)
                    # Check for errors
                    if not tax_template_mapping.get(fp_tax.tax_src_id.id):
                        log.add(
                            _("Fiscal position %s: The source tax %s can not be set.\n") % (
                                fp_template.name, fp_tax.tax_src_id.code),
                            True
                        )
                    if fp_tax.tax_dest_id and not tax_template_mapping.get(fp_tax.tax_dest_id.id):
                        log.add(
                            _("Fiscal position %s: The destination tax %s can not be set.\n") % (
                                fp_template.name, fp_tax.tax_dest_id.name),
                            True
                        )
                # (Re)create the account mappings
                for fp_account in fp_template.account_ids:
                    # Ensure the related account templates are on the map.
                    self._map_account_template(cr, uid, wizard,
                                               acc_templ_mapping,
                                               fp_account.account_src_id,
                                               context=context)
                    if fp_account.account_dest_id:
                        self._map_account_template(cr, uid, wizard,
                                                   acc_templ_mapping,
                                                   fp_account.account_dest_id,
                                                   context=context)
                    # Create the fp account mapping
                    vals_account = {
                        'account_src_id': acc_templ_mapping.get(fp_account.account_src_id.id),
                        'account_dest_id': (fp_account.account_dest_id and
                                            acc_templ_mapping.get(fp_account.account_dest_id.id)),
                        'position_id': fp_id,
                    }
                    fiscalpositions_account.create(cr, uid, vals_account)
                    # Check for errors
                    if not acc_templ_mapping.get(fp_account.account_src_id.id):
                        log.add(
                            _("Fiscal position %s: The source account %s can not be set.\n") % (
                                fp_template.name, fp_account.account_src_id.code),
                            True
                        )
                    if fp_account.account_dest_id and not acc_templ_mapping.get(fp_account.account_dest_id.id):
                        log.add(
                            _("Fiscal position %s: The destination account %s can not be set.\n") % (
                                fp_template.name, fp_account.account_dest_id.code),
                            True
                        )

            log.add(_("Created or updated fiscal position %s.\n")
                    % fp_template.name)
        return {'new': new_fps, 'updated': updated_fps}

    def action_update_records(self, cr, uid, ids, context=None):
        """
        Action that creates/updates the selected elements.
        """
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        if wizard.lang:
            context['lang'] = wizard.lang
        elif context.get('lang'):
            del context['lang']
        log = WizardLog()
        # Defaults when calculations are not done
        tax_codes_res = {'mapping': {}}
        taxes_res = {'mapping': {}, 'pending': {}}
        accounts_res = {'mapping': {}}
        fps_res = {}
        # Create or update the records.
        if wizard.update_tax_code:
            tax_codes_res = self._update_tax_codes(cr, uid, wizard, log,
                                                   context=context)
        if wizard.update_tax:
            taxes_res = self._update_taxes(cr, uid, wizard, log,
                                           tax_codes_res['mapping'],
                                           context=context)
        if wizard.update_account:
            accounts_res = self._update_accounts(cr, uid, wizard, log,
                                                 taxes_res['mapping'],
                                                 context=context)
        if wizard.update_tax and wizard.update_account:
            self._update_taxes_pending_for_accounts(cr, uid, wizard, log,
                                                    taxes_res['pending'],
                                                    accounts_res['mapping'],
                                                    context=context)
        if wizard.update_fiscal_position:
            fps_res = self._update_fiscal_positions(cr, uid, wizard, log,
                                                    taxes_res['mapping'],
                                                    accounts_res['mapping'],
                                                    context=context)
        # Check if errors where detected and wether we should stop.
        if log.has_errors() and not wizard.continue_on_errors:
            raise orm.except_orm(_('Error'), _(
                "One or more errors detected!\n\n%s") % log.get_errors_str())
        # Store the data and go to the next step.
        self.write(cr, uid, [wizard.id], {
            'state': 'done',
            'new_tax_codes': tax_codes_res.get('new', 0),
            'new_taxes': taxes_res.get('new', 0),
            'new_accounts': accounts_res .get('new', 0),
            'new_fps': fps_res.get('new', 0),
            'updated_tax_codes': tax_codes_res.get('updated', 0),
            'updated_taxes': taxes_res.get('updated', 0),
            'updated_accounts': accounts_res.get('updated', 0),
            'updated_fps': fps_res.get('updated', 0),
            'log': log(),
        }, context=context)
        return _reopen(self, wizard.id, 'wizard.update.chart.accounts')


class wizard_update_charts_accounts_tax_code(orm.TransientModel):
    """
    ******************************************************************
    Tax code that needs to be updated (new or updated in the template).
    ******************************************************************
    """
    _name = 'wizard.update.charts.accounts.tax.code'
    _columns = {
        'tax_code_id': fields.many2one(
            'account.tax.code.template',
            'Tax code template',
            required=True,
            ondelete='set null'
        ),
        'update_chart_wizard_id': fields.many2one(
            'wizard.update.charts.accounts',
            'Update chart wizard',
            required=True,
            ondelete='cascade'
        ),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_tax_code_id': fields.many2one(
            'account.tax.code',
            'Tax code to update',
            required=False,
            ondelete='set null'
        ),
        'notes': fields.text('Notes'),
    }
    _defaults = {
    }


class wizard_update_charts_accounts_tax(orm.TransientModel):
    """
    **************************************************************
    Tax that needs to be updated (new or updated in the template).
    **************************************************************
    """
    _name = 'wizard.update.charts.accounts.tax'
    _columns = {
        'tax_id': fields.many2one('account.tax.template', 'Tax template', required=True, ondelete='set null'),
        'update_chart_wizard_id': fields.many2one(
            'wizard.update.charts.accounts', 'Update chart wizard', required=True, ondelete='cascade'),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_tax_id': fields.many2one(
            'account.tax', 'Tax to update', required=False, ondelete='set null'),
        'notes': fields.text('Notes'),
    }

    _defaults = {
    }


class wizard_update_charts_accounts_account(orm.TransientModel):
    """
    ******************************************************************
    Account that needs to be updated (new or updated in the template).
    *******************************************************************
    """
    _name = 'wizard.update.charts.accounts.account'
    # The chart of accounts can have a lot of accounts, so we need an higher
    # limit for the objects in memory to let the wizard create all the items
    # at once.
    _columns = {
        'account_id': fields.many2one(
            'account.account.template',
            'Account template',
            required=True,
            ondelete='set null'
        ),
        'update_chart_wizard_id': fields.many2one(
            'wizard.update.charts.accounts',
            'Update chart wizard',
            required=True,
            ondelete='cascade'
        ),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_account_id': fields.many2one(
            'account.account',
            'Account to update',
            required=False,
            ondelete='set null'
        ),
        'notes': fields.text('Notes'),
    }

    _defaults = {
    }


class wizard_update_charts_accounts_fiscal_position(orm.TransientModel):
    """
    **************************************************************************
    Fiscal position that needs to be updated (new or updated in the template).
    **************************************************************************
    """
    _name = 'wizard.update.charts.accounts.fiscal.position'
    _columns = {
        'fiscal_position_id': fields.many2one(
            'account.fiscal.position.template',
            'Fiscal position template',
            required=True,
            ondelete='set null'
        ),
        'update_chart_wizard_id': fields.many2one(
            'wizard.update.charts.accounts',
            'Update chart wizard',
            required=True,
            ondelete='cascade'
        ),
        'type': fields.selection([
            ('new', 'New template'),
            ('updated', 'Updated template'),
        ], 'Type'),
        'update_fiscal_position_id': fields.many2one(
            'account.fiscal.position',
            'Fiscal position to update',
            required=False,
            ondelete='set null'
        ),
        'notes': fields.text('Notes'),
    }
    _defaults = {
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
