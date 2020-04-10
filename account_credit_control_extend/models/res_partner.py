# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _opened_invoice_total(self):
        account_invoice_report = self.env['account.invoice.report']
        if not self.ids:
            self.total_opened_invoice = 0.0
            return True

        user_currency_id = self.env.user.company_id.currency_id.id
        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self:
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        # searching account.invoice.report via the orm is comparatively expensive
        # (generates queries "id in []" forcing to build the full table).
        # In simple cases where all invoices are in the same currency than the user's company
        # access directly these elements

        # generate where clause to include multicompany rules
        where_query = account_invoice_report._where_calc([
            ('partner_id', 'in', all_partner_ids), ('state', '=', 'open'),
            ('type', 'in', ('out_invoice', 'out_refund'))
        ])
        account_invoice_report._apply_ir_rules(where_query, 'read')
        from_clause, where_clause, where_clause_params = where_query.get_sql()

        # price_total is in the company currency
        query = """
                  SELECT SUM(price_total) as total, partner_id
                    FROM account_invoice_report account_invoice_report
                   WHERE %s
                   GROUP BY partner_id
                """ % where_clause
        self.env.cr.execute(query, where_clause_params)
        price_totals = self.env.cr.dictfetchall()
        for partner, child_ids in all_partners_and_children.items():
            partner.total_opened_invoice = sum(price['total'] for price in price_totals if price['partner_id'] in child_ids)

    total_opened_invoice = fields.Monetary(compute='_opened_invoice_total', string="Total Opened Invoices", groups='account.group_account_invoice')
    credit_due = fields.Float(string="Credit Due", compute="_compute_credit_due")
    credit_left = fields.Float(string="Credit Left", compute="_compute_credit_due")

    @api.multi
    def _compute_credit_due(self):
        for record in self:
            #_logger.info("Due %s:%s" % (record.credit_control_line_ids, record.parent_id))
            record.credit_due = sum([x.balance_due for x in self.env["credit.control.line"].search([('partner_id', '=', record.parent_id and record.parent_id.id or record.id)])])
