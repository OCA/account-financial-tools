Lock each accounting journal independently within the boundaries of a period.

Using this module, you can implement stricter lock dates on certain journals,
such as a daily / weekly lock on sales, while having monthly periods.

You can also implement the inverse scenario, to virtually "extend" a period for
certain journals, such as pruchases. You'd postpone the period date and
implement early journal lock dates for all other journals.

By default only users with "Adviser" role are exempt from the journal lock date
check. Developers can implement more permissive exemptions from the lock date
check through a hook function on `account.journal`.

The lock date updating wizard will help you to updated journal lock dates, too.
