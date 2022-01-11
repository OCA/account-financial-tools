By Odoo standard, when an account document is cancelled, its journal entry will be deleted completely.
This module enhance the process, instead of deletion, it will create new reversed journal entry.
This will help preserved the accounting history, which is strictly required by some country.

Following are documented provide this feature,

- Invoice (account.invoice)
- Payment (acccont.payment)
- Bank Statement (account.bank.statement.line)

Remarks on changes when compare to version 12
=============================================

Odoo 13 has removed account.invoice, as such Invoice is no longer a front-end document
which generate account.move as a back-end document when validated.

Invoice is now account.move itself and force following changes,

- Canceled invoice (account.move) will create reversed account.move of type 'entry' to itself
- Canceled invoice (account.move) status is 'posted', with the new flag 'cancel_reversal = True'
- As result, cancel a posted invoice with reversal (state=posted) is now different from cancel from draft (state=canceled)
- When invoice or payment is reversed canceled, it will not allowed set to draft, in practice it will be frozen.
- The reversed canceled document (both invoice, payment, statement line) will still keep the relation with its journal entries
