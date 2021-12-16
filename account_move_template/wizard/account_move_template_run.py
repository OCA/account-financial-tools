# Copyright 2015-2019 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from ast import literal_eval

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMoveTemplateRun(models.TransientModel):
    _name = "account.move.template.run"
    _description = "Wizard to generate move from template"

    template_id = fields.Many2one("account.move.template", required=True)
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
            "tax_ids": [(6, 0, tmpl_line.tax_ids.ids)],
            "analytic_account_id": tmpl_line.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, tmpl_line.analytic_tag_ids.ids)],
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
        if self.company_id != self.template_id.company_id:
            raise UserError(
                _(
                    "The selected template (%s) is not in the same company (%s) "
                    "as the current user (%s)."
                )
                % (
                    self.template_id.name,
                    self.template_id.company_id.display_name,
                    self.company_id.display_name,
                )
            )
        tmpl_lines = self.template_id.line_ids
        for tmpl_line in tmpl_lines.filtered(lambda l: l.type == "input"):
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
        action = self.env.ref("account_move_template.account_move_template_run_action")
        result = action.sudo().read()[0]
        result.update({"res_id": self.id, "context": self.env.context})

        # Overwrite self.line_ids to show overwrite values
        self._overwrite_line(overwrite_vals)
        # Pass context furtner to generate_move function, only readonly field
        for key in overwrite_vals.keys():
            overwrite_vals[key].pop("amount", None)
        context = result.get("context", {}).copy()
        context.update({"overwrite": overwrite_vals})
        result["context"] = context
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
        except (SyntaxError, ValueError, AssertionError):
            raise ValidationError(_("Overwrite value must be a valid python dict"))
        # First level keys must be L1, L2, ...
        keys = overwrite_vals.keys()
        if list(filter(lambda x: x[:1] != "L" or not x[1:].isdigit(), keys)):
            raise ValidationError(_("Keys must be line sequence, i..e, L1, L2, ..."))
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
            raise ValidationError(_("Invalid dictionary: {}\n{}".format(e, msg)))
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
                    (0, 0, self._prepare_move_line(line, amount))
                )
        move = self.env["account.move"].create(move_vals)
        action = self.env.ref("account.action_move_journal_line")
        result = action.sudo().read()[0]
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
            pterm_list = line.payment_term_id.compute(value=1, date_ref=self.date)
            date_maturity = max(line[0] for line in pterm_list)
        debit = line.move_line_type == "dr"
        values = {
            "name": line.name,
            "analytic_account_id": line.analytic_account_id.id,
            "account_id": line.account_id.id,
            "credit": not debit and amount or 0.0,
            "debit": debit and amount or 0.0,
            "partner_id": self.partner_id.id or line.partner_id.id,
            "date_maturity": date_maturity or self.date,
            "tax_repartition_line_id": line.tax_repartition_line_id.id or False,
        }
        if line.analytic_tag_ids:
            values["analytic_tag_ids"] = [(6, 0, line.analytic_tag_ids.ids)]
        if line.tax_ids:
            values["tax_ids"] = [(6, 0, line.tax_ids.ids)]
            tax_repartition = "refund_tax_id" if line.is_refund else "invoice_tax_id"
            atrl_ids = self.env["account.tax.repartition.line"].search(
                [
                    (tax_repartition, "in", line.tax_ids.ids),
                    ("repartition_type", "=", "base"),
                ]
            )
            values["tag_ids"] = [(6, 0, atrl_ids.mapped("tag_ids").ids)]
        if line.tax_repartition_line_id:
            values["tag_ids"] = [(6, 0, line.tax_repartition_line_id.tag_ids.ids)]
        # With overwrite options
        overwrite = self._context.get("overwrite", {})
        move_line_vals = overwrite.get("L{}".format(line.sequence), {})
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

    wizard_id = fields.Many2one("account.move.template.run", ondelete="cascade")
    company_id = fields.Many2one(related="wizard_id.company_id")
    company_currency_id = fields.Many2one(
        related="wizard_id.company_id.currency_id", string="Company Currency"
    )
    sequence = fields.Integer("Sequence", required=True)
    name = fields.Char("Name", readonly=True)
    account_id = fields.Many2one("account.account", required=True, readonly=True)
    analytic_account_id = fields.Many2one("account.analytic.account", readonly=True)
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag", string="Analytic Tags", readonly=True
    )
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
    amount = fields.Monetary(
        "Amount", required=True, currency_field="company_currency_id"
    )
    note = fields.Char(readonly=True)
    is_refund = fields.Boolean(string="Is a refund?", readonly=True)
    tax_repartition_line_id = fields.Many2one(
        "account.tax.repartition.line",
        string="Tax Repartition Line",
        readonly=True,
    )
