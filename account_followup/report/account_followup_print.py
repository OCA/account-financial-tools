# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from collections import defaultdict
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.report import report_sxw


class ReportRappel(report_sxw.rml_parse):
    _name = "account_followup.report.rappel"

    @api.model_cr
    def init(self):
        super(ReportRappel, self).init()
        self.localcontext.update({
            'time': time,
            'ids_to_objects': self._ids_to_objects,
            'getLines': self._lines_get,
            'get_text': self._get_text
        })

    def _ids_to_objects(self, ids):
        all_lines = []
        for line in self.env['account_followup.stat.by.partner'].browse(ids):
            if line not in all_lines:
                all_lines.append(line)
        return all_lines

    def _lines_get(self, stat_by_partner_line):
        return self._lines_get_with_partner(stat_by_partner_line.partner_id,
                                            stat_by_partner_line.company_id.id)

    def _lines_get_with_partner(self, partner, company_id):
        moveline_obj = self.env['account.move.line']
        moveline_ids = moveline_obj.search([
            ('partner_id', '=', partner.id),
            ('account_id.internal_type', '=', 'receivable'),
            ('reconciled', '=', False),
            ('company_id', '=', company_id),
            '|', ('date_maturity', '=', False),
            ('date_maturity', '<=', fields.Date.today()),
        ])

        # lines_per_currency = {currency: [line data, ...], ...}
        lines_per_currency = defaultdict(list)
        for line in moveline_obj.browse(moveline_ids):
            currency = line.currency_id or line.company_id.currency_id
            line_data = {
                'name': line.move_id.name,
                'ref': line.ref,
                'date': line.date,
                'date_maturity': line.date_maturity,
                'balance':
                    line.amount_currency
                    if currency != line.company_id.currency_id
                    else line.debit - line.credit,
                'blocked': line.blocked,
                'currency_id': currency,
            }
            lines_per_currency[currency].append(line_data)

        return [
            {'line': lines, 'currency': currency} for currency, lines
            in lines_per_currency.items()]

    def _get_text(self, stat_line, followup_id, context=None):
        context = dict(context or {}, )
        fp_obj = self.env['account_followup.followup']
        fp_line = fp_obj.with_context(lang=stat_line.partner_id.lang).\
            browse(followup_id).followup_line
        if not fp_line:
            raise ValidationError(
                _("The followup plan defined for the current company does "
                  "not have any followup action.")
            )
        # the default text will be the first fp_line in the sequence with
        # a description.
        default_text = ''
        li_delay = []
        for line in fp_line:
            if not default_text and line.description:
                default_text = line.description
            li_delay.append(line.delay)
        li_delay.sort(reverse=True)
        # look into the lines of the partner that already have a followup
        # level, and take the description of the higher level for which it is
        # available
        partner_line_ids = self.env['account.move.line'].search([
            ('partner_id', '=', stat_line.partner_id.id),
            ('reconciled', '=', False),
            ('company_id', '=', stat_line.company_id.id),
            ('blocked', '=', False),
            ('debit', '!=', False),
            ('account_id.internal_type', '=', 'receivable'),
            ('followup_line_id', '!=', False)
        ])
        partner_max_delay = 0
        partner_max_text = ''
        for i in self.env['account.move.line'].browse(partner_line_ids):
            if i.followup_line_id.delay > partner_max_delay and \
                    i.followup_line_id.description:
                partner_max_delay = i.followup_line_id.delay
                partner_max_text = i.followup_line_id.description
        text = partner_max_delay and partner_max_text or default_text
        if text:
            lang_obj = self.env['res.lang']
            lang_ids = lang_obj.search([
                ('code', '=', stat_line.partner_id.lang)
            ])
            date_format = lang_ids and lang_obj.browse(
                lang_ids[0]).date_format or '%Y-%m-%d'
            text %= {
                'partner_name': stat_line.partner_id.name,
                'date': time.strftime(date_format),
                'company_name': stat_line.company_id.name,
                'user_signature': self.env.user.signature or '',
            }
        return text


class ReportFollowup(models.AbstractModel):
    _name = 'report.account_followup.report_followup'
    _inherit = 'report.abstract_report'
    _template = 'account_followup.report_followup'
    _wrapped_report_class = ReportRappel
