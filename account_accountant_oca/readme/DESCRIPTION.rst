This module extends the functionality of Accounting Odoo module, to
add the possibility to set hidden accounting parameters.

In Odoo Community Edition,

* some accouting settings are available only in the
  Onboarding popup section. Once set, it is not possible to change the value anymore
  by the interface. (for exemple, for the Fiscal Year information.)

* Other fields like 'Overdue Payments Message' are not available.

this module fixes this limitation allowing to set the following fields:

* ``fiscalyear_last_day``
* ``fiscalyear_last_month``
* ``period_lock_date``
* ``fiscalyear_lock_date``
* ``overdue_msg``
* ``incoterm_id``
