# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2011 Nicolas Bessi (Camptocamp)
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    to_be_reversed = fields.Boolean(
        copy=False,
        help="Check this box if your entry has to be reversed at the end " "of period.",
    )

    def _mark_as_reversed(self):
        self.filtered("to_be_reversed").write({"to_be_reversed": False})

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
        self._mark_as_reversed()
        return res
