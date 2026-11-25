When the modification reason is required, saving changes on an existing
account, from its form or from the chart of accounts list (including
multi-edition), opens a pop-up asking for the reason of the modification. The modification is only saved once a reason is selected.

The reason is logged in the chatter of the account with the tracked
changes.

For developers: the reason is given to `write()` through the
`modification_reason_id` value. No reason is required on the creation of
an account and for technical updates: writes done as superuser
(`sudo()`), when loading module data or a chart of accounts, or with the
`skip_account_modification_reason` context key.
