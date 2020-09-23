# Copyright 2015-2019 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from ast import literal_eval

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountMoveTemplateRun(models.TransientModel):
    _inherit = "account.move.template.run"

    overwrite = fields.Text(
        help="""
Valid dictionary to overwrite template lines:
{'L1': {'partner_id': 1, 'amount': 100, 'name': 'some label'},
 'L2': {'partner_id': 2, 'amount': 200, 'name': 'some label 2'}, }
        """
    )

    def _prepare_move_line(self, line, amount):
        # Context passed from load_lines() to write to account.move.line
        values = super()._prepare_move_line(line, amount)
        overwrite = self._context.get("overwrite", {})
        move_line_vals = overwrite.get("L{}".format(line.sequence), {})
        values.update(move_line_vals)
        # Use optional account, when amount is negative
        self._update_account_on_negative(line, values)
        return values

    def load_lines(self):
        # Verify and get overwrite dict
        overwrite_vals = self._get_overwrite_vals()
        res = super().load_lines()
        # Overwrite self.line_ids to show overwrite values
        self._overwrite_line(overwrite_vals)
        # Pass context furtner to generate_move function, only readonly field
        for key in overwrite_vals.keys():
            overwrite_vals[key].pop("amount", None)
        context = res.get("context", {}).copy()
        context.update({"overwrite": overwrite_vals})
        res["context"] = context
        return res

    def _get_valid_keys(self):
        return ["partner_id", "amount", "name", "date_maturity"]

    def _get_overwrite_vals(self):
        """ valid_dict = {
                'L1': {'partner_id': 1, 'amount': 10},
                'L2': {'partner_id': 2, 'amount': 20},
            }
        """
        self.ensure_one()
        valid_keys = self._get_valid_keys()
        overwrite_vals = self.overwrite or "{}"
        try:
            overwrite_vals = literal_eval(overwrite_vals)
            assert isinstance(overwrite_vals, dict)
        except (SyntaxError, ValueError, AssertionError):
            raise ValidationError(_("Overwrite value must be a valid python dict"))
        # First level keys must be L1, L2, ...
        keys = overwrite_vals.keys()
        if list(filter(lambda x: x[:1] != "L" or not x[1:].isdigit(), keys)):
            raise ValidationError(_("Keys must be line sequence, i..e, L1, L2, ..."))
        # Second level keys must be a valid keys
        if dict(
            filter(lambda x: set(overwrite_vals[x].keys()) - set(valid_keys), keys)
        ):
            raise ValidationError(_("Valid fields to overwrite are %s") % valid_keys)
        return overwrite_vals

    def _safe_vals(self, model, vals):
        obj = self.env[model]
        copy_vals = vals.copy()
        invalid_keys = list(
            set(list(vals.keys())) - set(list(dict(obj._fields).keys()))
        )
        for key in invalid_keys:
            copy_vals.pop(key)
        return copy_vals

    def _overwrite_line(self, overwrite_vals):
        self.ensure_one()
        for line in self.line_ids:
            vals = overwrite_vals.get("L{}".format(line.sequence), {})
            safe_vals = self._safe_vals(line._name, vals)
            line.write(safe_vals)

    def _update_account_on_negative(self, line, vals):
        if not line.opt_account_id:
            return
        for key in ["debit", "credit"]:
            if vals[key] < 0:
                ikey = (key == "debit") and "credit" or "debit"
                vals["account_id"] = line.opt_account_id.id
                vals[ikey] = abs(vals[key])
                vals[key] = 0
