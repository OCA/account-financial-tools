# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _


class WizardSelectMoveTemplate(models.TransientModel):
    _name = "wizard.select.move.template"

    template_id = fields.Many2one('account.move.template', required=True)
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many(
        'wizard.select.move.template.line', 'template_id')
    state = fields.Selection(
        [('template_selected', 'Template selected')])

    @api.onchange('template_id', 'company_id')
    def onchange_company_id(self):
        template_domain = [('company_id', '=', self.company_id.id)]
        return {'domain': {'template_id': template_domain}}

    @api.multi
    def load_lines(self):
        self.ensure_one()
        lines = self.template_id.template_line_ids
        for line in lines.filtered(lambda l: l.type == 'input'):
            self.env['wizard.select.move.template.line'].create({
                'template_id': self.id,
                'sequence': line.sequence,
                'name': line.name,
                'amount': 0.0,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id or self.partner_id.id,
                'move_line_type': line.move_line_type,
            })
        if not self.line_ids:
            return self.load_template()
        self.state = 'template_selected'
        view_rec = self.env.ref('account_move_template.wizard_select_template')
        action = self.env.ref(
            'account_move_template.action_wizard_select_template_by_move')
        result = action.read()[0]
        result['res_id'] = self.id
        result['view_id'] = [view_rec.id]
        result['context'] = self.env.context
        return result

    @api.multi
    def load_template(self):
        self.ensure_one()
        input_lines = {}
        for template_line in self.line_ids:
            input_lines[template_line.sequence] = template_line.amount
        amounts = self.template_id.compute_lines(input_lines)
        name = self.template_id.name
        partner = self.partner_id.id
        moves = self.env['account.move']
        for journal in self.template_id.template_line_ids.mapped('journal_id'):
            lines = []
            move = self._create_move(name, journal.id)
            moves = moves + move
            for line in self.template_id.template_line_ids.filtered(
                    lambda l, j=journal: l.journal_id == j):
                lines.append((0, 0,
                              self._prepare_line(line, amounts, partner)))
            move.write({'line_ids': lines})
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['domain'] = [('id', 'in', moves.ids)],
        result['name'] = _('Entries from template: %s') % name
        result['context'] = self.env.context
        return result

    @api.model
    def _create_move(self, ref, journal_id):
        return self.env['account.move'].create({
            'ref': ref,
            'journal_id': journal_id,
        })

    @api.model
    def _prepare_line(self, line, amounts, partner_id):
        debit = line.move_line_type == 'dr'
        values = {
            'name': line.name,
            'journal_id': line.journal_id.id,
            'analytic_account_id': line.analytic_account_id.id,
            'account_id': line.account_id.id,
            'date': fields.Date.today(),
            'credit': not debit and amounts[line.sequence] or 0.0,
            'debit': debit and amounts[line.sequence] or 0.0,
            'partner_id': line.partner_id.id or partner_id,
        }
        return values


class WizardSelectMoveTemplateLine(models.TransientModel):
    _description = 'Template Lines'
    _name = "wizard.select.move.template.line"

    template_id = fields.Many2one(
        'wizard.select.move.template')
    company_id = fields.Many2one('res.company',
                                 related='template_id.company_id',
                                 readonly=True)
    sequence = fields.Integer(required=True)
    name = fields.Char(required=True, readonly=True)
    account_id = fields.Many2one(
        'account.account', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True,
                                 string='Partner')
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')], required=True, readonly=True)
    amount = fields.Float(required=True)
