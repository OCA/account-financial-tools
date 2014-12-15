Credit Control Legal Claim
==========================

Extends the credit control with the possibility to generate lawsuit
requisitions when all levels were reached.

Overview:

* Adds **Lawsuit offices** (where the lawsuit can be filed).
* The Lawsuit offices have a **Fees Schedule**, with progressive fees
  depending on the due amount.
* Lawsuit offices are linked to one or many zip codes.
* A partner is automatically assigned to the lawsuit office in the same
  city and zip.
* When a credit control level implies a lawsuit procedure, a new
  printed document can be generated on the invoice for the lawsuit
  requisition.

Configuration
-------------

Create **Fees Schedules** in ``Invoicing > Configuration > Credit Control >
Fees Schedules``. A fees schedule defines how much fees the lawsuit
will cost depending on the amount still unpaid by the customer.

Then, create the **Lawsuit Offices** in ``Invoicing > Configuration >
Credit Control > Lawsuit Offices``. An office needs an address, a **Fees
Schedule** and one or several zip where the office is active.

Add a new level in the **Credit Control policy** in ``Invoicing >
Configuration > Credit Control > Credit Control Policies``. This level
must have the check box **Implies a Lawsuit procedure** activated.

Usage
-----

Select the invoices that needs a lawsuit requisition and use the menu
action ``More > Print Lawsuit Requisition``. The invoices that don't need
a lawsuit requisition will be filtered out of the list.
