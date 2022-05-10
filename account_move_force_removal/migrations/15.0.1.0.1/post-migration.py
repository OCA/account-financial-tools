from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    users_billing = env.ref("account.group_account_invoice").users
    group = env.ref("account_move_force_removal.group_account_move_force_removal")
    group.users = [(4, user.id) for user in users_billing]
