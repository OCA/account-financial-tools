1. Go to _Accounting \> Configuration \> Chart of Accounts_ and open an account.
2. Set the **Deactivation Date**. It must be later than the date of the last posted
   journal item of the account, and the account must not be used in a tax distribution.
3. When the date is today or in the past, the account is deprecated right away. When it
   is in the future, the account is deprecated by the daily scheduled action once the
   date is reached.

To reactivate an account, clear its deactivation date.

Use the _Inactive Account_ and _Scheduled Deactivation_ filters of the chart of accounts
to list deprecated accounts and accounts with a deactivation planned in the future.

Ticking _Deprecated_ without a deactivation date keeps the standard behavior: the
account is blocked on every accounting date, and no date is stored. With a date
set, _Deprecated_ is read-only. Clear the date to reactivate the account.

Known limitation: once the account is deprecated, changing the account of an existing
journal item to it fails, even on a back-dated draft entry. Add a new journal item with
the account instead.
