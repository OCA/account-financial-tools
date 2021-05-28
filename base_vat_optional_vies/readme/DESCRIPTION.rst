This module extends base_vat module features allowing to know if VIES
validation was passed or not.

Then you can use "VIES validation passed" field in order to show VAT ID with
or without country preffix in invoices, for instance.

*NOTE*: Although VIES validation is set in your company, this validation
will not block VAT ID write (main difference to Odoo standard behavior) if this
VAT ID is valid in its country.
