This module extends the functionality of Accounting Odoo module, to
generate custom sub sequences for accounting entries, if fiscal years are not "classic".
(ie: last day = 31 / last month = 12)

without this module, in such cases (for example, for fiscal year from 01 April 2020 to 31 May 2021)
accounting moves of the same fiscal year will not have the same numbering: Some entries will
have ``BILL/2020/`` prefix and other will have ``BILL/2021/``, that is not allowed in many countries.

That modules fixes this problem.
