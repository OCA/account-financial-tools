# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def import_lines(self):
        self.ensure_one()
        module = __name__.split('addons.')[1].split('.')[0]
        view = self.env.ref('%s.aml_import_view_form' % module)
        return {
            'name': _('Import File'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'aml.import',
            'view_id': view.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
