This module introduces to journal items two new fields:

* Amount (Used Currency)

* Used Currency

When the journal item is expressed in foreign currency, those fields will be
computed with the amount in foreign currency. Otherwise the company currency
and balance in company currency is filled in.

Those fields are useful for reporting purposes. For example, in an
intercompany context company A (that operates using USD) sells to company B
(that operates using EUR) in EUR, and you want to be able to compare the
balances in a common account across the two companies, using the same
currency EUR.
