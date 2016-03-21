# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#    Copyright (c) 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#    @authors: Jordi Esteve (Zikzakmedia), Borja López Soilán (Pexego)
#    Copyright (c) 2015 Antiun Ingeniería S.L. (http://www.antiun.com)
#                       Antonio Espinosa <antonioea@antiun.com>
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
from openerp import models, fields, api, exceptions, _
from openerp.osv.orm import except_orm
from openerp.osv.osv import except_osv
import logging


def _reopen(self):
    return {
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_type': 'form',
        'res_id': self.id,
        'res_model': self._name,
        'target': 'new',
        # save original model in context,
        # because selecting the list of available
        # templates requires a model in context
        'context': {
            'default_model': self._name,
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
        self._logger = logging.getLogger("account_chart_update")

    def add(self, message, is_error=False):
        """Adds a message to the log."""
        if is_error:
            self._logger.warning(u"Log line: %s" % message)
            self.errors.append(message)
        else:
            self._logger.debug(u"Log line: %s" % message)
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


class WizardUpdateChartsAccounts(models.TransientModel):
    _name = 'wizard.update.charts.accounts'

    @api.model
    def _get_lang_selection_options(self):
        """Gets the available languages for the selection."""
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs] + [('', '')]

    @api.model
    def _get_chart(self):
        """Returns the default chart template."""
        templates = self.env['account.chart.template'].search([])
        return templates and templates[0] or False

    state = fields.Selection(
        selection=[('init', 'Step 1'),
                   ('ready', 'Step 2'),
                   ('done', 'Wizard completed')],
        string='Status', readonly=True, default='init')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        ondelete='set null', default=lambda self: self.env.user.company_id.id)
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template',
        ondelete='cascade', required=True, default=_get_chart)
    code_digits = fields.Integer(
        string='# of digits', required=True,
        help="No. of digits to use for account code. "
             "Make sure it is the same number as existing accounts.")
    lang = fields.Selection(
        _get_lang_selection_options, 'Language', size=5,
        help="For records searched by name (taxes, tax codes, fiscal "
             "positions), the template name will be matched against the "
             "record name on this language.",
        default=lambda self: self.env.context.get('lang') or self.user.lang)
    update_tax_code = fields.Boolean(
        string='Update tax codes', default=True,
        help="Existing tax codes are updated. Tax codes are searched by name.")
    update_tax = fields.Boolean(
        string='Update taxes', default=True,
        help="Existing taxes are updated. Taxes are searched by name.")
    update_account = fields.Boolean(
        string='Update accounts', default=True,
        help="Existing accounts are updated. Accounts are searched by code.")
    update_fiscal_position = fields.Boolean(
        string='Update fiscal positions', default=True,
        help="Existing fiscal positions are updated. Fiscal positions are "
             "searched by name.")
    update_children_accounts_parent = fields.Boolean(
        string="Update children accounts parent", default=True,
        help="Update the parent of accounts that seem (based on the code)"
             " to be children of the newly created ones."
             " If you had an account 430 with a child 4300000, and a 4300 "
             "account is created, the 4300000 parent will be set to 4300.")
    update_financial_reports = fields.Boolean(
        string="Update financial report accounts", default=True,
        help="Update the financial reports mapping the accounts")
    continue_on_errors = fields.Boolean(
        string="Continue on errors", default=False,
        help="If set, the wizard will continue to the next step even if "
             "there are minor errors (for example the parent account "
             "of a new account couldn't be set).")
    tax_code_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.tax.code',
        inverse_name='update_chart_wizard_id', string='Tax codes',
        ondelete='cascade')
    tax_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.tax', ondelete='cascade',
        inverse_name='update_chart_wizard_id', string='Taxes')
    account_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.account',
        inverse_name='update_chart_wizard_id', string='Accounts',
        ondelete='cascade')
    fiscal_position_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.fiscal.position',
        inverse_name='update_chart_wizard_id', string='Fiscal positions',
        ondelete='cascade')
    financial_report_ids = fields.One2many(
        comodel_name='wizard.update.charts.accounts.financial.report',
        inverse_name='update_chart_wizard_id', string='Financial reports',
        ondelete='cascade')
    new_tax_codes = fields.Integer(
        string='New tax codes', readonly=True,
        compute="_get_new_tax_codes_count")
    new_taxes = fields.Integer(
        string='New taxes', readonly=True, compute="_get_new_taxes_count")
    new_accounts = fields.Integer(
        string='New accounts', readonly=True,
        compute="_get_new_accounts_count")
    new_fps = fields.Integer(
        string='New fiscal positions', readonly=True,
        compute="_get_new_fps_count")
    updated_tax_codes = fields.Integer(
        string='Updated tax codes', readonly=True,
        compute="_get_updated_tax_codes_count")
    updated_taxes = fields.Integer(
        string='Updated taxes', readonly=True,
        compute="_get_updated_taxes_count")
    updated_accounts = fields.Integer(
        string='Updated accounts', readonly=True,
        compute="_get_updated_accounts_count")
    updated_fps = fields.Integer(
        string='Updated fiscal positions', readonly=True,
        compute="_get_updated_fps_count")
    deleted_tax_codes = fields.Integer(
        string='Deactivated tax codes', readonly=True,
        compute="_get_deleted_tax_codes_count")
    deleted_taxes = fields.Integer(
        string='Deactivated taxes', readonly=True,
        compute="_get_deleted_taxes_count")
    log = fields.Text(string='Messages and Errors', readonly=True)

    ##########################################################################
    # Compute methods
    ##########################################################################

    @api.one
    @api.depends('tax_code_ids')
    def _get_new_tax_codes_count(self):
        self.new_tax_codes = len(
            [x for x in self.tax_code_ids if x.type == 'new'])

    @api.one
    @api.depends('tax_ids')
    def _get_new_taxes_count(self):
        self.new_taxes = len(
            [x for x in self.tax_ids if x.type == 'new'])

    @api.one
    @api.depends('account_ids')
    def _get_new_accounts_count(self):
        self.new_accounts = len(
            [x for x in self.account_ids if x.type == 'new'])

    @api.one
    @api.depends('fiscal_position_ids')
    def _get_new_fps_count(self):
        self.new_fps = len(
            [x for x in self.fiscal_position_ids if x.type == 'new'])

    @api.one
    @api.depends('tax_code_ids')
    def _get_updated_tax_codes_count(self):
        self.updated_tax_codes = len(
            [x for x in self.tax_code_ids if x.type == 'updated'])

    @api.one
    @api.depends('tax_ids')
    def _get_updated_taxes_count(self):
        self.updated_taxes = len(
            [x for x in self.tax_ids if x.type == 'updated'])

    @api.one
    @api.depends('account_ids')
    def _get_updated_accounts_count(self):
        self.updated_accounts = len(
            [x for x in self.account_ids if x.type == 'updated'])

    @api.one
    @api.depends('fiscal_position_ids')
    def _get_updated_fps_count(self):
        self.updated_fps = len(
            [x for x in self.fiscal_position_ids if x.type == 'updated'])

    @api.one
    @api.depends('tax_code_ids')
    def _get_deleted_tax_codes_count(self):
        self.deleted_tax_codes = len(
            [x for x in self.tax_code_ids if x.type == 'deleted'])

    @api.one
    @api.depends('tax_ids')
    def _get_deleted_taxes_count(self):
        self.deleted_taxes = len(
            [x for x in self.tax_ids if x.type == 'deleted'])

    ##########################################################################
    # Main methods
    ##########################################################################

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        """
        Redefine the search to search by company name.
        """
        if not name:
            name = '%'
        if not args:
            args = []
        args = args[:]
        records = self.search([('company_id', operator, name)] + args,
                              limit=limit)
        return records.name_get()

    @api.multi
    def name_get(self):
        """Use the company name and template as name."""
        res = []
        for record in self:
            res.append(
                (record.id, "%s - %s" % (record.company_id.name,
                                         record.chart_template_id.name)))
        return res

    @api.model
    def _get_code_digits(self, company=None):
        """Returns the default code size for the accounts.
        To figure out the number of digits of the accounts it look at the
        code size of the default receivable account of the company
        (or user's company if any company is given).
        """
        property_obj = self.env['ir.property']
        if not company:
            company = self.env.user.company_id
        properties = property_obj.search(
            [('name', '=', 'property_account_receivable'),
             ('company_id', '=', company.id),
             ('res_id', '=', False),
             ('value_reference', '!=', False)])
        number_digits = 6
        if not properties:
            # Try to get a generic (no-company) property
            properties = property_obj.search(
                [('name', '=', 'property_account_receivable'),
                 ('res_id', '=', False),
                 ('value_reference', '!=', False)])
        if properties:
            account = property_obj.get_by_record(properties[0])
            if account:
                number_digits = len(account.code)
        return number_digits

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Update the code digits when the company changes"""
        self.code_digits = self._get_code_digits(company=self.company_id)

    @api.multi
    def action_init(self):
        """Initial action that sets the initial state."""
        self.write({'state': 'init'})
        return _reopen(self)

    @api.multi
    def action_find_records(self):
        """Searchs for records to update/create and shows them."""
        self = self.with_context(lang=self.lang)
        mapping_tax_codes = {}
        mapping_taxes = {}
        mapping_accounts = {}
        mapping_fps = {}
        # Get all chart templates involved
        wiz_obj = self.env['wizard.multi.charts.accounts']
        chart_template_ids = wiz_obj._get_chart_parent_ids(
            self.chart_template_id)
        # Search for, and load, the records to create/update.
        if self.update_tax_code:
            self._find_tax_codes(mapping_tax_codes)
        if self.update_tax:
            self._find_taxes(
                chart_template_ids, mapping_tax_codes, mapping_taxes,
                mapping_accounts)
        if self.update_account:
            self._find_accounts(mapping_accounts)
        if self.update_fiscal_position:
            self._find_fiscal_positions(
                chart_template_ids, mapping_taxes, mapping_accounts,
                mapping_fps)
        if self.update_financial_reports:
            self._find_financial_reports(mapping_accounts)
        # Write the results, and go to the next step.
        self.write({'state': 'ready'})
        return _reopen(self)

    @api.multi
    def action_update_records(self):
        """Action that creates/updates the selected elements."""
        self_lang = self.with_context(lang=self.lang)
        log = WizardLog()
        taxes_pending_for_accounts = {}
        mapping_tax_codes = {}
        mapping_taxes = {}
        mapping_accounts = {}
        # Create or update the records.
        if self_lang.update_tax_code:
            self_lang._update_tax_codes(log, mapping_tax_codes)
        if self_lang.update_tax:
            taxes_pending_for_accounts = self._update_taxes(
                log, mapping_tax_codes, mapping_taxes)
        if self_lang.update_account:
            self_lang._update_accounts(log, mapping_taxes, mapping_accounts)
        if self_lang.update_tax:
            self_lang._update_taxes_pending_for_accounts(
                log, taxes_pending_for_accounts, mapping_accounts)
        if self_lang.update_fiscal_position:
            self_lang._update_fiscal_positions(
                log, mapping_taxes, mapping_accounts)
        if self_lang.update_financial_reports:
            self._update_financial_reports(log)
        # Check if errors where detected and wether we should stop.
        if log.has_errors() and not self_lang.continue_on_errors:
            raise exceptions.Warning(
                _("One or more errors detected!\n\n%s") % log.get_errors_str())
        # Store the data and go to the next step.
        self_lang.write({'state': 'done', 'log': log()})
        return _reopen(self_lang)

    ##########################################################################
    # Helper methods
    ##########################################################################

    @api.model
    def _get_depth_first_tax_code_template_ids(self, root_tax_code):

        def get_children(tct):
            for child in tct.child_ids:
                res.append(child)
                get_children(child)

        res = [root_tax_code]
        get_children(root_tax_code)
        return res

    @api.multi
    def map_tax_code_template(self, tax_code_template, mapping_tax_codes):
        """Adds a tax code template -> tax code id to the mapping."""
        if not tax_code_template or not self.chart_template_id:
            return self.env['account.tax.code']
        if mapping_tax_codes.get(tax_code_template):
            return mapping_tax_codes[tax_code_template]
        # prepare a search context in order to
        # search inactive tax codes too, to avoid re-creating
        # tax codes that have been deactivated before
        tax_code_obj = self.env['account.tax.code'].with_context(
            active_test=False)
        root_tax_code = self.chart_template_id.tax_code_root_id
        tax_code_code = tax_code_template.code
        if tax_code_code:
            tax_codes = tax_code_obj.search(
                [('code', '=', tax_code_code),
                 ('company_id', '=', self.company_id.id)])
        if not tax_code_code or not tax_codes:
            tax_code_name = (
                tax_code_template == root_tax_code and
                self.company_id.name or tax_code_template.name)
            tax_codes = tax_code_obj.search(
                [('name', '=', tax_code_name),
                 ('company_id', '=', self.company_id.id)])
        mapping_tax_codes[tax_code_template] = (
            tax_codes and tax_codes[0] or self.env['account.tax.code'])
        return mapping_tax_codes[tax_code_template]

    @api.multi
    def map_tax_template(self, tax_template, mapping_taxes):
        """Adds a tax template -> tax id to the mapping."""
        if not tax_template:
            return self.env['account.tax']
        if mapping_taxes.get(tax_template):
            return mapping_taxes[tax_template]
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        tax_obj = self.env['account.tax'].with_context(active_test=False)
        criteria = ['|',
                    ('name', '=', tax_template.name),
                    ('description', '=', tax_template.name)]
        if tax_template.description:
            criteria = ['|', '|'] + criteria
            criteria += [('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', self.company_id.id)]
        taxes = tax_obj.search(criteria)
        mapping_taxes[tax_template] = (
            taxes and taxes[0] or self.env['account.tax'])
        return mapping_taxes[tax_template]

    @api.multi
    def map_account_template(self, account_template, mapping_accounts):
        """Adds an account template -> account id to the mapping."""
        if not account_template:
            return self.env['account.account']
        if mapping_accounts.get(account_template):
            return mapping_accounts[account_template]
        # In other case
        acc_obj = self.env['account.account']
        code = account_template.code or ''
        if account_template.type != 'view':
            if code and len(code) <= self.code_digits:
                code = '%s%s' % (code, '0' * (self.code_digits - len(code)))
        accounts = acc_obj.search(
            [('code', '=', code),
             ('company_id', '=', self.company_id.id)])
        mapping_accounts[account_template] = (
            accounts and accounts[0] or self.env['account.account'])
        return mapping_accounts[account_template]

    @api.multi
    def map_fp_template(self, fp_template, mapping_fps):
        """Adds a fiscal position template -> fiscal position id to the
        mapping.
        """
        if not fp_template:
            return self.env['account.fiscal.position']
        if mapping_fps.get(fp_template):
            return mapping_fps[fp_template]
        # In other case
        fps = self.env['account.fiscal.position'].search(
            [('name', '=', fp_template.name),
             ('company_id', '=', self.company_id.id)])
        mapping_fps[fp_template] = (
            fps and fps[0] or self.env['account.fiscal.position'])
        return mapping_fps[fp_template]

    ##########################################################################
    # Find methods
    ##########################################################################

    def _is_different_tax_code(
            self, tax_code, tax_code_template, mapping_tax_codes):
        """Check the tax code for changes.
        :return: An string that will be empty if no change detected.
        """
        notes = ""
        if tax_code.name != tax_code_template.name:
            notes += _("The name field is different.\n")
        if tax_code.code != tax_code_template.code:
            notes += _("The code field is different.\n")
        if tax_code.info != tax_code_template.info:
            notes += _("The info field is different.\n")
        if tax_code.sign != tax_code_template.sign:
            notes += _("The sign field is different.\n")
        if tax_code.notprintable != tax_code_template.notprintable:
            notes += _("The notprintable field is different.\n")
        if tax_code.sequence != tax_code_template.sequence:
            notes += _("The sequence field is different.\n")
        if tax_code.parent_id != self.map_tax_code_template(
                tax_code_template.parent_id, mapping_tax_codes):
            notes += _("The parent field is different.\n")
        return notes

    @api.one
    def _find_tax_codes(self, mapping_tax_codes):
        """Search for, and load, tax code templates to create/update."""
        wiz_tax_code_obj = self.env['wizard.update.charts.accounts.tax.code']
        # Remove previous tax codes
        self.tax_code_ids.unlink()
        # Search for new / updated tax codes
        children_tax_code_template = \
            self._get_depth_first_tax_code_template_ids(
                self.chart_template_id.tax_code_root_id)
        for tax_code_template in children_tax_code_template:
            if tax_code_template == self.chart_template_id.tax_code_root_id:
                continue
            tax_code = self.map_tax_code_template(
                tax_code_template, mapping_tax_codes)
            if not tax_code:
                wiz_tax_code_obj.create({
                    'tax_code_id': tax_code_template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('Name or code not found.'),
                })
            else:
                notes = self._is_different_tax_code(
                    tax_code, tax_code_template, mapping_tax_codes)
                if notes:
                    # Tax code to update
                    wiz_tax_code_obj.create({
                        'tax_code_id': tax_code_template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_tax_code_id': tax_code.id,
                        'notes': notes,
                    })
        # search for tax codes not in the template and propose them for
        # deactivation
        root_code = self.map_tax_code_template(
            self.chart_template_id.tax_code_root_id, mapping_tax_codes)
        tax_codes_to_delete = self.env['account.tax.code'].search(
            [('company_id', '=', self.company_id.id),
             ('id', '!=', root_code.id)])
        for tax_code in mapping_tax_codes.values():
            if tax_code:
                tax_codes_to_delete -= tax_code
        for tax_code_to_delete in tax_codes_to_delete:
            wiz_tax_code_obj.create({
                'tax_code_id': False,
                'update_chart_wizard_id': self.id,
                'type': 'deleted',
                'update_tax_code_id': tax_code_to_delete.id,
                'notes': _("To deactivate: not in the template"),
            })

    def _is_different_tax(self, tax, tax_template, mapping_taxes,
                          mapping_tax_codes, mapping_accounts):
        """Check the tax for changes.
        :return: An string that will be empty if no change detected.
        """
        notes = ""
        if not tax.active:
            notes += _("Tax is disabled.\n")
        if tax.name != tax_template.name:
            notes += _("The name field is different.\n")
        if tax.description != tax_template.description:
            notes += _("The description field is different.\n")
        if tax.sequence != tax_template.sequence:
            notes += _("The sequence field is different.\n")
        if tax.amount != tax_template.amount:
            notes += _("The amount field is different.\n")
        if tax.type != tax_template.type:
            notes += _("The type field is different.\n")
        if tax.applicable_type != tax_template.applicable_type:
            notes += _("The applicable type field is different.\n")
        if tax.domain != tax_template.domain:
            notes += _("The domain field is different.\n")
        if tax.child_depend != tax_template.child_depend:
            notes += _("The child depend field is different.\n")
        if tax.parent_id != self.map_tax_template(tax_template.parent_id,
                                                  mapping_taxes):
            notes += _("The parent_id field is different.\n")
        if tax.python_compute != tax_template.python_compute:
            notes += _("The python compute field is different.\n")
        # if tax.tax_group != tax_template.tax_group:
            # notes += _("The tax group field is different.\n")
        if tax.base_sign != tax_template.base_sign:
            notes += _("The base sign field is different.\n")
        if tax.tax_sign != tax_template.tax_sign:
            notes += _("The tax sign field is different.\n")
        if tax.include_base_amount != tax_template.include_base_amount:
            notes += _("The include base amount field is different.\n")
        if tax.type_tax_use != tax_template.type_tax_use:
            notes += _("The type tax use field is different.\n")
        if tax.price_include != tax_template.price_include:
            notes += _("The Tax Included in Price field is different.\n")
        # compare tax code fields
        if tax.base_code_id != self.map_tax_code_template(
                tax_template.base_code_id, mapping_tax_codes):
            notes += _("The base_code_id field is different.\n")
        if tax.tax_code_id != self.map_tax_code_template(
                tax_template.tax_code_id, mapping_tax_codes):
            notes += _("The tax_code_id field is different.\n")
        if tax.ref_base_code_id != self.map_tax_code_template(
                tax_template.ref_base_code_id, mapping_tax_codes):
            notes += _("The ref_base_code_id field is different.\n")
        if tax.ref_tax_code_id != self.map_tax_code_template(
                tax_template.ref_tax_code_id, mapping_tax_codes):
            notes += _("The ref_tax_code_id field is different.\n")
        # compare tax account fields
        if tax.account_paid_id != self.map_account_template(
                tax_template.account_paid_id, mapping_accounts):
            notes += _("The account_paid field is different.\n")
        if tax.account_collected_id != self.map_account_template(
                tax_template.account_collected_id, mapping_accounts):
            notes += _("The account_collected field is different.\n")
        return notes

    @api.one
    def _find_taxes(self, chart_template_ids, mapping_tax_codes,
                    mapping_taxes, mapping_accounts):
        """Search for, and load, tax templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        wiz_taxes_obj = self.env['wizard.update.charts.accounts.tax']
        delay_wiz_tax = []
        # Remove previous taxes
        self.tax_ids.unlink()
        # Search for new / updated taxes
        tax_templates = self.env['account.tax.template'].search(
            [('chart_template_id', 'in', chart_template_ids)])
        for tax_template in tax_templates:
            # Ensure tax template is on the map (search for the mapped tax id)
            tax = self.map_tax_template(tax_template, mapping_taxes)
            if not tax:
                vals_wiz = {
                    'tax_id': tax_template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('Name or description not found.'),
                }
                if not tax_template.parent_id:
                    wiz_taxes_obj.create(vals_wiz)
                else:
                    delay_wiz_tax.append(vals_wiz)
            else:
                # Check the tax for changes.
                notes = self._is_different_tax(
                    tax, tax_template, mapping_taxes, mapping_tax_codes,
                    mapping_accounts)
                if notes:
                    # Tax code to update.
                    wiz_taxes_obj.create({
                        'tax_id': tax_template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_tax_id': tax.id,
                        'notes': notes,
                    })
        for delay_vals_wiz in delay_wiz_tax:
            wiz_taxes_obj.create(delay_vals_wiz)
        # search for taxes not in the template and propose them for
        # deactivation
        taxes_to_delete = self.env['account.tax'].search(
            [('company_id', '=', self.company_id.id)])
        for tax in mapping_taxes.values():
            if tax:
                taxes_to_delete -= tax
        for tax_to_delete in taxes_to_delete:
            wiz_taxes_obj.create({
                'tax_id': False,
                'update_chart_wizard_id': self.id,
                'type': 'deleted',
                'update_tax_id': tax_to_delete.id,
                'notes': _("To deactivate: not in the template"),
            })

    def _is_different_account(self, account, account_template):
        notes = ""
        if (account.name != account_template.name and
                account.name != self.company_id.name):
            notes += _("The name is different.\n")
        if account.type != account_template.type:
            notes += _("The type is different.\n")
        if account.user_type != account_template.user_type:
            notes += _("The user type is different.\n")
        if account.reconcile != account_template.reconcile:
            notes += _("The reconcile is different.\n")
        return notes

    def _acc_tmpl_to_search_criteria(self, chart_template):
        root_account_id = chart_template.account_root_id.id
        acc_templ_criteria = [
            ('chart_template_id', '=', self.chart_template_id.id)]
        if root_account_id:
            acc_templ_criteria = ['|'] + acc_templ_criteria
            acc_templ_criteria += [
                '&', ('parent_id', 'child_of', [root_account_id]),
                ('chart_template_id', '=', False)]
        if chart_template.parent_id:
            acc_templ_criteria = ['|'] + acc_templ_criteria
            acc_templ_criteria += self._acc_tmpl_to_search_criteria(
                chart_template.parent_id)
        return acc_templ_criteria

    @api.one
    def _find_accounts(self, mapping_accounts):
        """Search for, and load, account templates to create/update."""
        wiz_accounts = self.env['wizard.update.charts.accounts.account']
        # Remove previous accounts
        self.account_ids.unlink()
        # Search for new / updated accounts
        acc_templ_criteria = self._acc_tmpl_to_search_criteria(
            self.chart_template_id)
        account_templates = self.env['account.account.template'].search(
            acc_templ_criteria)
        for account_template in account_templates:
            # Ensure the account template is on the map (search for the mapped
            # account id).
            account = self.map_account_template(
                account_template, mapping_accounts)
            if not account:
                wiz_accounts.create({
                    'account_id': account_template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('Code not found.'),
                })
            else:
                # Check the account for changes.
                notes = self._is_different_account(account, account_template)
                if notes:
                    # Account to update.
                    wiz_accounts.create({
                        'account_id': account_template.id,
                        'update_chart_wizard_id': self.id,
                        'type': 'updated',
                        'update_account_id': account.id,
                        'notes': notes,
                    })

    def _is_different_fiscal_position(self, fp, fp_template, mapping_taxes,
                                      mapping_accounts):
        notes = ""
        # Check fiscal position taxes for changes.
        if fp_template.tax_ids and fp.tax_ids:
            for fp_tax_templ in fp_template.tax_ids:
                found = False
                tax_src_id = self.map_tax_template(
                    fp_tax_templ.tax_src_id, mapping_taxes)
                tax_dest_id = self.map_tax_template(
                    fp_tax_templ.tax_dest_id, mapping_taxes)
                for fp_tax in fp.tax_ids:
                    if fp_tax.tax_src_id == tax_src_id:
                        if not fp_tax.tax_dest_id:
                            if not tax_dest_id:
                                found = True
                                break
                        else:
                            if fp_tax.tax_dest_id == tax_dest_id:
                                found = True
                                break
                if not found:
                    msg = fp_tax_templ.tax_dest_id.name or _('None')
                    notes += _(
                        "Tax mapping not found on the fiscal position "
                        "instance: %s -> %s.\n") % (
                            fp_tax_templ.tax_src_id.name, msg)
        elif fp_template.tax_ids and not fp.tax_ids:
            notes += _("The template has taxes the fiscal position instance "
                       "does not.\n")
        # Check fiscal position accounts for changes
        if fp_template.account_ids and fp.account_ids:
            for fp_acc_templ in fp_template.account_ids:
                found = False
                acc_src_id = self.map_account_template(
                    fp_acc_templ.account_src_id, mapping_accounts)
                acc_dest_id = self.map_account_template(
                    fp_acc_templ.account_dest_id, mapping_accounts)
                for fp_acc in fp.account_ids:
                    if (fp_acc.account_src_id == acc_src_id and
                            fp_acc.account_dest_id == acc_dest_id):
                        found = True
                        break
                if not found:
                    notes += _(
                        "Account mapping not found on the fiscal "
                        "position instance: %s -> %s.\n") % (
                            fp_acc_templ.account_src_id.name,
                            fp_acc_templ.account_dest_id.name)
        elif fp_template.account_ids and not fp.account_ids:
            notes += _("The template has accounts the fiscal position "
                       "instance does not.\n")
        return notes

    @api.one
    def _find_fiscal_positions(self, chart_template_ids, mapping_taxes,
                               mapping_accounts, mapping_fps):
        """Search for, and load, fiscal position templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        wiz_fp = self.env['wizard.update.charts.accounts.fiscal.position']
        # Remove previous fiscal positions
        self.fiscal_position_ids.unlink()
        # Search for new / updated fiscal positions
        fp_templates = self.env['account.fiscal.position.template'].search(
            [('chart_template_id', 'in', chart_template_ids)])
        for fp_template in fp_templates:
            # Ensure the fiscal position template is on the map (search for the
            # mapped fiscal position id).
            fp = self.map_fp_template(fp_template, mapping_fps)
            if not fp:
                # New fiscal position template.
                wiz_fp.create({
                    'fiscal_position_id': fp_template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'new',
                    'notes': _('Name not found.')
                })
                continue
            # Check the fiscal position for changes
            notes = self._is_different_fiscal_position(
                fp, fp_template, mapping_taxes, mapping_accounts)
            if notes:
                # Fiscal position template to update
                wiz_fp.create({
                    'fiscal_position_id': fp_template.id,
                    'update_chart_wizard_id': self.id,
                    'type': 'updated',
                    'update_fiscal_position_id': fp.id,
                    'notes': notes,
                })

    @api.one
    def _find_financial_reports(self, mapping_accounts):
        wiz_fr = self.env['wizard.update.charts.accounts.financial.report']
        # Remove previous financial reports
        self.financial_report_ids.unlink()
        # Search for new / updated accounts
        root_account_id = self.chart_template_id.account_root_id.id
        acc_templ_criteria = [
            ('chart_template_id', '=', self.chart_template_id.id)]
        if root_account_id:
            acc_templ_criteria = ['|'] + acc_templ_criteria
            acc_templ_criteria += [
                '&', ('parent_id', 'child_of', [root_account_id]),
                ('chart_template_id', '=', False)]
        account_templates = self.env['account.account.template'].search(
            acc_templ_criteria)
        for account_template in account_templates:
            template_fr_ids = set([fr.id for fr in
                                   account_template.financial_report_ids])
            account = self.map_account_template(
                account_template, mapping_accounts)
            if account:
                fr_ids = set([fr.id for fr in
                              account.financial_report_ids])
                new_fr_ids = template_fr_ids - fr_ids
                for fr_id in new_fr_ids:
                    wiz_fr.create({
                        'update_chart_wizard_id': self.id,
                        'type': 'new',
                        'account_id': account.id,
                        'financial_report_id': fr_id,
                    })
                deleted_fr_ids = fr_ids - template_fr_ids
                for fr_id in deleted_fr_ids:
                    wiz_fr.create({
                        'update_chart_wizard_id': self.id,
                        'type': 'deleted',
                        'account_id': account.id,
                        'financial_report_id': fr_id,
                    })
            else:
                for fr_id in template_fr_ids:
                    wiz_fr.create({
                        'update_chart_wizard_id': self.id,
                        'type': 'warn',
                        'financial_report_id': fr_id,
                        'notes': ('Missing account %s' %
                                  account_template.code),
                    })

    ##########################################################################
    # Update methods
    ##########################################################################

    def _prepare_tax_code_vals(self, tax_code_template, mapping_tax_codes):
        parent_code = self.map_tax_code_template(
            tax_code_template.parent_id, mapping_tax_codes)
        return {
            'name': tax_code_template.name,
            'code': tax_code_template.code,
            'info': tax_code_template.info,
            'parent_id': parent_code.id,
            'company_id': self.company_id.id,
            'sign': tax_code_template.sign,
            'notprintable': tax_code_template.notprintable,
            'sequence': tax_code_template.sequence,
        }

    @api.multi
    def _update_tax_codes(self, log, mapping_tax_codes):
        """Process tax codes to create/update/deactivate."""
        tax_code_obj = self.env['account.tax.code']
        # process new/updated
        for wiz_tax_code in self.tax_code_ids:
            if wiz_tax_code.type == 'deleted':
                continue
            tax_code_template = wiz_tax_code.tax_code_id
            # Values
            vals = self._prepare_tax_code_vals(
                tax_code_template, mapping_tax_codes)
            if wiz_tax_code.type == 'new':
                # Create the tax code
                tax_code = tax_code_obj.create(vals)
                mapping_tax_codes[tax_code_template] = tax_code
                log.add(_("Created tax code %s.\n") % vals['name'])
            elif wiz_tax_code.update_tax_code_id:
                # Update the tax code
                wiz_tax_code.update_tax_code_id.write(vals)
                log.add(_("Updated tax code %s.\n") % vals['name'])
        # process deleted
        tax_codes_to_delete = self.tax_code_ids.filtered(
            lambda x: x.type == 'deleted').mapped('update_tax_code_id')
        tax_codes_to_delete.write({'active': False})
        log.add(_("Deactivated %d tax codes\n" % len(tax_codes_to_delete)))

    def _prepare_tax_vals(self, tax_template, mapping_tax_codes,
                          mapping_taxes):
        return {
            'active': True,
            'name': tax_template.name,
            'sequence': tax_template.sequence,
            'amount': tax_template.amount,
            'type': tax_template.type,
            'applicable_type': tax_template.applicable_type,
            'domain': tax_template.domain,
            'parent_id': self.map_tax_template(
                tax_template.parent_id, mapping_taxes).id,
            'child_depend': tax_template.child_depend,
            'python_compute': tax_template.python_compute,
            'python_compute_inv': tax_template.python_compute_inv,
            'python_applicable': tax_template.python_applicable,
            'base_code_id': (
                self.map_tax_code_template(
                    tax_template.base_code_id, mapping_tax_codes).id),
            'tax_code_id': (
                self.map_tax_code_template(
                    tax_template.tax_code_id, mapping_tax_codes).id),
            'base_sign': tax_template.base_sign,
            'tax_sign': tax_template.tax_sign,
            'ref_base_code_id': (
                self.map_tax_code_template(
                    tax_template.ref_base_code_id, mapping_tax_codes).id),
            'ref_tax_code_id': (
                self.map_tax_code_template(
                    tax_template.ref_tax_code_id, mapping_tax_codes).id),
            'ref_base_sign': tax_template.ref_base_sign,
            'ref_tax_sign': tax_template.ref_tax_sign,
            'include_base_amount': tax_template.include_base_amount,
            'description': tax_template.description,
            'company_id': self.company_id.id,
            'type_tax_use': tax_template.type_tax_use,
            'price_include': tax_template.price_include,
        }

    @api.multi
    def _update_taxes(self, log, mapping_tax_codes, mapping_taxes):
        """Process taxes to create/update."""
        tax_obj = self.env['account.tax']
        taxes_pending_for_accounts = {}
        for wiz_tax in self.tax_ids:
            if wiz_tax.type == 'deleted':
                continue
            tax_template = wiz_tax.tax_id
            vals = self._prepare_tax_vals(
                tax_template, mapping_taxes, mapping_tax_codes)
            if wiz_tax.type == 'new':
                # Create a new tax.
                tax = tax_obj.create(vals)
                mapping_taxes[tax_template] = tax
                log.add(_("Created tax %s.\n") % tax_template.name)
            elif wiz_tax.update_tax_id:
                # Update the tax
                wiz_tax.update_tax_id.write(vals)
                tax = wiz_tax.update_tax_id
                log.add(_("Updated tax %s.\n") % tax_template.name)
            # Add to the dict of taxes waiting for accounts
            taxes_pending_for_accounts[tax] = {
                'account_collected_id': tax_template.account_collected_id,
                'account_paid_id': tax_template.account_paid_id,
            }
        # process deleted
        taxes_to_delete = self.tax_ids.filtered(
            lambda x: x.type == 'deleted').mapped('update_tax_id')
        taxes_to_delete.write({'active': False})
        log.add(_("Deactivated %d taxes\n" % len(taxes_to_delete)))
        return taxes_pending_for_accounts

    @api.multi
    def _update_children_accounts_parent(self, log, parent_account):
        """Updates the parent_id of accounts that seem to be children of the
        given account (accounts that start with the same code and are brothers
        of the first account).
        """
        account_obj = self.env['account.account']
        if not parent_account.parent_id or not parent_account.code:
            return False
        children = account_obj.search(
            [('company_id', '=', parent_account.company_id.id),
             ('parent_id', '=', parent_account.parent_id.id),
             ('code', '=like', "%s%%" % parent_account.code),
             ('id', '!=', parent_account.id)])
        if children:
            try:
                children.write({'parent_id': parent_account.id})
            except (exceptions.Warning, except_orm, except_osv) as ex:
                log.add(_("Exception setting the parent of account %s "
                          "children: %s - %s.\n") % (parent_account.code,
                                                     ex.name, ex.value), True)
        return True

    def _prepare_account_vals(self, account_template, mapping_taxes,
                              mapping_accounts):
        root_account_id = self.chart_template_id.account_root_id.id
        # Get the taxes
        taxes = [self.map_tax_template(tax_template, mapping_taxes)
                 for tax_template in account_template.tax_ids
                 if self.map_tax_template(tax_template, mapping_taxes)]
        # Calculate the account code (we need to add zeros to non-view
        # account codes)
        code = account_template.code or ''
        if account_template.type != 'view':
            if len(code) and len(code) <= self.code_digits:
                code = '%s%s' % (code, '0' * (self.code_digits - len(code)))
        return {
            'name': ((root_account_id == account_template.id) and
                     self.company_id.name or account_template.name),
            'currency_id': account_template.currency_id,
            'code': code,
            'type': account_template.type,
            'user_type': account_template.user_type.id,
            'reconcile': account_template.reconcile,
            'shortcut': account_template.shortcut,
            'note': account_template.note,
            'parent_id': (
                self.map_account_template(
                    account_template.parent_id, mapping_accounts).id),
            'tax_ids': [(6, 0, taxes)],
            'company_id': self.company_id.id,
        }

    @api.multi
    def _update_accounts(self, log, mapping_taxes, mapping_accounts):
        """Process accounts to create/update."""
        account_obj = self.env['account.account']
        # Disable the parent_store computing on account_account
        # during the batch processing,
        # We will force _parent_store_compute afterwards.
        account_obj._init = True
        for wiz_account in self.account_ids:
            account_template = wiz_account.account_id
            vals = self._prepare_account_vals(
                account_template, mapping_taxes, mapping_accounts)
            if wiz_account.type == 'new':
                # Create the account
                try:
                    account = account_obj.create(vals)
                    mapping_accounts[account_template] = account
                    log.add(_("Created account %s.\n") % vals['code'])
                except (exceptions.Warning, except_orm, except_osv) as ex:
                    log.add(_("Exception creating account %s: %s - %s.\n") %
                            (vals['code'], ex.name, ex.value), True)
            else:
                # Update the account
                account = wiz_account.update_account_id
                # Don't write again the same code - it may give an error
                code = vals.pop('code')
                try:
                    account.write(vals)
                    log.add(_("Updated account %s.\n") % code)
                except (exceptions.Warning, except_orm, except_osv) as ex:
                    log.add(_("Exception writing account %s: %s - %s.\n") %
                            (code, ex.name, ex.value), True)
            # Set this account as the parent of the accounts that seem to
            # be its children (brothers starting with the same code).
            if self.update_children_accounts_parent:
                self._update_children_accounts_parent(log, account)
        # Reenable the parent_store computing on account_account
        # and force the recomputation.
        account_obj._init = False
        account_obj._parent_store_compute()

    @api.multi
    def _update_taxes_pending_for_accounts(
            self, log, taxes_pending_for_accounts, mapping_accounts):
        """Updates the taxes (created or updated on previous steps) to set
        the references to the accounts (the taxes where created/updated first,
        when the referenced accounts are still not available).
        """
        for tax, accounts in taxes_pending_for_accounts.items():
            # Ensure the related account templates are on the map.
            for key, value in accounts.iteritems():
                if not value:
                    continue
                if not self.map_account_template(value, mapping_accounts):
                    if key == 'account_collected_id':
                        log.add(_("Tax %s: The collected account can not be "
                                  "set.\n") % tax.name, True)
                    else:
                        log.add(_("Tax %s: The paid account can not be set.\n")
                                % tax.name, True)
                tax.write({key: self.map_account_template(
                    value, mapping_accounts).id})

    def _prepare_fp_vals(self, fp_template, mapping_taxes, mapping_accounts):
        # Tax mappings
        tax_mapping = []
        for fp_tax in fp_template.tax_ids:
            # Create the fp tax mapping
            tax_mapping.append({
                'tax_src_id': self.map_tax_template(
                    fp_tax.tax_src_id, mapping_taxes).id,
                'tax_dest_id': self.map_tax_template(
                    fp_tax.tax_dest_id, mapping_taxes).id,
            })
        # Account mappings
        account_mapping = []
        for fp_account in fp_template.account_ids:
            # Create the fp account mapping
            account_mapping.append({
                'account_src_id': (
                    self.map_account_template(
                        fp_account.account_src_id, mapping_accounts).id),
                'account_dest_id': (
                    self.map_account_template(
                        fp_account.account_dest_id, mapping_accounts).id),
            })
        return {
            'company_id': self.company_id.id,
            'name': fp_template.name,
            'tax_ids': [(0, 0, x) for x in tax_mapping],
            'account_ids': [(0, 0, x) for x in account_mapping],
        }

    @api.multi
    def _update_fiscal_positions(self, log, mapping_taxes, mapping_accounts):
        """Process fiscal position templates to create/update."""
        for wiz_fp in self.fiscal_position_ids:
            fp_template = wiz_fp.fiscal_position_id
            vals = self._prepare_fp_vals(
                fp_template, mapping_taxes, mapping_accounts)
            if wiz_fp.type == 'new':
                # Create a new fiscal position
                fp = self.env['account.fiscal.position'].create(vals)
            else:
                # Update the given fiscal position (remove the tax and account
                # mappings, that will be regenerated later)
                fp = wiz_fp.update_fiscal_position_id
                fp.tax_ids.unlink()
                fp.account_ids.unlink()
                fp.write(vals)
            log.add(_("Created or updated fiscal position %s.\n") %
                    fp_template.name)

    @api.multi
    def _update_financial_reports(self, log):
        for wiz_fr in self.financial_report_ids:
            if wiz_fr.type == 'new':
                wiz_fr.financial_report_id.write(
                    {'account_ids': [(4, wiz_fr.account_id.id, False)]})
                log.add(_("Added account %s to financial report %s.\n") %
                        (wiz_fr.account_id.code,
                         wiz_fr.financial_report_id.name))
            elif wiz_fr.type == 'deleted':
                wiz_fr.financial_report_id.write(
                    {'account_ids': [(3, wiz_fr.account_id.id, False)]})
                log.add(_("Removed account %s from financial report %s.\n") %
                        (wiz_fr.account_id.code,
                         wiz_fr.financial_report_id.name))


class WizardUpdateChartsAccountsTaxCode(models.TransientModel):
    _name = 'wizard.update.charts.accounts.tax.code'
    _description = ("Tax code that needs to be updated (new or updated in the "
                    "template).")

    tax_code_id = fields.Many2one(
        comodel_name='account.tax.code.template', string='Tax code template',
        ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'New tax code'),
                   ('updated', 'Updated tax code'),
                   ('deleted', 'Tax code to deactivate')], string='Type')
    update_tax_code_id = fields.Many2one(
        comodel_name='account.tax.code', string='Tax code to update',
        required=False, ondelete='set null')
    notes = fields.Text('Notes')


class WizardUpdateChartsAccountsTax(models.TransientModel):
    _name = 'wizard.update.charts.accounts.tax'
    _description = ("Tax that needs to be updated (new or updated in the "
                    "template).")

    tax_id = fields.Many2one(
        comodel_name='account.tax.template', string='Tax template',
        ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template'),
                   ('deleted', 'Tax to deactivate')], string='Type')
    update_tax_id = fields.Many2one(
        comodel_name='account.tax', string='Tax to update', required=False,
        ondelete='set null')
    notes = fields.Text('Notes')


class WizardUpdateChartsAccountsAccount(models.TransientModel):
    _name = 'wizard.update.charts.accounts.account'
    _description = ("Account that needs to be updated (new or updated in the "
                    "template).")

    account_id = fields.Many2one(
        comodel_name='account.account.template', string='Account template',
        required=True, ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade'
    )
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template')], string='Type')
    update_account_id = fields.Many2one(
        comodel_name='account.account', string='Account to update',
        required=False, ondelete='set null')
    notes = fields.Text('Notes')


class WizardUpdateChartsAccountsFiscalPosition(models.TransientModel):
    _name = 'wizard.update.charts.accounts.fiscal.position'
    _description = ("Fiscal position that needs to be updated (new or updated "
                    "in the template).")

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position.template',
        string='Fiscal position template', required=True, ondelete='set null')
    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'New template'),
                   ('updated', 'Updated template')], string='Type')
    update_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position', required=False,
        string='Fiscal position to update', ondelete='set null')
    notes = fields.Text('Notes')


class WizardUpdateFinancialReport(models.TransientModel):
    _name = 'wizard.update.charts.accounts.financial.report'
    _description = ("Financial report mapping that needs to be updated "
                    "(new or updated in the template).")

    update_chart_wizard_id = fields.Many2one(
        comodel_name='wizard.update.charts.accounts',
        string='Update chart wizard', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('new', 'Add account'),
                   ('deleted', 'Remove account'),
                   ('warn', 'Warning')], string='Type')
    financial_report_id = fields.Many2one(
        comodel_name='account.financial.report', required=True,
        string='Financial report to update', ondelete='set null')
    account_id = fields.Many2one(
        comodel_name='account.account', required=False,
        string='Account to change on financial report', ondelete='set null')
    notes = fields.Text('Notes')
