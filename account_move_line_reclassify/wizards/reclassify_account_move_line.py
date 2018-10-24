# -*- encoding: utf-8 -*-
# Copyright 2018 FIEF Management SA <svalaeys@fiefmanage.ch>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ReclassifyAccountMoveLine(models.TransientModel):
    _name = 'reclassify.account.move.line'

    journal_id = fields.Many2one('account.journal', 'Journal',
                                 domain="[('type','=','general')]",
                                 required=True)
    line_prefix = fields.Char('Entry prefix', size=100, default="RECLASS -",
                              help="This label will be inserted "
                                   "in entries description.")
    destination_account_id = fields.Many2one('account.account',
                                             'Destination Account',
                                             help="Leave blank to use the "
                                                  "original line account")
    destination_date = fields.Date('Date On The Move To The '
                                   'Destination Account',
                                   help="Leave blank to use the original "
                                        "line date")
    use_transitory_account = fields.Boolean('Use Transitory Account')
    transitory_account_id = fields.Many2one('account.account',
                                            'Transitory Account',
                                            help="This is the account through "
                                                 "which the items will "
                                                 "transit for the duration "
                                                 "of the transit. It should be"
                                                 " a balance  sheet account.")
    transitory_date = fields.Date('Date On The Move To The Transitory Account',
                                  help="Leave blank to use original line date")
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag',
                                        'reclassify_analytic_tag_rel',
                                        'wizard_id', 'analytic_tag_id',
                                        string='Analytic Tags')
    partner_id = fields.Many2one('res.partner', 'Partner')

    def _prepare_additional_fields(self, res, line=None):
        return res

    @api.model
    def _reverse_financial_fields(self, vals):
        res = vals.copy()

        res['debit'] = vals['credit']
        res['credit'] = vals['debit']
        res['amount_currency'] = vals['amount_currency'] * -1
        return res

    @api.model
    def _get_list_of_fields_to_pop(self):
        return ['move_id', 'invoice_id', 'to_reclassify', 'blocked']

    def _get_line_values(self, line):
        vals = line.copy_data()[0]
        for x in self._get_list_of_fields_to_pop():
            vals.pop(x)
        vals['name'] = self.line_prefix + line.name
        return vals

    def _prepare_fields(self, vals):
        if self.partner_id:
            vals['partner_id'] = self.partner_id.id
        if self.analytic_account_id:
            vals['analytic_account_id'] = self.analytic_account_id.id
        if self.analytic_tag_ids:
            vals['analytic_tag_ids'] = [(6, 0,
                                         [x.id for x in self.analytic_tag_ids]
                                         )]

        self._prepare_additional_fields(vals)
        return vals

    def reclassify(self):
        """
        Reclassify the selected line items

        @return: dict to open a view filtered on generated move lines
        """
        lines_to_reclassify = self.env['account.move.line']. \
            browse(self.env.context['active_ids'])
        newly_created_line_ids = self.env['account.move.line']
        for original_line in lines_to_reclassify:
            move_name = self.line_prefix + original_line.name
            original_values = self._get_line_values(original_line)
            # We determine the first line of the move:
            # this one "cancels" out the line to reclassify.
            # It is therefore identical, save for the financial fields
            first_line_dict = self._reverse_financial_fields(original_values)
            if self.use_transitory_account:
                # The second line of the transitory move goes
                # into the transitory account.
                # We start from the values of the original line
                trans_second_line_dict = original_values.copy()
                # We change the fields specified by the user
                self._prepare_fields(trans_second_line_dict)
                # The account is the transitory account
                trans_second_line_dict['account_id'] = \
                    self.transitory_account_id.id
                # Both lines are created, we can create the move
                transitory_move_vals = \
                    {'journal_id': self.journal_id.id,
                     'date': self.transitory_date or original_line.date,
                     'ref': move_name,
                     'line_ids': [(0, 0, first_line_dict),
                                  (0, 0, trans_second_line_dict)]}
                transitory_move = self.env['account.move']. \
                    create(transitory_move_vals)
                newly_created_line_ids = transitory_move.line_ids

                # The use of the transitory account affects the
                # values of the first line of the destination move.
                # We overwrite the first_line_dic to take this into account
                first_line_dict = self. \
                    _reverse_financial_fields(trans_second_line_dict)

            # The second line of the destination
            # move goes into the destination account
            # If a transitory account was used,
            # it is allowed to go back to the original_line account
            # (pure transitory operation)
            second_line_dict = self._reverse_financial_fields(first_line_dict)
            second_line_dict['account_id'] = \
                self.destination_account_id.id or original_line.account_id.id
            destination_move_vals = \
                {'journal_id': self.journal_id.id,
                 'date': self.destination_date or
                    self.transitory_date or original_line.date,
                 'ref': move_name, 'line_ids': [(0, 0, first_line_dict),
                                                (0, 0, second_line_dict)]}
            destination_move = self.env['account.move']. \
                create(destination_move_vals)
            newly_created_line_ids = \
                newly_created_line_ids | destination_move.line_ids

            # Now we mark the original line as not to reclassify anymore
            original_line.to_reclassify = False

        if newly_created_line_ids:
            return {
                'domain': "[('id', 'in', %s)]" % newly_created_line_ids.ids,
                'name': _("Created Lines"),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'auto_search': True,
                'res_model': 'account.move.line',
                'view_id': False,
                'search_view_id': False,
                'type': 'ir.actions.act_window'}
        else:
            raise UserError(_("No accounting entry have been posted."))
