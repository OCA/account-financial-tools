# Copyright 2019 Apps2GROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
import logging
logger = logging.getLogger('OpenUpgrade')


def create_asset_group(cr):
    view_to_group = {}
    cr.execute('''SELECT id, name, parent_id, company_id
                  FROM account_asset WHERE type = 'view';''')
    for view in cr.fetchall():
        sql = '''INSERT INTO account_asset_group (name, parent_id, company_id)
            VALUES ('%s', %s, %s) returning id;''' % \
            (view[1], view[2] or 'NULL', view[3])
        cr.execute(sql)
        view_id = view[0]
        group_id = cr.fetchone()[0]
        view_to_group[view_id] = group_id
    return view_to_group


def update_asset_and_asset_profile(cr, view_to_group):
    cr.execute('''UPDATE account_asset
                  SET active = false
                  WHERE type = 'view';''')

    for view_id, group_id in view_to_group.items():
        cr.execute('''UPDATE account_asset
                      SET group_id = %s
                      WHERE parent_id = %s;''' % (group_id, view_id))

        cr.execute('''UPDATE account_asset_profile
                      SET group_id = %s
                      WHERE parent_id = %s;''' % (group_id, view_id))


def update_asset(cr):
    cr.execute('''SELECT a.id,
                         a.openupgrade_legacy_12_0_method_number,
                         a.openupgrade_legacy_12_0_method_period,
                         p.account_analytic_id,
                         a.company_id
                    FROM account_asset a
                    LEFT JOIN account_asset_profile p ON a.profile_id = p.id;
               ''')
    for asset in cr.fetchall():
        no_of_entries = asset[1]
        months_between_entries = asset[2]

        values = {}
        # Analytic account
        values['account_analytic_id'] = asset[3] or 'NULL'
        # Number of years
        values['method_number'] = \
            int(no_of_entries * months_between_entries / 12)
        # Period: month / quarter / year (default: year)
        if months_between_entries == 3:
            values['method_period'] = "'quarter'"
        elif months_between_entries == 1:
            values['method_period'] = "'month'"

        vals = ['%s = %s' % (key, value) for key, value in values.items()]
        sql = "UPDATE account_asset SET %s WHERE id = %s" % \
              (', '.join(vals), asset[0])
        logger.debug('update_asset: %s' % sql)
        cr.execute(sql)


def update_asset_profile(cr):
    cr.execute('''SELECT id,
                         openupgrade_legacy_12_0_method_number,
                         openupgrade_legacy_12_0_method_period,
                         company_id FROM account_asset_profile;''')
    for profile in cr.fetchall():

        no_of_entries = profile[1]
        months_between_entries = profile[2]

        values = {}
        # Number of years
        values['method_number'] = \
            int(no_of_entries * months_between_entries / 12)
        # Period: month / quarter / year (default: year)
        if months_between_entries == 3:
            values['method_period'] = "'quarter'"
        elif months_between_entries == 1:
            values['method_period'] = "'month'"

        vals = ['{} = {}'.format(key, value) for key, value in values.items()]
        sql = """UPDATE account_asset_profile
                 SET %s WHERE id = %s""" % (', '.join(vals), profile[0])
        logger.debug('update_asset_profile: %s' % sql)
        cr.execute(sql)


def update_move_line(cr):
    cr.execute("""SELECT l.move_id, l.asset_id, a.profile_id
        FROM account_asset_line l
        LEFT JOIN account_asset a ON l.asset_id = a.id
        WHERE l.move_id IS NOT NULL;""")
    for line in cr.fetchall():
        sql = """UPDATE account_move_line
                 SET asset_id = %s, asset_profile_id = %s
                 WHERE move_id = %s""" % (line[1], line[2], line[0])
        logger.debug('update_move_line: %s' % sql)
        cr.execute(sql)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    cr.execute('''SELECT column_name
                  FROM information_schema.columns
                  WHERE table_name = 'account_asset'
                    AND column_name = 'type';''')
    if cr.fetchone():
        # migrate from account_asset_management
        view_to_group = create_asset_group(cr)
        update_asset_and_asset_profile(cr, view_to_group)
    else:
        # migrate from account_asset
        update_asset(cr)
        update_asset_profile(cr)
        update_move_line(cr)
