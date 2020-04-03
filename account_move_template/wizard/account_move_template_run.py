# Copyright 2015-2019 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountMoveTemplateRun(models.TransientModel):
    _name = "account.move.template.run"
    _description = "Wizard to generate move from template"

    template_id = fields.Many2one('account.move.template', required=True)
    company_id = fields.Many2one(
        'res.company', required=True, readonly=True,
        default=lambda self: self.env['res.company']._company_default_get())
    partner_id = fields.Many2one(
        'res.partner', 'Override Partner',
        domain=['|', ('parent_id', '=', False), ('is_company', '=', True)])
    date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one(
        'account.journal', string='Journal', readonly=True)
    ref = fields.Char(string='Reference')
    line_ids = fields.One2many(
        'account.move.template.line.run', 'wizard_id', string="Lines")
    state = fields.Selection([
        ('select_template', 'Select Template'),
        ('set_lines', 'Set Lines'),
        ], readonly=True, default='select_template')

    def _prepare_wizard_line(self, tmpl_line):
        vals = {
            'wizard_id': self.id,
            'sequence': tmpl_line.sequence,
            'name': tmpl_line.name,
            'amount': 0.0,
            'account_id': tmpl_line.account_id.id,
            'partner_id': tmpl_line.partner_id.id or False,
            'move_line_type': tmpl_line.move_line_type,
            'tax_ids': [(6, 0, tmpl_line.tax_ids.ids)],
            'tax_line_id': tmpl_line.tax_line_id.id,
            'analytic_account_id': tmpl_line.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, tmpl_line.analytic_tag_ids.ids)],
            'note': tmpl_line.note,
            'payment_term_id': tmpl_line.payment_term_id.id or False,
            }
        return vals

    # STEP 1
    def load_lines(self):
        self.ensure_one()
        amtlro = self.env['account.move.template.line.run']
        if self.company_id != self.template_id.company_id:
            raise UserError(_(
                "The selected template (%s) is not in the same company (%s) "
                "as the current user (%s).") % (
                    self.template_id.name,
                    self.template_id.company_id.display_name,
                    self.company_id.display_name))
        tmpl_lines = self.template_id.line_ids
        for tmpl_line in tmpl_lines.filtered(lambda l: l.type == 'input'):
            vals = self._prepare_wizard_line(tmpl_line)
            amtlro.create(vals)
        self.write({
            'journal_id': self.template_id.journal_id.id,
            'ref': self.template_id.ref,
            'state': 'set_lines',
            })
        if not self.line_ids:
            return self.generate_move()
        action = self.env.ref(
            'account_move_template.account_move_template_run_action')
        result = action.read()[0]
        result.update({
            'res_id': self.id,
            'context': self.env.context,
            })
        return result

    # STEP 2
    def generate_move(self):
        self.ensure_one()
        sequence2amount = {}
        for wizard_line in self.line_ids:
            sequence2amount[wizard_line.sequence] = wizard_line.amount
        prec = self.company_id.currency_id.rounding
        self.template_id.compute_lines(sequence2amount)
        if all([
                float_is_zero(x, precision_rounding=prec)
                for x in sequence2amount.values()]):
            raise UserError(_("Debit and credit of all lines are null."))
        move_vals = self._prepare_move()
        for line in self.template_id.line_ids:
            amount = sequence2amount[line.sequence]
            if not float_is_zero(amount, precision_rounding=prec):
                move_vals['line_ids'].append(
                    (0, 0, self._prepare_move_line(line, amount)))
        move = self.env['account.move'].create(move_vals)
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result.update({
            'name': _('Entry from template %s') % self.template_id.name,
            'res_id': move.id,
            'views': False,
            'view_id': False,
            'view_mode': 'form,tree,kanban',
            'context': self.env.context,
            })
        return result

    def _prepare_move(self):
        move_vals = {
            'ref': self.ref,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
            'line_ids': [],
        }
        return move_vals

    def _prepare_move_line(self, line, amount):
        date_maturity = False
        if line.payment_term_id:
            pterm_list = line.payment_term_id.compute(
                value=1, date_ref=self.date)[0]
            date_maturity = max(l[0] for l in pterm_list)
        debit = line.move_line_type == 'dr'
        values = {
            'name': line.name,
            'analytic_account_id': line.analytic_account_id.id,
            'account_id': line.account_id.id,
            'credit': not debit and amount or 0.0,
            'debit': debit and amount or 0.0,
            'partner_id': self.partner_id.id or line.partner_id.id,
            'tax_line_id': line.tax_line_id.id,
            'date_maturity': date_maturity or self.date,
        }
        if line.analytic_tag_ids:
            values['analytic_tag_ids'] = [(6, 0, line.analytic_tag_ids.ids)]
        if line.tax_ids:
            values['tax_ids'] = [(6, 0, line.tax_ids.ids)]
        return values


class AccountMoveTemplateLineRun(models.TransientModel):
    _name = "account.move.template.line.run"
    _description = 'Wizard Lines to generate move from template'

    wizard_id = fields.Many2one(
        'account.move.template.run', ondelete='cascade')
    company_id = fields.Many2one(
        related='wizard_id.company_id')
    company_currency_id = fields.Many2one(
        related='wizard_id.company_id.currency_id', string='Company Currency')
    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', readonly=True)
    account_id = fields.Many2one(
        'account.account', required=True, readonly=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', readonly=True)
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    tax_line_id = fields.Many2one(
        'account.tax', string='Originator Tax',
        ondelete='restrict', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', readonly=True, string='Partner')
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', readonly=True)
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')],
        required=True, readonly=True, string='Direction')
    amount = fields.Monetary(
        'Amount', required=True, currency_field='company_currency_id')
    note = fields.Char(readonly=True)
