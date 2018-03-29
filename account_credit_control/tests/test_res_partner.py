# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCreditControlPolicyLevel(TransactionCase):
    post_install = True
    at_install = False

    def test_check_credit_policy(self):
        """
        Test the constrains on res.partner
        First we try to assign an account and a policy with a wrong policy
        (this policy doesn't contains the account of the partner).
        After that we add the previous account in the policy and
        retry to assign this policy and this account on the partner
        :return:
        """
        policy = self.env.ref('account_credit_control.credit_control_3_time')

        partner = self.env['res.partner'].create({
            'name': 'Partner 1',
        })
        account = partner.property_account_receivable_id

        with self.assertRaises(ValidationError):
            partner.write({
                'credit_policy_id': policy.id,
            })

        policy.write({
            'account_ids': [(6, 0, [account.id])]
        })
        partner.property_account_receivable_id = account.id
        partner.credit_policy_id = policy.id
