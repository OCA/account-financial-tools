By Odoo standard, when an account document is cancelled, its journal entry will be deleted completely.
This module enhance the process, instead of deletion, it will create new reversed journal entry.
This will help preserved the accounting history, which is strictly required by some country.

Following are documented provide this feature,

- Invoice (account.invoice)
- Payment (acccont.payment)
- Bank Statement (account.bank.statement.line)
