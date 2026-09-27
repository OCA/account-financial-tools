This module automatically writes off residual balances on posted
customer invoices and vendor bills when the outstanding amount falls
below a configurable threshold.

When a small residual remains after a payment (due to rounding, currency
differences, or commercial rounding by the payer), the module creates a
journal entry that zeroes out the balance and reconciles it with the
original invoice. Destination accounts are configurable separately for
customer-side balances (income) and vendor-side balances (expense).

A scheduled action can run the process periodically. A wizard allows
on-demand execution with a preview step before any entries are
committed.

For high-volume environments, install the companion module
`account_invoice_writeoff_threshold_queue` to process write-offs as
background jobs via the OCA job queue.
