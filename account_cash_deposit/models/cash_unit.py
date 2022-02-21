# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_amount


class CashUnit(models.Model):
    _name = "cash.unit"
    _description = "Cash Unit"
    _order = "currency_id, tree_order desc"
    _rec_name = "value"

    currency_id = fields.Many2one("res.currency", ondelete="cascade")
    active = fields.Boolean(default=True)
    tree_order = fields.Float(compute="_compute_all", store=True)
    cash_type = fields.Selection(
        [
            ("note", "Note"),
            ("coin", "Coin"),
            ("coinroll", "Coin Roll"),
        ],
        string="Type",
        required=True,
        help="This field should never be modified.",
    )
    coinroll_qty = fields.Integer(
        string="Coin Quantity", help="This field should never be modified."
    )
    value = fields.Monetary(
        required=True,
        help="This field should never be modified. For a coin roll, "
        "you must enter the value of the coin.",
    )
    total_value = fields.Monetary(compute="_compute_all", store=True)
    auto_create = fields.Selection(
        [
            ("deposit", "Deposit"),
            ("order", "Order"),
            ("both", "Both"),
        ],
        help="If set, a line for this cash unit will be created by default "
        "on a new cash deposit or a new cash order or both.",
    )

    _sql_constraints = [
        (
            "coinroll_qty_positive",
            "CHECK(coinroll_qty >= 0)",
            "The coin quantity must be positive.",
        ),
        ("value_positive", "CHECK(value > 0)", "The value must be strictly positive."),
    ]

    @api.constrains("cash_type", "coinroll_qty")
    def _check_cash_unit(self):
        for rec in self:
            if rec.cash_type == "coinroll" and rec.coinroll_qty <= 0:
                raise ValidationError(
                    _("For a coin roll, the coin quantity must be strictly positive.")
                )

    @api.depends("coinroll_qty", "cash_type", "value")
    def _compute_all(self):
        # I want bank notes first, then coinrolls, then coins
        # This is a hack, but it is designed to work fine with
        # all currencies of the planet !
        type2multiplier = {
            "note": 1000000,
            "coinroll": 1000,
            "coin": 1,
        }
        for rec in self:
            qty = rec.cash_type == "coinroll" and rec.coinroll_qty or 1
            total_value = rec.value * qty
            rec.tree_order = type2multiplier.get(rec.cash_type, 0) * total_value
            rec.total_value = total_value

    def _get_value_label(self, value):
        self.ensure_one()
        symbol_position = self.currency_id.position
        symbol = self.currency_id.symbol
        int_value = int(round(value))
        # if value is an integer
        if self.currency_id.compare_amounts(value, int_value) == 0:
            amount_label = str(int_value)
            if symbol_position == "before":
                value_label = "%s %s" % (symbol, amount_label)
            else:
                value_label = "%s %s" % (amount_label, symbol)
        else:
            value_label = format_amount(self.env, value, self.currency_id)
        return value_label

    def name_get(self):
        res = []
        type2label = dict(
            self.fields_get("cash_type", "selection")["cash_type"]["selection"]
        )
        for rec in self:
            cash_type_label = type2label.get(rec.cash_type)
            value_label = rec._get_value_label(rec.value)
            if rec.cash_type == "coinroll":
                total_value_label = rec._get_value_label(rec.total_value)
                label = "%s %s x %d (%s)" % (
                    cash_type_label,
                    value_label,
                    rec.coinroll_qty,
                    total_value_label,
                )
            else:
                label = "%s %s" % (cash_type_label, value_label)
            res.append((rec.id, label))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if name and operator == "ilike":
            if name.isdigit():
                recs = self.search([("value", "=", name)] + args, limit=limit)
                if recs:
                    return recs.name_get()
            value = False
            try:
                value = float(name)
            except Exception:
                pass
            if value:
                recs = self.search([("value", "=", value)] + args, limit=limit)
                if recs:
                    return recs.name_get()
            lang = self.env["res.lang"]._lang_get(self.env.user.lang)
            if lang:
                decimal_sep = lang.decimal_point
                if decimal_sep and decimal_sep != ".":
                    try:
                        value = float(name.replace(decimal_sep, ".", 1))
                    except Exception:
                        pass
                    if value:
                        recs = self.search([("value", "=", value)] + args, limit=limit)
                        if recs:
                            return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
