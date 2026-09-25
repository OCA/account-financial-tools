# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class AccountLoan(models.Model):
    _inherit = "account.loan"

    loan_type = fields.Selection(
        selection_add=[("leasing", "Leasing")],
        ondelete={"leasing": "set default"},
    )
    leased_asset_account_id = fields.Many2one(
        "account.account",
        domain="[('company_ids', '=', company_id)]",
    )
    long_term_journal_id = fields.Many2one(
        "account.journal",
        domain="[('company_id', '=', company_id),('type', '=', 'general')]",
        readonly=True,
        check_company=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Loan product",
        help="Product where the amount of the loan will be assigned when the "
        "invoice is created",
    )
    interests_product_id = fields.Many2one(
        "product.product",
        string="Interest product",
        help="Product where the amount of interests will be assigned when the "
        "invoice is created",
    )
    post_invoice = fields.Boolean(
        default=True, help="Invoices will be posted automatically"
    )

    def _check_laon_type_constrains(self):
        res = super()._check_laon_type_constrains()
        if self.loan_type == "leasing" and self.loan_amount < 0:
            raise ValidationError(
                self.env._("Leasing type must have postive amount or change the type")
            )
        return res

    def _journal_type_domain(self):
        if self.loan_type == "leasing":
            return Domain("type", "=", "purchase")
        return super()._journal_type_domain()

    @api.onchange("loan_type", "company_id")
    def _onchange_loan_type(self):
        self.residual_amount = 0.0

    def view_account_invoices(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        result["domain"] = Domain(
            [("loan_id", "=", self.id), ("move_type", "=", "in_invoice")]
        )
        return result

    @api.model
    def _generate_leasing_entries(self, date):
        res = []
        for record in self.search(
            Domain([("state", "=", "posted"), ("loan_type", "=", "leasing")])
        ):
            res += record.line_ids.filtered(
                lambda r: r.date <= date and not r.move_ids
            )._generate_invoice()
        return res

    @api.model
    def _loan_and_borrow_domain(self):
        return Domain("loan_type", "!=", "leasing")
