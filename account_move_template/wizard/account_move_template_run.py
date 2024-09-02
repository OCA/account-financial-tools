# Copyright 2015-2019 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from ast import literal_eval

from odoo import Command, _, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMoveTemplateRun(models.TransientModel):
    _name = "account.move.template.run"
    _description = "Wizard to generate move from template"
    _check_company_auto = True

    template_id = fields.Many2one(
        "account.move.template",
        required=True,
        check_company=True,
        domain="[('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Override Partner",
        domain=["|", ("parent_id", "=", False), ("is_company", "=", True)],
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    ref = fields.Char(string="Reference")
    line_ids = fields.One2many(
        "account.move.template.line.run", "wizard_id", string="Lines"
    )
    state = fields.Selection(
        [("select_template", "Select Template"), ("set_lines", "Set Lines")],
        readonly=True,
        default="select_template",
    )
    overwrite = fields.Text(
        help="""
Valid dictionary to overwrite template lines:
{'L1': {'partner_id': 1, 'amount': 100, 'name': 'some label'},
 'L2': {'partner_id': 2, 'amount': 200, 'name': 'some label 2'}, }
        """
    )

    def _prepare_wizard_line(self, tmpl_line):
        vals = {
            "wizard_id": self.id,
            "sequence": tmpl_line.sequence,
            "name": tmpl_line.name,
            "amount": 0.0,
            "account_id": tmpl_line.account_id.id,
            "partner_id": tmpl_line.partner_id.id or False,
            "move_line_type": tmpl_line.move_line_type,
            "tax_line_id": tmpl_line.tax_line_id.id,
            "tax_ids": [Command.set(tmpl_line.tax_ids.ids)],
            "analytic_distribution": tmpl_line.analytic_distribution,
            "note": tmpl_line.note,
            "payment_term_id": tmpl_line.payment_term_id.id or False,
            "is_refund": tmpl_line.is_refund,
            "tax_repartition_line_id": tmpl_line.tax_repartition_line_id.id or False,
        }
        return vals

    # STEP 1
    def load_lines(self):
        self.ensure_one()
        # Verify and get overwrite dict
        overwrite_vals = self._get_overwrite_vals()
        amtlro = self.env["account.move.template.line.run"]
        tmpl_lines = self.template_id.line_ids
        for tmpl_line in tmpl_lines.filtered(lambda line: line.type == "input"):
            vals = self._prepare_wizard_line(tmpl_line)
            amtlro.create(vals)
        self.write(
            {
                "journal_id": self.template_id.journal_id.id,
                "ref": self.template_id.ref,
                "state": "set_lines",
            }
        )
        if not self.line_ids:
            return self.generate_move()
        result = self.env["ir.actions.actions"]._for_xml_id(
            "account_move_template.account_move_template_run_action"
        )
        result.update({"res_id": self.id, "context": self.env.context})

        # Overwrite self.line_ids to show overwrite values
        self._overwrite_line(overwrite_vals)
        # Pass context furtner to generate_move function, only readonly field
        for key in overwrite_vals.keys():
            overwrite_vals[key].pop("amount", None)
        result["context"] = dict(result.get("context", {}), overwrite=overwrite_vals)
        return result

    def _get_valid_keys(self):
        return ["partner_id", "amount", "name", "date_maturity"]

    def _get_overwrite_vals(self):
        """valid_dict = {
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
        except (SyntaxError, ValueError, AssertionError) as err:
            raise ValidationError(
                _("Overwrite value must be a valid python dict")
            ) from err
        # First level keys must be L1, L2, ...
        keys = overwrite_vals.keys()
        if list(filter(lambda x: x[:1] != "L" or not x[1:].isdigit(), keys)):
            raise ValidationError(_("Keys must be line sequence i.e. L1, L2, ..."))
        # Second level keys must be a valid keys
        try:
            if dict(
                filter(lambda x: set(overwrite_vals[x].keys()) - set(valid_keys), keys)
            ):
                raise ValidationError(
                    _("Valid fields to overwrite are %s") % valid_keys
                )
        except ValidationError as e:
            raise e
        except Exception as e:
            msg = """
    valid_dict = {
        'L1': {'partner_id': 1, 'amount': 10},
        'L2': {'partner_id': 2, 'amount': 20},
    }
            """
            raise ValidationError(
                _(
                    "Invalid dictionary: %(exception)s\n%(msg)s",
                    exception=e,
                    msg=msg,
                )
            ) from e
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
            vals = overwrite_vals.get(f"L{line.sequence}", {})
            safe_vals = self._safe_vals(line._name, vals)
            line.write(safe_vals)

    # STEP 2
    def generate_move(self):
        self.ensure_one()
        sequence2amount = {}
        for wizard_line in self.line_ids:
            sequence2amount[wizard_line.sequence] = wizard_line.amount
        company_cur = self.company_id.currency_id
        self.template_id.compute_lines(sequence2amount)
        if all([company_cur.is_zero(x) for x in sequence2amount.values()]):
            raise UserError(_("Debit and credit of all lines are null."))
        move_vals = self._prepare_move()
        for line in self.template_id.line_ids:
            amount = sequence2amount[line.sequence]
            if not company_cur.is_zero(amount):
                move_vals["line_ids"].append(
                    Command.create(self._prepare_move_line(line, amount))
                )
        move = self.env["account.move"].create(move_vals)
        result = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_journal_line"
        )
        result.update(
            {
                "name": _("Entry from template %s") % self.template_id.name,
                "res_id": move.id,
                "views": False,
                "view_id": False,
                "view_mode": "form,tree,kanban",
                "context": self.env.context,
            }
        )
        return result

    def _prepare_move(self):
        move_vals = {
            "ref": self.ref,
            "journal_id": self.journal_id.id,
            "date": self.date,
            "company_id": self.company_id.id,
            "line_ids": [],
        }
        return move_vals

    def _prepare_move_line(self, line, amount):
        date_maturity = False
        if line.payment_term_id:
            date_maturity = max(
                [
                    line._get_due_date(self.date)
                    for line in line.payment_term_id.line_ids
                ]
            )
        debit = line.move_line_type == "dr"
        values = {
            "name": line.name,
            "account_id": line.account_id.id,
            "credit": not debit and amount or 0.0,
            "debit": debit and amount or 0.0,
            "partner_id": self.partner_id.id or line.partner_id.id,
            "date_maturity": date_maturity or self.date,
            "tax_repartition_line_id": line.tax_repartition_line_id.id or False,
            "analytic_distribution": line.analytic_distribution,
        }
        if line.tax_ids:
            values["tax_ids"] = [Command.set(line.tax_ids.ids)]
            document_type = "refund" if line.is_refund else "invoice"
            atrl_ids = self.env["account.tax.repartition.line"].search(
                [
                    ("tax_id", "in", line.tax_ids.ids),
                    ("document_type", "=", document_type),
                    ("repartition_type", "=", "base"),
                ]
            )
            values["tax_tag_ids"] = [Command.set(atrl_ids.mapped("tag_ids").ids)]
        if line.tax_repartition_line_id:
            values["tax_tag_ids"] = [
                Command.set(line.tax_repartition_line_id.tag_ids.ids)
            ]
        # With overwrite options
        overwrite = self._context.get("overwrite", {})
        move_line_vals = overwrite.get(f"L{line.sequence}", {})
        values.update(move_line_vals)
        # Use optional account, when amount is negative
        self._update_account_on_negative(line, values)
        return values

    def _update_account_on_negative(self, line, vals):
        if not line.opt_account_id:
            return
        for key in ["debit", "credit"]:
            if vals[key] < 0:
                ikey = (key == "debit") and "credit" or "debit"
                vals["account_id"] = line.opt_account_id.id
                vals[ikey] = abs(vals[key])
                vals[key] = 0


class AccountMoveTemplateLineRun(models.TransientModel):
    _name = "account.move.template.line.run"
    _description = "Wizard Lines to generate move from template"
    _inherit = "analytic.mixin"

    wizard_id = fields.Many2one("account.move.template.run", ondelete="cascade")
    company_id = fields.Many2one(related="wizard_id.company_id")
    company_currency_id = fields.Many2one(
        related="wizard_id.company_id.currency_id", string="Company Currency"
    )
    sequence = fields.Integer(required=True)
    name = fields.Char(readonly=True)
    account_id = fields.Many2one("account.account", required=True, readonly=True)
    tax_ids = fields.Many2many("account.tax", string="Taxes", readonly=True)
    tax_line_id = fields.Many2one(
        "account.tax", string="Originator Tax", ondelete="restrict", readonly=True
    )
    partner_id = fields.Many2one("res.partner", readonly=True, string="Partner")
    payment_term_id = fields.Many2one(
        "account.payment.term", string="Payment Terms", readonly=True
    )
    move_line_type = fields.Selection(
        [("cr", "Credit"), ("dr", "Debit")],
        required=True,
        readonly=True,
        string="Direction",
    )
    amount = fields.Monetary(required=True, currency_field="company_currency_id")
    note = fields.Char(readonly=True)
    is_refund = fields.Boolean(string="Is a refund?", readonly=True)
    tax_repartition_line_id = fields.Many2one(
        "account.tax.repartition.line",
        string="Tax Repartition Line",
        readonly=True,
    )
