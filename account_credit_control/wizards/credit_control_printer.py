# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models
from openerp.exceptions import UserError


class CreditControlPrinter(models.TransientModel):
    """ Print lines """

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = 'Mass printer'

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if context.get('active_model') != 'credit.control.line':
            return False
        return context.get('active_ids', False)

    mark_as_sent = fields.Boolean(string='Mark letter lines as sent',
                                  default=True,
                                  help="Only letter lines will be marked.")
    line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=_get_line_ids)

    @api.model
    def _credit_line_predicate(self, line):
        return True

    @api.model
    @api.returns('credit.control.line')
    def _get_lines(self, lines, predicate):
        return lines.filtered(predicate)

    @api.multi
    def print_lines(self):
        self.ensure_one()
        comm_obj = self.env['credit.control.communication']
        if not self.line_ids:
            raise UserError(_('No credit control lines selected.'))

        lines = self._get_lines(self.line_ids, self._credit_line_predicate)

        comms = comm_obj._generate_comm_from_credit_lines(lines)

        if self.mark_as_sent:
            comms._mark_credit_line_as_sent()

        report_name = 'account_credit_control.report_credit_control_summary'
        report_obj = self.env['report'].with_context(active_ids=comms.ids)
        return report_obj.get_action(comms, report_name)
