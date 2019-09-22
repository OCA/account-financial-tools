This module helps ensuring the chronology of invoice numbers.

It prevents the validation of invoices when:

* there are draft invoices with a prior date
* there are validated invoices with a later date
* invoice have a date (which generates account move) prior of date_invoice
