First, for each currency of your cash boxes, you must define the bank notes and coin rolls for that currency (coin rolls are often standardised by the Central Bank). You can also definie the coins, but it's not useful if your bank only accept coin rolls and not coins.

.. figure:: static/description/currency_form_view.png
   :scale: 100 %
   :alt: Currency form view

To save time for new users, this module provides the bank notes, coins and coin rolls for several currencies (EUR, USD, CAD, etc.). If it is not the case for your currency, it would be very nice of you to contribute it (you can use the file *account_cash_deposit/data/cash_unit_eur.xml* as an example).

To save time when encoding the cash deposits/orders, you can set the parameter *Auto Create* on the bank notes and/or coin rolls that you use very often.

On the Accounting configuration page, in the section *Bank & Cash*, the *Inter-Banks Transfer Account* must be configured.
