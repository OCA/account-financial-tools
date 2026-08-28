If a journal entry includes lines on accounts restricted by different access groups, the
entry is accessible to any user who belongs to at least one (not all) of those groups.

When Odoo's standard duplicate-bill detection finds a matching move that the current user
cannot read (because the match uses a restricted account), that match is silently dropped
from `duplicated_ref_ids` to avoid leaking data. As a result, the form gives no hint that
a hidden potential duplicate exists. Surfacing a warning in that case was considered but
dropped as too costly for the limited business benefit.
