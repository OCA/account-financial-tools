This module extends the Odoo CE account module to make easier
accouting journal configuration.


Without that module, accountant have to put an account on two tabs "Incoming Payments"
and "Outgoing Payments".

Otherwise, when entering a payment, there is an error raised by the system.

.. figure:: static/description/payment_error.png

With that module, the setting is done automatically, and the default 'Account Journal'
is set in the two other tags.

.. figure:: static/description/journal_form.png

**Note:**

When installing the module, the configuration will be done for existing journals.
