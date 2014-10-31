Dunning Fees for Credit Control
===============================

This extention of credit control adds the notion of dunning fees
on credit control lines.

Configuration
-------------
For release 0.1 only fixed fees are supported.

You can specifiy a fixed fees amount, a product and a currency
on the credit control level form.

The amount will be used as fees values the currency will determine
the currency of the fee. If the credit control line has not the
same currency as the fees currency, fees will be converted to
the credit control line currency.

The product is used to compute taxes in reconciliation process.

Run
---
Fees are automatically computed on credit run and saved
on the generated credit lines.

Fees can be manually edited as long credit line is draft

Credit control Summary report includes a new fees column
--------------------------------------------------------
Support of fees price list
