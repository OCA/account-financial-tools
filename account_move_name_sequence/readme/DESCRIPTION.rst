In Odoo version 13.0 and previous versions, the number of journal entries was generated from a sequence configured on the journal.

In Odoo version 14.0, the number of journal entries can be manually set by the user. Then, the number attributed for the next journal entries in the same journal is computed by a complex piece of code that guesses the format of the journal entry number from the number of the journal entry which was manually entered by the user. It has several drawbacks:

* the available options for the sequence are limited,
* it is not possible to configure the sequence in advance before the deployment in production,
* as it is error-prone, they added a *Resequence* wizard to re-generate the journal entry numbers, which can be considered as illegal in many countries,
* the `piece of code <https://github.com/odoo/odoo/blob/14.0/addons/account/models/sequence_mixin.py>`_ that handles this is not easy to understand and quite difficult to debug.

Odoo>=v14.0 raises new concurrency issues since it locks the last journal entry of the journal to get the new number causing a bottleneck
Even if you only are creating a draft journal entry it locks the last one
It applies to all accounting Journal Entries

e.g.

 - Customer Invoices
 - Credit Notes
 - Customer Payments
 - Vendor Bills
 - Vendor Refunds
 - Vendor Payment
 - Manual Journal Entries

Then, the following concurrency errors are being raised now frequently:

* Editing the last record used to get the new number from another process
* Creating a new draft invoice/payment (not only when posting it)
* Creating a transaction to create an invoice then payment or vice versa raises a deadlock error
* Reconciling the last record it could be a heavy process
* Creating 2 or more Invoices/Bills at the same time
* Creating 2 or more Payments at the same time (Even if your country allows to relax gaps in these kinds of documents, you are not able anymore to change the implementation to standard)
* Creating 2 or more Journal Entries at the same time


All these increases in concurrency errors bring more issues since that Odoo is not prepared:

* Using e-commerce, configured with Invoicing Policy Ordered and Automatic Invoice, the portal users will see errors in the checkout even if the payment was done, the sale order could be in state draft and request a new payment, so double charges
* Using `subscription_template.payment_mode=success_payment` you will see subscriptions with tag "payment exception"
* Using accounting creating invoice or payment, you will see errors then you will need to start the process again and again until you get the lock before another user
* The workers could be used for more time than before since that it could be waiting for release so less concurrent users supported or loading page is shown more frequently affecting the performance

The new accounting number is a significant bottleneck

.. image:: https://media.istockphoto.com/vectors/road-highways-with-many-different-vehicles-vector-id1328678690


If you do not believe all these issues are occurring, we have created the following issues and unittest to reproduce errors in v14.0 including the deadlock, but not v13.0:

 - Passing unittest for `13.0 - [REF] account: Adding unittests for concurrency issues in account_move sequences <https://github.com/odoo/odoo/pull/91614>`_
 - Concurrency errors for `14.0 - [REF] account: Adding unittests for concurrency issues in account_move sequences <https://github.com/odoo/odoo/pull/91525>`_
 - `Stress testing and issue reported to Odoo <https://github.com/odoo/odoo/issues/90465>`_
 - `[BUG] account: Concurrency errors increased considerably in account.move for Odoo>=v14.0 #91873 <https://github.com/odoo/odoo/issues/91873>`_


Using this module, you can configure what kind of documents the gap sequence may be relaxed
And even if you must use no-gap in your company or country it will reduce the concurrency issues since the module is using an extra table (ir_sequence) instead of locking the last record

For those like me who think that the implementation before Odoo v14.0 was much better, for the accountants who think it should not be possible to manually enter the sequence of a customer invoice, for the auditor who considers that resequencing journal entries is prohibited by law, this module may be a solution to get out of the nightmare.

The field names used in this module to configure the sequence on the journal are exactly the same as in Odoo version 13.0 and previous versions. That way, if you migrate to Odoo version 14.0 and you install this module immediately after the migration, you should keep the previous behavior and the same sequences will continue to be used.

The module removes access to the *Resequence* wizard on journal entries.
