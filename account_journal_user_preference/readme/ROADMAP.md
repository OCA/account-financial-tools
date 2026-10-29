Preference ordering also applies when a caller explicitly requests the
model's default order. Odoo 18 passes that order internally for ordinary
searches and dropdowns.

Applying preferences materializes all eligible journals before
pagination. This approach is intended for ordinary journal lists, rather
than very large journal datasets.
