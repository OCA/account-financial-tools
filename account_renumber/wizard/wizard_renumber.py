# -*- coding: utf-8 -*-
# Copyright 2009 Pexego Sistemas Informáticos. All Rights Reserved
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class WizardRenumber(models.TransientModel):
    _name = "wizard.renumber"
    _description = "Account renumber wizard"

    journal_ids = fields.Many2many(
        'account.journal',
        'account_journal_wzd_renumber_rel',
        'wizard_id', 'journal_id',
        required=True,
        help="Journals to renumber",
        string="Journals",
    )
    period_ids = fields.Many2many(
        'account.period',
        'account_period_wzd_renumber_rel',
        'wizard_id',
        'period_id',
        required=True,
        help='Fiscal periods to renumber',
        string="Periods",
        ondelete='null',
    )
    number_next = fields.Integer(
        'First Number',
        required=True,
        help="Journal sequences will start "
             "counting on this number",
        default=1,
    )
    state = fields.Selection([
        ('init', 'Initial'),
        ('renumber', 'Renumbering')],
        readonly=True,
        default='init',
    )

    def get_sequence_id_for_fiscalyear_id(self, sequence_id, fiscalyear_id):
        """
        Based on ir_sequence.get_id from the account module.
        Allows us to get the real sequence for the given fiscal year.
        """
        sequence = self.env['ir.sequence'].browse(sequence_id)
        for line in sequence.fiscal_ids:
            if line.fiscalyear_id.id == fiscalyear_id:
                return line.sequence_id.id
        return sequence_id

    @api.multi
    def renumber(self):
        """
        Action that renumbers all the posted moves on the given
        journal and periods, and returns their ids.
        """
        self.ensure_one()
        period_ids = self.period_ids.ids
        journal_ids = self.journal_ids.ids
        number_next = self.number_next or 1
        if not (period_ids and journal_ids):
            raise ValidationError(_(
                'No Data Available \nNo records found for your selection!'))
        _logger.debug("Searching for account moves to renumber.")
        move_obj = self.env['account.move']
        sequence_obj = self.env['ir.sequence']
        sequences_seen = []
        for period in period_ids:
            move_ids = move_obj.search([
                ('journal_id', 'in', journal_ids),
                ('period_id', '=', period),
                ('state', '=', 'posted')],
                limit=0,
                order='date,id')
            if not move_ids:
                continue
            _logger.debug("Renumbering %d account moves.", len(move_ids))
            for move in move_ids:
                sequence_id = self.get_sequence_id_for_fiscalyear_id(
                    sequence_id=move.journal_id.sequence_id.id,
                    fiscalyear_id=move.period_id.fiscalyear_id.id
                )
                if sequence_id not in sequences_seen:
                    sequence_id.sudo().write({'number_next': number_next})
                    sequences_seen.append(sequence_id)
                # Generate (using our own get_id) and write the new move number
                new_name = sequence_obj.with_context(
                    fiscalyear_id=move.period_id.fiscalyear_id.id).next_by_id(
                        move.journal_id.sequence_id.id,
                )
                # Note: We can't just do a
                # "move_obj.write(cr, uid, [move.id], {'name': new_name})"
                # cause it might raise a
                # ``You can't do this modification on a confirmed entry``
                # exception.
                self.env.cr.execute(
                    'UPDATE account_move SET name=%s WHERE id=%s',
                    (new_name, move.id))
            _logger.debug("%d account moves renumbered.", len(move_ids))
        sequences_seen = []
        self.write({'state': 'renumber'})
        data_obj = self.env['ir.model.data']
        view_ref = data_obj.get_object_reference('account', 'view_move_tree')
        view_id = view_ref and view_ref[1] or False,
        res = {
            'type': 'ir.actions.act_window',
            'name': _("Renumbered account moves"),
            'res_model': 'account.move',
            'domain': ("[('journal_id','in',%s), ('period_id','in',%s), "
                       "('state','=','posted')]"
                       % (journal_ids, period_ids)),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view_id,
            'context': self.env.context,
        }
        return res
