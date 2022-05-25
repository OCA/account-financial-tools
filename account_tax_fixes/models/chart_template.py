# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api, fields, _, SUPERUSER_ID
from odoo.addons.account.models.chart_template import AccountChartTemplate as accountcharttemplate
from odoo.addons.account.models.chart_template import WizardMultiChartsAccounts as wizardMultichartsaccounts

import logging

from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


def noupdate_existing_xmlid(cr, model, module, name):
    env = api.Environment(cr, SUPERUSER_ID, {})
    xml_records = env['ir.model.data'].search([('model', '=', model), ('name', '=', name), ('module', '=', module)])
    if xml_records:
        cr.execute("update ir_model_data set noupdate = null where id in %s", [tuple(xml_records.ids)])


class WizardMultiChartsAccounts(models.TransientModel):

    @api.multi
    def execute_update(self):
        self = self.with_context(lang=self.company_id.partner_id.lang)
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can change the settings"))
        company = self.company_id
        tmp1, tmp2 = self.chart_template_id._update_template(company)
        return {}

    @api.multi
    def execute(self):
        '''
        This function is called at the confirmation of the wizard to generate the COA from the templates. It will read
        all the provided information to create the accounts, the banks, the journals, the taxes, the
        accounting properties... accordingly for the chosen company.
        '''
        # Ensure everything is translated consitingly to the company's language, not the user's one.
        self = self.with_context(lang=self.company_id.partner_id.lang)
        if not self.env.user._is_admin():
            raise AccessError(_("Only administrators can change the settings"))

        existing_accounts = self.env['account.account'].search([('company_id', '=', self.company_id.id)])
        if existing_accounts:
            # we tolerate switching from accounting package (localization module) as long as there isn't yet any accounting
            # entries created for the company.
            if self.existing_accounting(self.company_id):
                raise UserError(
                    _('Could not install new chart of account as there are already accounting entries existing'))

            # delete accounting properties
            prop_values = ['account.account,%s' % (account_id,) for account_id in existing_accounts.ids]
            existing_journals = self.env['account.journal'].search([('company_id', '=', self.company_id.id)])
            if existing_journals:
                prop_values.extend(['account.journal,%s' % (journal_id,) for journal_id in existing_journals.ids])
            accounting_props = self.env['ir.property'].search([('value_reference', 'in', prop_values)])
            if accounting_props:
                accounting_props.unlink()

            # delete account, journal, tax, fiscal position and reconciliation model
            models_to_delete = ['account.reconcile.model', 'account.fiscal.position', 'account.tax', 'account.move',
                                'account.journal']
            for model in models_to_delete:
                res = self.env[model].search([('company_id', '=', self.company_id.id)])
                if len(res):
                    res.unlink()
            existing_accounts.unlink()

        company = self.company_id
        self.company_id.write({'currency_id': self.currency_id.id,
                               'accounts_code_digits': self.code_digits,
                               'anglo_saxon_accounting': self.use_anglo_saxon,
                               'bank_account_code_prefix': self.bank_account_code_prefix,
                               'cash_account_code_prefix': self.cash_account_code_prefix,
                               'chart_template_id': self.chart_template_id.id})

        # set the coa currency to active
        self.currency_id.write({'active': True})

        # When we install the CoA of first company, set the currency to price types and pricelists
        if company.id == 1:
            for reference in ['product.list_price', 'product.standard_price', 'product.list0']:
                try:
                    tmp2 = self.env.ref(reference).write({'currency_id': self.currency_id.id})
                except ValueError:
                    pass

        # If the floats for sale/purchase rates have been filled, create templates from them
        self._create_tax_templates_from_rates(company.id)

        # Install all the templates objects and generate the real objects
        acc_template_ref, taxes_ref, tag_ref = self.chart_template_id. \
            _install_template(company, code_digits=self.code_digits, transfer_account_id=self.transfer_account_id)

        # write values of default taxes for product as super user and write in the config
        IrDefault = self.env['ir.default']
        if self.sale_tax_id and taxes_ref:
            IrDefault.sudo().set('product.template', "taxes_id", [taxes_ref[self.sale_tax_id.id]],
                                 company_id=company.id)
        if self.purchase_tax_id and taxes_ref:
            IrDefault.sudo().set('product.template', "supplier_taxes_id", [taxes_ref[self.purchase_tax_id.id]],
                                 company_id=company.id)

        # Create Bank journals
        self._create_bank_journals_from_o2m(company, acc_template_ref)

        # Create the current year earning account if it wasn't present in the CoA
        company.get_unaffected_earnings_account()
        return {}


