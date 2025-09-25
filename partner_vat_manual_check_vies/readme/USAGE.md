To use this module, you need to:

- Go to *Invoicing* / Configuration / Settings menu
- Check **Verify VAT Numbers**
-  Optionally, choose the **VIES API** used to query the service:
   -  *REST API* (default): direct HTTP call to the VIES REST endpoint
   -  *SOAP API*: call through the ``stdnum`` library (legacy SOAP service)
- Go to *Contacts*
- In “Contact” form for an EU based partner, next to VAT number you get either a check sign (if validated) of question mark (if validation failed) or cross sign (if invalid)
![](static/description/valid.png)

- If validation failed, you get a new button **Validate with VIES** which allows you to request a new validation from VIES
![](static/description/validation_failed.png)
- Each VIES check posts a message in the chatter with the resulting status (valid, invalid or the reason why the validation could not be performed)
- If VAT number is invalid, you should correct if or remove it, you get a new button **Clear invalid VAT** that would remove VAT and replace by "/"
![](static/description/invalid.png)

You also get 2 planned action (cron job), disabled by default that will try to request new validation for the first 20 partners with failed validation, and another one that would clear VAT from all partners with invalid VAT.
It also disables `base_vat` IAP cron job.