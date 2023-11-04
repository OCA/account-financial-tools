# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from setuptools.config._validate_pyproject import ValidationError

from odoo import _, api, fields, models


class MoveAlreadyReversedValidationError(ValidationError):
    pass


class AccountMove(models.Model):

    _inherit = "account.move"

    to_be_reversed = fields.Boolean(copy=False)
    reversal_id = fields.Many2one(
        "account.move",
        compute="_compute_reversal_id",
        string="Reversal Entry",
        readonly=True,
    )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super()._reverse_moves(default_values_list, cancel)
        self.to_be_reversed = False
        return res

    @api.depends("reversal_move_id")
    def _compute_reversal_id(self):
        for move in self:
            move.reversal_id = move._get_reversal_id()

    @api.constrains("to_be_reversed", "reversal_move_id")
    def check_to_be_reversed(self):
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
