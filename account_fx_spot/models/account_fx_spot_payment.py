# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountFxSpotPayment(models.TransientModel):
    _name = "account.fx.spot.payment"
    _inherit = 'account.abstract.payment'
    _description = "Register payments on FX Spot Transactions"

    @api.multi
    def default_type(self):
        active_ids = self._context.get('active_ids')
        if not active_ids:
            return
        transactions = self.env['account.fx.spot'].browse(active_ids)
        if not any(t.in_currency_id != transactions[0].in_currency_id for
                   t in transactions):
            return 'inbound'
        elif not any(t.out_currency_id != transactions[0].out_currency_id for
                     t in transactions):
            return "outbound"
        return

    fx_spot_ids = fields.Many2many(
        comodel_name="account.fx.spot",
        string="Foreign Exchange Spot Transaction",
        copy=False,
    )
    multi = fields.Boolean(
        string='Multi',
        help='Technical field indicating if the user selected transactions '
             'from multiple partners or from different types.',
    )
    payment_type = fields.Selection(default=default_type)

    @api.onchange("payment_type")
    def onchange_payment_type(self):
        active_ids = self._context.get('active_ids')
        transactions = self.env['account.fx.spot'].browse(active_ids)
        for rec in self:
            if rec.payment_type == "outbound":
                rec.partner_type = "supplier"
                rec.amount = self._compute_payment_amount_out(transactions)
                rec.currency_id = transactions[0].out_currency_id
            else:
                rec.partner_type = "customer"
                rec.amount = self._compute_payment_amount_in(transactions)
                rec.currency_id = transactions[0].in_currency_id

    @api.model
    def _compute_payment_amount_out(self, transactions):
        payment_currency = transactions[0].out_currency_id
        total = 0
        for t in transactions:
            if t.out_currency_id == payment_currency:
                total += t.residual_out
        return total

    @api.model
    def _compute_payment_amount_in(self, transactions):
        payment_currency = transactions[0].in_currency_id
        total = 0
        for t in transactions:
            if t.in_currency_id == payment_currency:
                total += t.residual_in
        return total

    @api.constrains("payment_type", "currency_id")
    def _check_currencies(self, transactions=False):
        transactions = transactions or self.fx_spot_ids
        if (
            any(t.in_currency_id != transactions[0].in_currency_id for
                t in transactions) and
            any(t.out_currency_id != transactions[0].out_currency_id for
                t in transactions)
        ):
            raise UserError(
                _("In order to pay multiple transactions at once, they must "
                  "use the same outgoing or incoming currency.")
            )
        if self.currency_id:
            currency = self.currency_id
            if (self.payment_type == "inbound" and
                    any(currency != t.in_currency_id for t in transactions)):
                raise UserError(
                    _("Incoming Currencies does not match."))
            if (self.payment_type == "outbound" and
                    any(currency != t.out_currency_id for t in transactions)):
                raise UserError(
                    _("Outgoing Currencies does not match."))

    @api.model
    def default_get(self, fields):
        rec = super(AccountFxSpotPayment, self).default_get(fields)
        active_ids = self._context.get('active_ids')

        # Check for selected transactions ids
        if not active_ids:
            raise UserError(
                _("Programming error: wizard action executed without "
                  "active_ids in context.")
            )
        transactions = self.env['account.fx.spot'].browse(active_ids)

        # Check all transactions are open
        if any(t.state != 'open' for t in transactions):
            raise UserError(
                _("You can only register payments for open transactions")
            )

        # Check all transactions have the same currency in or out.
        self._check_currencies(transactions)
        update_dict = dict()
        if rec.get("payment_type") == "inbound":
            update_dict["partner_type"] = "customer"
            update_dict["currency_id"] = transactions[0].in_currency_id.id
            if not rec.get("amount"):
                update_dict["amount"] = self._compute_payment_amount_in(
                    transactions)
        elif rec.get("payment_type") == "outbound":
            update_dict["partner_type"] = "supplier"
            update_dict["currency_id"] = transactions[0].out_currency_id.id
            if not rec.get("amount"):
                update_dict["amount"] = self._compute_payment_amount_out(
                    transactions)

        # Look if we are mixin multiple commercial_partner
        multi = any(t.partner_id.commercial_partner_id !=
                    transactions[0].partner_id.commercial_partner_id for
                    t in transactions)
        update_dict["multi"] = multi
        update_dict["fx_spot_ids"] = [(6, 0, transactions.ids)]
        update_dict["communication"] = ' '.join(
            [ref for ref in transactions.mapped('name') if ref])
        update_dict["partner_id"] = False if multi else \
            transactions[0].partner_id.commercial_partner_id.id

        rec.update(update_dict)
        return rec

    @api.multi
    def _groupby_transactions(self):
        """Split the transactions linked to the wizard according to their
        commercial partner.
        :return: a dictionary mapping commercial_partner_id and
        transactions recordset.
        """
        res = {}
        for rec in self.fx_spot_ids:
            key = rec.partner_id.commercial_partner_id.id
            if key not in res:
                res[key] = self.env['account.fx.spot']
            res[key] += rec
        return res

    @api.multi
    def _prepare_payment_vals(self, transactions):
        """Create the payment values.
        :param transactions: The transactions that should have the same
        commercial partner.
        :return: The payment values as a dictionary.
        """
        if self.multi:
            if self.payment_type == 'inbound':
                amount = self._compute_payment_amount_in(transactions)
            elif self.payment_type == 'outbound':
                amount = self._compute_payment_amount_out(transactions)
            else:
                raise UserError(_(
                    "Payment Type is not set."
                ))
        else:
            amount = self.amount
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'fx_spot_ids': [(6, 0, transactions.ids)],
            'payment_type': self.payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': transactions[0].partner_id.commercial_partner_id.id,
            'partner_type': self.partner_type,
        }

    @api.multi
    def get_payments_vals(self):
        """Compute the values for payments.
        :return: a list of payment values (dictionary).
        """
        if self.multi:
            groups = self._groupby_transactions()
            return [self._prepare_payment_vals(transactions) for
                    transactions in groups.values()]
        return [self._prepare_payment_vals(self.fx_spot_ids)]

    @api.multi
    def create_payments(self):
        """Create payments according to the transactions.
        Having transactions with different commercial_partner_id leads
        to multiple payments.
        In case of all the transactions are related to the same
        commercial_partner_id, only one payment will be created.
        :return: The ir.actions.act_window to show created payments.
        """
        payment_obj = self.env['account.payment']
        payments = payment_obj
        for payment_vals in self.get_payments_vals():
            payments += payment_obj.create(payment_vals)
        payments.post()
        return {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
