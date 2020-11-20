The user can configure journal entries templates, useful for recurring entries.
The amount of each template line can be computed (through python code)
or kept as user input.

If user input, when using the template, user has to fill
the amount of every input lines.

The journal entry form allows lo load, through a wizard,
the template to use and the amounts to fill.

**Notable features:**

This module enhance the capability of module account_move_template with following features,

#. Optional account for negative amount.

    When the Journal entry is created, and credit/debit is negative value, change debit/credit
    side and use the opt_account_id

#. Allow overwrite move line values with overwrite dict.

    Normally, the journal items created by the template will require user input on wizard.
    This feature allow passing the overwrite values with a dictionary.
    This is particularly useful when the wizard is called by code.

    Sample of dictionary to overwrite move lines::

      {'L1': {'partner_id': 1, 'amount': 100, 'name': 'some label'},
       'L2': {'partner_id': 2, 'amount': 200, 'name': 'some label 2'}, }
