This module extends the functionality of Accounting Odoo module, to
auto generate fiscal years.

Once installed, a cron is running each day. It will create, for each company,
a new fiscal year, if it is the last day of the current fiscal year.

This module is interesting specially in multi company context, to avoid annoying setup every year.

The fiscal year created has a classical "12 monthes" duration, but the accountant
can modify it, once created.

Example
~~~~~~~

If a company has it last fiscal year, defined as:

- ``name``: FY 2021-2022
- ``date_from``: 2021-06-01
- ``date_to``: 2022-05-31

When the cron will be executed on May 31, 2022, it will create the following fiscal year:

- ``name``: FY 2022-2023
- ``date_from``: 2022-06-01
- ``date_to``: 2023-05-31
