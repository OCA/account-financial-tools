In Odoo version 13.0 and previous versions, the number of journal entries was generated from a sequence configured on the journal.

In Odoo version 14.0, the number of journal entries can be manually set by the user. Then, the number attributed for next journal entries in the same journal is computed by a complex piece of code that guesses the format of the journal entry number from the number of the journal entry which was manually entered by the user. It has several drawbacks:

* the available options for the sequence are limited,
* it is not possible to configure the sequence in advance before the deployment in production,
* as it is error-prone, they added a *Resequence* wizard to re-generate the journal entry numbers, which can be considered as illegal in many countries,
* the `piece of code <https://github.com/odoo/odoo/blob/14.0/addons/account/models/sequence_mixin.py>`_ that handle this is not easy to understand and quite difficult to debug.

For those like me who think that the implementation before Odoo v14.0 was much better, for the accountants who think it should not be possible to manually enter the sequence of a customer invoice, for the auditor who consider that resequencing journal entries is prohibited by law, this module may be a solution to get out of the nightmare.

The field names used in this module to configure the sequence on the journal are exactly the same as in Odoo version 13.0 and previous versions. That way, if you migrate to Odoo version 14.0 and you install this module immediately after the migration, you should keep the previous behavior and the same sequences will continue to be used.

The module removes access to the *Resequence* wizard on journal entries.
