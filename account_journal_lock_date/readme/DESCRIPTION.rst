Lock each accounting journal independently.

In addition to the lock dates provided by standard Odoo and
account_permanent_lock_move, provide a per journal lock date.

Note: this module depends on account_permanent_lock_move because it
implements stricter checks than standard Odoo, such as verifying that
one cannot create draft moves before the lock date.

Note: the journal lock date is ignored for users that are part of
the Adviser group. This rule can be adapted by overriding method
`_can_bypass_journal_lock_date` of `account.journal`.
