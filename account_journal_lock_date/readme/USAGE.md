If the logged-in user has the **Accounting/Invoicing Administrator** role
(`account.group_account_manager`), they will not be able to create a journal entry
if the 'Lock Date' of the journal is greater than or equal to the journal entry date.

If the logged-in user does **not** have the Accounting/Invoicing Administrator role,
they will not be able to create a journal entry if the 'Lock Date for
Non-Accounting Administrators' of the journal is greater than or equal to the journal
entry date.
