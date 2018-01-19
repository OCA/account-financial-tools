# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreditControlEmailer(models.TransientModel):
    """ Send emails for each selected credit control lines. """

    _name = "credit.control.emailer"
    _description = """Mass credit line emailer"""
    _rec_name = 'id'

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if not (context.get('active_model') == 'credit.control.line' and
                context.get('active_ids')):
            return False
        line_obj = self.env['credit.control.line']
        lines = line_obj.browse(context['active_ids'])
        return self._filter_lines(lines)

    line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=lambda self: self._get_line_ids(),
                                domain=[('state', '=', 'to_be_sent'),
                                        ('channel', '=', 'email')])

    @api.model
    @api.returns('credit.control.line')
    def _filter_lines(self, lines):
        """ filter lines to use in the wizard """
        line_obj = self.env['credit.control.line']
        domain = [('state', '=', 'to_be_sent'),
                  ('id', 'in', lines.ids),
                  ('channel', '=', 'email')]
        return line_obj.search(domain)

    @api.multi
    def email_lines(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('No credit control lines selected.'))

        comm_obj = self.env['credit.control.communication']

        filtered_lines = self._filter_lines(self.line_ids)
        comms = comm_obj._generate_comm_from_credit_lines(filtered_lines)
        comms._generate_emails()
        return {'type': 'ir.actions.act_window_close'}
