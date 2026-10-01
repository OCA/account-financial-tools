If the logged-in user has the access group 'Adviser', he/she will not be
able to create or modify a journal entry dated on or after the 'Lock To
Date' of its journal.

If the logged-in user does not have the access group 'Adviser', he/she
will not be able to create or modify a journal entry dated on or after
the earliest of the 'Lock To Date' and the 'Lock To Date for
Non-Advisers' of its journal.

The check can be bypassed programmatically with the
`bypass_journal_lock_to_date` context key.
