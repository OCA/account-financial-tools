In the Accounting module of Odoo, when you want to close a period or a fiscal year, you update the *Lock Dates* to the last day of the period or fiscal year that you want to close.

By default, you can write any value on the *Lock Date* fields. As a consequence, it is always possible to re-open any period or fiscal year by setting the Lock Dates backwards.

With this module, the *Lock Date for All Users* (technical field name: *fiscalyear_lock_date*) cannot be updated backwards, it can only be updated forward. For example, if the *Lock Date for All Users* has been set to December 31st 2020, it cannot be set back to December 31st 2019. The *Lock Date for Non-Advisers* (technical field name: *period_lock_date*) can still be set backwards.
