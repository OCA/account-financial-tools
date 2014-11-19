Recompute tax amount
====================

The way the tax amount is computed in journal entries in the core
``account`` module is prone to input errors.

This module forces the the tax amount to always be: ``credit - debit``
whatever the configuration of the tax is and whatever the user types in
the tax amount.

**Warning**: there is no guarantee that this module will work for every
country, at least it works for Switzerland and France where the tax
amount is always ``credit - debit``.
