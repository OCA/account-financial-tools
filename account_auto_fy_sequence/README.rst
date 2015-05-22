Automatic creation of fiscal year sequences
===========================================

This module adds the possibility to use the %(fy)s placeholder
in sequences. %(fy)s is replaced by the fiscal year code when
using the sequence.

The first time the sequence is used for a given fiscal year,
a specific fiscal year sequence starting at 1 is created automatically.

The module also replaces %(year)s by %(fy)s in the default prefix
for new journals, assuming it is a safer default.

Caveat
------

/!\ If you change %(year)s to %(fy)s on a sequence that has
already been used for the current fiscal year, make sure to manually
create the fiscal year sequence for the current fiscal year and
initialize it's next number to the correct value.
For this reason, the module will forbid the user to change
a sequence from %(year)s to %(fy)s if it's next number is > 1.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_auto_fy_sequence%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
-------

Author:

* Stéphane Bidoul (ACSONE)

Contributors: 

* Laetitia Gangloff (ACSONE)
