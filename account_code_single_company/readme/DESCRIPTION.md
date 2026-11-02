Improve account code display and search for accounts linked to a single company.

When an account is linked to one and only one company (`len(company_ids) == 1`), its account code for that company is stored in `code_store_single_company`.
This enables `account.code`, `account.display_name`, and domain searches by code to return the single-company account code regardless of the active session context company (e.g. when querying via API).
