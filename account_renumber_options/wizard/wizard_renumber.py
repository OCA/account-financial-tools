# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - Avanzosc S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, exceptions, api, _
import logging

_logger = logging.getLogger(__name__)


class WizardRenumber(models.TransientModel):

    _inherit = 'wizard.renumber'

    @api.multi
    def get_sequence_for_fiscalyear_id(self, sequence, fiscalyear_id):
        lines = sequence.mapped('fiscal_ids').filtered(
            lambda x: x.fiscalyear_id.id == fiscalyear_id)
        return lines and lines[:1].sequence_id or sequence

    @api.multi
    def renumber_without_period(self):
        number_next = self.number_next or 1
        if not (self.period_ids and self.journal_ids):
            raise exceptions.Warning(_('No Data Available.'
                                       'No records found for your selection!'))
        _logger.debug('Searching for account moves to renumber.')
        move_obj = self.env['account.move']
        sequences_seen = self.env['ir.sequence']
        move_ids = move_obj.search([('journal_id', 'in', self.journal_ids.ids),
                                    ('period_id', 'in', self.period_ids.ids),
                                    ('state', '=', 'posted')], order='date,id')
        _logger.debug('Renumbering %d account moves.', len(move_ids))
        for move in move_ids:
            fiscalyear = move.period_id.fiscalyear_id.id
            sequence = self.get_sequence_for_fiscalyear_id(
                sequence=move.journal_id.sequence_id, fiscalyear_id=fiscalyear)
            if sequence not in sequences_seen:
                sequence.sudo().write({'number_next': number_next})
                sequences_seen |= sequence
            new_name = sequence.with_context(fiscalyear_id=fiscalyear
                                             ).next_by_id(sequence.id)
            self.env.cr.execute("UPDATE account_move SET name=%s WHERE id=%s;",
                                (new_name, move.id))
        move_ids.invalidate_cache()
        _logger.debug('%d account moves renumbered.', len(move_ids))
        self.state = 'renumber'
        res = {
            'type': 'ir.actions.act_window',
            'name': _('Renumbered account moves'),
            'res_model': 'account.move',
            'domain': ("[('journal_id','in',%s), ('period_id','in',%s), "
                       "('state','=','posted')]"
                       % (self.journal_ids.ids, self.period_ids.ids)),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('account.view_move_tree').id,
            'context': self.env.context,
            'target': 'current',
        }
        return res

    @api.multi
    def renumber(self):
        if not self.env['ir.config_parameter'].search(
                [('key', '=', 'renumber_by_period')]):
            return self.renumber_without_period()
        else:
            return super(WizardRenumber, self).renumber()
