This module extends `date.range.type` to add `fiscal_year` flag.

Override official `res_company.compute_fiscal_year_dates` to get the
fiscal year date start / date end for any given date.
That methods first looks for a date range of type fiscal year that
encloses the give date.
If it does not find it, it falls back on the standard Odoo
technique based on the day/month of end of fiscal year.
