from odoo.tests.common import TransactionCase


class TestUserRestriction(TransactionCase):

    def setUp(self):
        super(TestUserRestriction, self).setUp()
        self.account_user = self.env['res.users'].create({
            'login': 'account_user',
            'name': 'account_user',
            'groups_id': [(6, 0, [self.env.ref('account.group_account_invoice').id])]
        })
        self.account_user_assigned_journal = self.env['res.users'].create({
            'login': 'account_user_assigned_journal',
            'name': 'account_user_assigned_journal',
            'groups_id': [(6, 0, [self.env.ref(
                'account_journal_user_restriction.'
                'group_assigned_journals_user'
            ).id])]
        })
        self.sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale')])[0]
        self.journal_model = self.env['account.journal']

    def test_access_picking_type(self):
        # assigned_user_ids is not set: both users can read
        journals = self.journal_model.sudo(self.account_user.id).search([
            ('type', '=', 'sale')])
        self.assertTrue(self.sale_journal in journals)
        journals = self.journal_model.sudo(
            self.account_user_assigned_type.id).search([
                ('type', '=', 'sale')])
        self.assertTrue(self.sale_journal in journals)

        self.sale_journal.assigned_user_ids = [
            (6, 0, [self.account_user_assigned_journal.id])]
        # assigned_user_ids is set with account_user_assigned_journal:
        # both users can read
        journals = self.journal_model.sudo(self.account_user.id).search([
            ('type', '=', 'sale')])
        self.assertTrue(self.sale_journal in journals)
        journals = self.journal_model.sudo(
            self.account_user_assigned_journal.id).search([
                ('type', '=', 'sale')])
        self.assertTrue(self.sale_journal in journals)

        self.sale_journal.assigned_user_ids = [
            (6, 0, [self.account_user.id])]
        # assigned_user_ids is set with account_user: only account_user can read
        journals = self.journal_model.sudo(self.account_user.id).search([
            ('type', '=', 'sale')])
        self.assertTrue(self.sale_journal in journals)
        journals = self.journal_model.sudo(
            self.account_user_assigned_journal.id).search([
                ('type', '=', 'sale')])
        self.assertFalse(self.sale_journal in journals)
