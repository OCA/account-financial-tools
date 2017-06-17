# -*- coding: utf-8 -*-
# Copyright (C) 2016 Steigend IT Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"

    parent_id = fields.Many2one(
        'account.account.template', 'Parent Account', ondelete="set null")
    property_temp_related_account_id = fields.Many2one(
        'account.account', 'Related Account', company_dependent=True,)

    def update_template_property_field(self, account_id, company):
        PropertyObj = self.env['ir.property']
        value = account_id and 'account.account,' + str(account_id) or False
        if value:
            field = self.env['ir.model.fields'].search(
                [('name', '=', 'property_temp_related_account_id'),
                 ('model', '=', "account.account.template"),
                 ('relation', '=', 'account.account')], limit=1)
            vals = {
                'name': 'property_temp_related_account_id',
                'company_id': company.id,
                'fields_id': field.id,
                'value': value,
                'res_id': 'account.account.template,' + str(self.id)
            }
            properties = PropertyObj.search(
                [('res_id', '=', self.id),
                 ('name', '=', 'property_temp_related_account_id'),
                 ('company_id', '=', company.id)])
            if properties:
                # the property exist: modify it
                properties.write(vals)
            else:
                # create the property
                PropertyObj.create(vals)
        return True


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.multi
    def generate_account(self, tax_template_ref, acc_template_ref, code_digits,
                         company):
        account_tmpl_pool = self.env['account.account.template']
        account_pool = self.env['account.account']
        account_template_account_dict = super(
            AccountChartTemplate, self).generate_account(
                tax_template_ref, acc_template_ref, code_digits, company)
        account_template_objs = account_tmpl_pool.browse(
            account_template_account_dict.keys())
        for account_template_obj in account_template_objs:
            account_template_obj.update_template_property_field(
                account_template_account_dict[account_template_obj.id],
                company)
            if not account_template_obj.parent_id:
                continue
            account_parent_id = account_template_account_dict.get(
                account_template_obj.parent_id.id, False)
            account_obj = account_pool.browse(
                account_template_account_dict[account_template_obj.id])
            account_obj.write({'parent_id': account_parent_id})
        return account_template_account_dict

    @api.multi
    def update_generated_account(self, tax_template_ref=[], code_digits=1,
                                 company=False, importing_parent=False):
        """ This method for generating parent accounts from templates.

            :param tax_template_ref: Taxes templates reference for write
                taxes_id in account_account.
            :param code_digits: number of digits got
                from wizard.multi.charts.accounts,
                this is use for account code.
            :param company_id: company_id selected
                from wizard.multi.charts.accounts.
            :returns: return acc_template_ref for reference purpose.
            :rtype: dict
        """

        account_tmpl_obj = self.env['account.account.template']
        account_obj = self.env['account.account']
        view_liquidity_type = self.env.ref(
            'account_parent.data_account_type_view')
        if not importing_parent:
            return True
        self.ensure_one()
        if not company:
            company = self.env.user.company_id
        acc_template = account_tmpl_obj.search(
            [('nocreate', '!=', True),
             ('chart_template_id', '=', self.id), ], order='id')
        code_account_dict = {}

        for account_template in acc_template:
            tax_ids = []
            for tax in account_template.tax_ids:
                tax_ids.append(tax_template_ref[tax.id])

            code_main = account_template.code and len(
                account_template.code) or 0
            code_acc = account_template.code or ''
            if code_main > 0 and code_main <= code_digits:
                code_acc = str(code_acc) + \
                    (str('0' * (code_digits - code_main)))
            if account_template.user_type_id.id == view_liquidity_type.id:
                new_code = account_template.code
            else:
                new_code = code_acc
            new_account = account_obj.with_context(
                {'show_parent_account': True}).search(
                    [('code', '=', new_code),
                     ('company_id', '=', company.id)], limit=1)
            if not new_account:
                currency_id = account_template.currency_id and \
                    account_template.currency_id.id or False
                user_type_id = account_template.user_type_id and \
                    account_template.user_type_id.id or False
                vals = {
                    'name': account_template.name,
                    'currency_id': currency_id,
                    'code': new_code,
                    'user_type_id': user_type_id,
                    'reconcile': account_template.reconcile,
                    'note': account_template.note,
                    'tax_ids': [(6, 0, tax_ids)],
                    'company_id': company.id,
                    'tag_ids': [(6, 0, [tuple(account_template.tag_ids)])],
                }
                new_account = account_obj.create(vals)
            account_template.update_template_property_field(
                new_account.id, company)
            if new_code not in code_account_dict:
                code_account_dict[new_code] = new_account
        if company.bank_account_code_prefix:
            if code_account_dict.get(company.bank_account_code_prefix, False):
                parent_account_id = code_account_dict.get(
                    company.bank_account_code_prefix, False)
            else:
                parent_account_id = account_obj.with_context(
                    {'show_parent_account': True}).search(
                        [('code', '=', company.bank_account_code_prefix),
                         ('company_id', '=', company.id)], limit=1)
            account = account_obj.search(
                [('code', 'like', "%s%%" % company.bank_account_code_prefix),
                 ('id', '!=', parent_account_id.id),
                 ('company_id', '=', company.id)])
            if account:
                account.write({
                    'parent_id': parent_account_id.id
                })
        if company.cash_account_code_prefix:
            if code_account_dict.get(company.cash_account_code_prefix, False):
                parent_account_id = code_account_dict.get(
                    company.cash_account_code_prefix, False)
            else:
                parent_account_id = account_obj.with_context(
                    {'show_parent_account': True}).search(
                        [('code', '=', company.cash_account_code_prefix),
                         ('company_id', '=', company.id)], limit=1)

            account = account_obj.search(
                [('code', 'like', "%s%%" % company.cash_account_code_prefix),
                 ('id', '!=', parent_account_id.id),
                 ('company_id', '=', company.id)])
            if account:
                account.write({
                    'parent_id': parent_account_id.id
                })

        all_acc_templates = acc_template.with_context(
            {'company_id': company.id})
        for account_template in all_acc_templates:
            if not account_template.parent_id:
                continue
            parent_id = account_template.parent_id and \
                account_template.parent_id.property_temp_related_account_id.id
            account_template.property_temp_related_account_id.write({
                'parent_id': parent_id
            })
        return True
