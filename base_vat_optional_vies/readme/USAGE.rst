When VIES VAT Check is activated:

* Odoo will try to validate VAT against VIES online service
* If passed, then "VIES validation passed" field will be True
* If not passed, then try to validate using country validation method
* If validated, then "VIES validation passed" field will be False
* If not validated, then a ValidationError will be shown to user

When VIES VAT Check is not activated:

* "VIES validation passed" field will be always False

You must prefix VAT with country code (ISO 3166-1 alpha-2) and if you want to
bypass country validation you can use "EU" code