wizardMultichartsaccounts.execute = WizardMultiChartsAccounts.execute


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    tag_template_ids = fields.One2many('account.account.tag.template', 'chart_template_id', string='Tag Template List',
                                       help='List of all the tags that have to be installed by the wizard')

    @api.multi
    def create_record_with_xmlid(self, company, template, model, vals):
        # Create a record for the given model with the given vals and
        # also create an entry in ir_model_data to have an xmlid for the newly created record
        # xmlid is the concatenation of company_id and template_xml_id
        ir_model_data = self.env['ir.model.data']
        template_xmlid = ir_model_data.search([('model', '=', template._name), ('res_id', '=', template.id)])
        new_xml_id = str(company.id) + '_' + template_xmlid.name
        check_for_old_id = self.env.ref("%s.%s" % (template_xmlid.module, new_xml_id), raise_if_not_found=False)
        if check_for_old_id:
            noupdate_existing_xmlid(check_for_old_id.model, check_for_old_id.module, check_for_old_id.name)
            return check_for_old_id
        return ir_model_data._update(model, template_xmlid.module, vals, xml_id=new_xml_id, store=True, noupdate=True,
                                     mode='init', res_id=False)

    @api.multi
    def _install_template(self, company, code_digits=None, transfer_account_id=None, obj_wizard=None, acc_ref=None,
                          taxes_ref=None, tags_ref=None):
        """ Recursively load the template objects and create the real objects from them.
            :param company: company the wizard is running for
            :param code_digits: number of digits the accounts code should have in the COA
            :param transfer_account_id: reference to the account template that will be used as intermediary account for transfers between 2 liquidity accounts
            :param obj_wizard: the current wizard for generating the COA from the templates
            :param acc_ref: Mapping between ids of account templates and real accounts created from them
            :param taxes_ref: Mapping between ids of tax templates and real taxes created from them
            :returns: tuple with a dictionary containing
                * the mapping between the account template ids and the ids of the real accounts that have been generated
                  from them, as first item,
                * a similar dictionary for mapping the tax templates and taxes, as second item,
            :rtype: tuple(dict, dict, dict)
        """
        self.ensure_one()
        if acc_ref is None:
            acc_ref = {}
        if taxes_ref is None:
            taxes_ref = {}
        if tags_ref is None:
            tags_ref = {}
        if self.parent_id:
            tmp1, tmp2, tmp3 = self.parent_id._install_template(company, code_digits=code_digits,
                                                                transfer_account_id=transfer_account_id,
                                                                acc_ref=acc_ref,
                                                                taxes_ref=taxes_ref,
                                                                tags_ref=tags_ref)
            acc_ref.update(tmp1)
            taxes_ref.update(tmp2)
            tags_ref.update(tmp3)
        # Ensure, even if individually, that everything is translated according to the company's language.
        tmp1, tmp2, tmp3 = self.with_context(lang=company.partner_id.lang)._load_template(company,
                                                                                          code_digits=code_digits,
                                                                                          transfer_account_id=transfer_account_id,
                                                                                          account_ref=acc_ref,
                                                                                          taxes_ref=taxes_ref,
                                                                                          tags_ref=tags_ref)
        acc_ref.update(tmp1)
        taxes_ref.update(tmp2)
        tags_ref.update(tmp3)
        return acc_ref, taxes_ref, tags_ref

    @api.multi
    def _load_template(self, company, code_digits=None, transfer_account_id=None, account_ref=None, taxes_ref=None,
                       tags_ref=None):
        """ Generate all the objects from the templates
            :param company: company the wizard is running for
            :param code_digits: number of digits the accounts code should have in the COA
            :param transfer_account_id: reference to the account template that will be used as intermediary account for transfers between 2 liquidity accounts
            :param acc_ref: Mapping between ids of account templates and real accounts created from them
            :param taxes_ref: Mapping between ids of tax templates and real taxes created from them
            :returns: tuple with a dictionary containing
                * the mapping between the account template ids and the ids of the real accounts that have been generated
                  from them, as first item,
                * a similar dictionary for mapping the tax templates and taxes, as second item,
            :rtype: tuple(dict, dict, dict)
        """
        self.ensure_one()
        if account_ref is None:
            account_ref = {}
        if taxes_ref is None:
            taxes_ref = {}
        if tags_ref is None:
            tags_ref = {}
        if not code_digits:
            code_digits = self.code_digits
        if not transfer_account_id:
            transfer_account_id = self.transfer_account_id
        AccountTaxObj = self.env['account.tax']

        # Generate taxes from templates.
        generated_tax_res = self.with_context(active_test=False).tax_template_ids._generate_tax(company)
        taxes_ref.update(generated_tax_res['tax_template_to_tax'])

        # Generate tags from templates.
        generated_tag_res = self.with_context(active_test=False).tag_template_ids._generate_tag(company)
        tags_ref.update(generated_tag_res['tag_template_to_tag'])

        # Generating Accounts from templates.
        account_template_ref = self.generate_account(taxes_ref, account_ref, code_digits, company)
        account_ref.update(account_template_ref)

        # writing account values after creation of accounts
        company.transfer_account_id = account_template_ref[transfer_account_id.id]
        for key, value in generated_tax_res['account_dict'].items():
            if value['refund_account_id'] or value['account_id'] or value['cash_basis_account']:
                AccountTaxObj.browse(key).write({
                    'refund_account_id': account_ref.get(value['refund_account_id'], False),
                    'account_id': account_ref.get(value['account_id'], False),
                    'cash_basis_account': account_ref.get(value['cash_basis_account'], False),
                })

        # Create Journals - Only done for root chart template
        if not self.parent_id:
            self.generate_journals(account_ref, company)

        # generate properties function
        self.generate_properties(account_ref, company)

        # Generate Fiscal Position , Fiscal Position Accounts and Fiscal Position Taxes from templates
        self.generate_fiscal_position(taxes_ref, account_ref, company)

        # Generate account operation template templates
        self.generate_account_reconcile_model(taxes_ref, account_ref, company)

        return account_ref, taxes_ref, tags_ref

    @api.multi
    def _update_template(self, company, taxes_ref=None, tags_ref=None):
        self.ensure_one()
        if taxes_ref is None:
            taxes_ref = {}
        if tags_ref is None:
            tags_ref = {}
        # Generate taxes from templates.
        generated_tax_res = self.with_context(active_test=False).tax_template_ids._generate_tax(company)
        taxes_ref.update(generated_tax_res['tax_template_to_tax'])

        # Generate tags from templates.
        generated_tag_res = self.with_context(active_test=False).tag_template_ids._generate_tag(company)
        tags_ref.update(generated_tag_res['tag_template_to_tag'])
        return taxes_ref, tags_ref


