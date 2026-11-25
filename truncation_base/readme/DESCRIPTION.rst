This module provides shared, generic infrastructure to truncate (instead of
round) monetary amounts: a ``decimal.precision.truncate()`` helper that cuts
off the extra decimals of a value according to a named Decimal Accuracy
precision, and a "Truncate Subtotal" flag on the partner to express that its
sale condition requires truncation instead of rounding.

Monetary fields always round their value to the record's currency
precision on write, which would silently undo a truncation done at a finer
precision. Pass the record's currency to ``truncate()`` so the effective
precision never exceeds what a Monetary field can actually store.

It also adds an (initially empty) "Truncation" tab on the Companies form,
so consuming modules such as ``sale_order_truncation_subtotal`` and
``sale_blanket_order_truncation_subtotal`` have a common place to expose
their own truncation precision fields, instead of each adding its own tab.

It does not change any computation or define any named precision by
itself: consuming modules declare their own named Decimal Accuracy
precision and use this infrastructure to actually truncate the line
subtotal.
