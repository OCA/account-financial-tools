This module allows to create payable / receivable account from partner (in particular)
by showing the Reconcile boolean on account.account form view.
Without this, the account you would create would not be reconciliable
and therefore would create issues when invoicing (invoices would automatically be marked as paid).

This should have been part of Odoo core but was refused in https://github.com/odoo/odoo/pull/80778
