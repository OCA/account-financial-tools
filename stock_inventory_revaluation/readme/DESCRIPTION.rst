This module defines a new object stock.inventory.revaluation that
stores the changes in the value of the valuation layers.

The action that triggers the revaluation is the vendor bill

The original stock valuation layer are not affected but new stock valuation
layers are created to reflect the actual value of the stock that is located
in the remaining quantity of a stock valuation layer

This is specially necessary when using a FIFO costing method,
but in any case, a revaluation should be possible independently og the
valuation method.

This is not chaning the past, you can create stock valuation layers in the
past (by forcing the create_date in the database). New layers are created
in order to not interfere the history
