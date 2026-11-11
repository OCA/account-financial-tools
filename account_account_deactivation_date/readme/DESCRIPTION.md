This module adds a **Deactivation Date** to accounts, so an account can be phased out of
the chart of accounts without being deleted.

The date drives the standard _Deprecated_ flag:

- Until the date, the account stays active everywhere.
- From the date on, the account is deprecated and disappears from the configuration
  fields (journals, products, taxes, partners, fiscal positions, etc.). A daily
  scheduled action deprecates the accounts whose date has been reached.

Journal entries are validated against their **accounting date**:

- Entries dated on or after the deactivation date cannot use the account, whether they
  come from the user interface, an import or an integration.
- Entries dated before the deactivation date remain allowed, even after the date has
  passed. Period-closing adjustments and back-dated entries keep working, and the
  history is never changed.

Every inclusion, change or removal of the date is tracked in the account chatter.
