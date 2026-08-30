This module adds a switch on journal entries to disable automatic tax
recomputation.

In standard behavior, Odoo synchronizes dynamic tax lines each time a
journal entry or its lines are edited. That is generally correct for
invoices, but it can be problematic in specific accounting flows where
tax amounts must remain manually controlled.

Typical use case: payroll journal entries. When payroll-related entries
are adjusted manually, automatic tax recomputation can overwrite
intended withholding amounts or tax lines. With this module, you can
freeze tax synchronization for a specific journal entry and keep your
manual values unchanged.

The feature is intentionally limited to journal entries
(`move_type = 'entry'`).
