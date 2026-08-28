This module adds an Access Groups field on accounts. When set, only users in the
selected groups can view journal entries and journal items that use those accounts.

In standard Odoo, accounting users can generally access all journal entries and items.
In some cases, even certain accounting managers should not see specific entries because
they contain confidential information. This module fills that gap by enforcing
account-based visibility rules.

Note: The groups set on accounts are intended to be additional to the standard
account.group_account_user, so users still keep basic accounting access. For this
reason, the module also provides a default group, View Restricted Accounts, which 
implies account.group_account_user.
