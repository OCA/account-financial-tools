Lock each accounting journal independently.

In addition to the lock dates in standard Odoo provide a (more strict) per
journal lock date.

By default users with "Adviser" role are exempt from the journal lock date
check. Developers can implement more ample exepmtions from the lock date check
through a hook function on `account.journal`.