accountcharttemplate._load_template = AccountChartTemplate._load_template
accountcharttemplate._install_template = AccountChartTemplate._install_template
accountcharttemplate.create_record_with_xmlid = AccountChartTemplate.create_record_with_xmlid


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    def _get_tax_credit_payable(self):
        return [('taxcredit', 'Tax credit receivable from the taxpayer'),
                ('taxpay', 'Tax payable by the taxpayer'),
                ('eutaxcredit', 'Tax credit receivable from the taxpayer on EU deals'),
                ('eutaxpay', 'Tax payable by the taxpayer on EU deals'),
                ('taxadvpay', 'Tax payable by the taxpayer when Imports from outside EU'),
                ('taxbalance', 'Account for balance of taxes'),
                ('othertax', 'Different by VAT Tax payable by the taxpayer')]

    tax_credit_payable = fields.Selection(selection='_get_tax_credit_payable',
                                          string='Who pays tax', required=True, default='taxpay',
                                          help="If not applicable (computed through a Python code), the tax won't "
                                               "appear on the invoice.Who pays the tax purchaser or seller ( for "
                                               "imports from outside the EU pay the buyer )")

    def _get_tax_vals(self, company, tax_template_to_tax):
        val = super(AccountTaxTemplate, self)._get_tax_vals(company, tax_template_to_tax)
        val.update(dict(tax_credit_payable=self.tax_credit_payable, ))
        return val


