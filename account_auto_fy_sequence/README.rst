Automatic creation of fiscal year sequences
===========================================

This module adds the possibility to use the %(fy)s placeholder
in sequences. %(fy)s is replaced by the fiscal year code when
using the sequence.

The first time the sequence is used for a given fiscal year,
a specific fiscal year sequence starting at 1 is created automatically.

Caveat
------

/!\ If you change %(year)s to %(fy)s on a sequence that has
already been used for the current fiscal year, make sure to manually
create the fiscal year sequence for the current fiscal year and
initialize it's next number to the correct value.
For this reason, the module will forbid the user to change
a sequence from %(year)s to %(fy)s if it's next number is > 1.

Credits
-------

Author:

* Stéphane Bidoul (ACSONE)

Contributors: 

* Laetitia Gangloff (ACSONE)