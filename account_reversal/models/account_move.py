# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2011 Nicolas Bessi (Camptocamp)
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MoveAlreadyReversedValidationError(ValidationError):
    pass


class AccountMove(models.Model):
    _inherit = "account.move"

    to_be_reversed = fields.Boolean(
        copy=False,
        help="Check this box if your entry has to be reversed at the end of period.",
    )
    reversal_id = fields.Many2one(
        "account.move",
        compute="_compute_reversal_id",
        string="Reversal Entry",
        readonly=True,
    )

    @api.depends("reversal_move_id")
    def _compute_reversal_id(self):
        for move in self:
            move.reversal_id = move._get_reversal_id()

    @api.constrains("to_be_reversed", "reversal_move_id")
    def _check_to_be_reversed(self):
        for move in self:
            if move.to_be_reversed and move._get_reversal_id():
                raise MoveAlreadyReversedValidationError(
                    _(
                        "The move has already been reversed, "
                        "so you are not allowed to mark it as to be reversed."
                    )
                )

    def _get_reversal_id(self):
        # Although theoretically a o2o, reversal_move_id is technically a o2m,
        # which does not prevent having more than one record. That is why we are using
        # a slicing in order to get the first record or an empty recordset.
        self.ensure_one()
        return self.reversal_move_id.filtered(lambda m: m.state != "cancel")[:1]

    def _mark_as_reversed(self):
        self.filtered("to_be_reversed").write({"to_be_reversed": False})

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
        self._mark_as_reversed()
        return res