class AccountAccountTagTemplate(models.Model):
    _name = 'account.account.tag.template'
    _description = 'Account Tag Template'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    def _get_type_taxes(self):
        return [
            ('0', _('Tax base')),
            ('2', _('Tax base (debit)')),
            ('3', _('Tax base (credit)')),
            ('1', _('Coupled tax')),
            ('98', _('Boot Tax base and tax EU deals')),
            ('99', _('Boot Tax base and tax')),
        ]

    def _get_type_info(self):
        return [
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
        ]

    name = fields.Char(required=True)
    code = fields.Char("Code", index=True, copy=False)
    applicability = fields.Selection([('accounts', 'Accounts'), ('taxes', 'Taxes')], required=True, default='accounts')
    color = fields.Integer('Color Index', default=10)
    active = fields.Boolean(default=True, help="Set active to false to hide the Account Tag without removing it.")
    chart_template_id = fields.Many2one('account.chart.template', string='Chart Template', required=True)
    account_ids = fields.Many2many('account.account', 'account_account_account_tag', string='Accounts',
                                   help="Assigned accounts for custom reporting")
    tax_ids = fields.Many2many('account.tax', 'account_tax_account_tag', string='Taxes',
                               help="Assigned taxes for custom reporting")
    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', index=True, ondelete='cascade')
    child_ids = fields.One2many('account.account.tag', 'parent_id', string='Child Tags')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    type_taxes = fields.Selection(selection='_get_type_taxes', string='Type taxes')
    type_info = fields.Selection(selection='_get_type_info', string='Type info')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'Tag names must be unique by company!'),
    ]

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        res = []
        for record in self:
            code = "%s" % record.code and "[%s]" % record.code or ""
            name = "%s%s" % (code, record.name)
            res.append((record.id, name))
        return res

    def _get_tag_vals(self, company, tag_template_to_tag):
        """ This method generates a dictionary of all the values for the tag that will be created.
        """
        self.ensure_one()
        tax_ids = self.env['account.tax']
        account_ids = self.env['account.account']
        ir_model_data = self.env['ir.model.data'].sudo()
        xid = ir_model_data.search([('model', '=', 'account.chart.template'),
                                    ('res_id', '=', self.chart_template_id.id)])
        res = xid.read(['module', 'name'])[0]
        for tax_id in self.tax_ids:
            base_tax_ids = ir_model_data.search([('module', '=', res['module']),
                                                 ('model', '=', 'account.tax.template'),
                                                 ('res_id', '=', tax_id.id)])
            base_tax_id = base_tax_ids.read(['name'])[0]
            ref = "%s.%s_%s" % (res['module'], self.company_id.id, base_tax_id['name'])
            tax_ids |= self.env.ref(ref, raise_if_not_found=False)
        for account_id in self.account_ids:
            base_account_id = ir_model_data.search([('module', '=', res['module']),
                                                    ('model', '=', 'account.account'),
                                                    ('res_id', '=', account_id.id)])
            ref = "%s.%s_%s" % (res['module'], self.company_id.id, base_account_id['name'])
            account_ids |= self.env.ref(ref, raise_if_not_found=False)
        val = {
            'name': self.name,
            'active': self.active,
            'company_id': company.id,
            'applicability': self.applicability,
            'color': self.color,
            'code': self.code,
            'tax_ids': [(6, False, tax_ids.ids)],
            'account_ids': [(6, False, account_ids.ids)]
        }
        return val

    @api.multi
    def _generate_tag(self, company):
        """ This method generate taxes from templates.
            :param company: the company for which the taxes should be created from templates in self
            :returns: {
                'tax_template_to_tax': mapping between tax template and the newly generated taxes corresponding,
                'account_dict': dictionary containing a to-do list with all the accounts to assign on new taxes
            }
        """
        tag_template_to_tag = {}
        for tag in self:
            vals_tag = tag._get_tag_vals(company, tag_template_to_tag)
            new_tag = self.env['account.chart.template'].create_record_with_xmlid(company, tag, 'account.account.tag',
                                                                                  vals_tag)
            tag_template_to_tag[tag.id] = new_tag

        return {
            'tax_template_to_tax': tag_template_to_tag,
        }
