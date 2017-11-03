# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountMoveReverse(models.TransientModel):
    _name = "account.move.reverse"
    _description = "Create reversal of account moves"

    def _default_date(self):
        active_id = (self.env.context.get('active_id') or
                     self.env.context.get('active_ids', [None])[0])
        move = self.env['account.move'].browse(active_id)
        return move.date or fields.Date.today()

    def _default_journal_id(self):
        active_id = (self.env.context.get('active_id') or
                     self.env.context.get('active_ids', [None])[0])
        move = self.env['account.move'].browse(active_id)
        return move.journal_id.id

    date = fields.Date(
        string="Reversal Date", required=True, default=_default_date,
        help="Enter the date of the reversal account entries. "
             "By default, Odoo proposes the same date of the move to reverse.")
    journal_id = fields.Many2one(
        comodel_name='account.journal', string="Reversal Journal",
        default=_default_journal_id,
        help="Enter the date of the reversal account entries. "
             "If empty, Odoo uses the same journal of the move to reverse.")
    move_prefix = fields.Char(
        string="Entries Ref. Prefix",
        help="Prefix that will be added to the 'Ref' of the reversal account "
             "entries. If empty, Odoo uses the Ref of the move to reverse. "
             "(NOTE: A space is added after the prefix).")
    line_prefix = fields.Char(
        string="Items Name Prefix",
        help="Prefix that will be added to the 'Name' of the reversal account "
             "entrie items. If empty, Odoo uses the same name of the move "
             "line to reverse. (NOTE: A space is added after the prefix).")
    reconcile = fields.Boolean(
        string="Reconcile", default=True,
        help="Mark this if you want to reconcile items of both moves.")

    @api.multi
    def action_reverse(self):
        moves = self.env['account.move']
        for wizard in self:
            orig = moves.browse(self.env.context.get('active_ids'))
            moves |= orig.create_reversals(
                date=wizard.date, journal=wizard.journal_id,
                move_prefix=wizard.move_prefix, line_prefix=wizard.line_prefix,
                reconcile=wizard.reconcile)
        action = {
            'name': _('Reverse moves'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_model': 'account.move',
            'context': {'search_default_to_be_reversed': 0},
        }
        if len(moves) == 1:
            action.update({
                'view_mode': 'form,tree',
                'res_id': moves.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', moves.ids)],
            })
        return action
