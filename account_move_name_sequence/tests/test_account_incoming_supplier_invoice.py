import json

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountIncomingSupplierInvoice(AccountTestInvoicingCommon):
    """Testing creating account move fetching mail.alias"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env["ir.config_parameter"].sudo().set_param(
            "mail.catchall.domain", "test-company.odoo.com"
        )

        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "Internal User",
                "login": "internal.user@test.odoo.com",
                "email": "internal.user@test.odoo.com",
            }
        )

        cls.supplier_partner = cls.env["res.partner"].create(
            {
                "name": "Your Supplier",
                "email": "supplier@other.company.com",
                "supplier_rank": 10,
            }
        )

        cls.journal = cls.company_data["default_journal_purchase"]

        journal_alias = cls.env["mail.alias"].create(
            {
                "alias_name": "test-bill",
                "alias_model_id": cls.env.ref("account.model_account_move").id,
                "alias_defaults": json.dumps(
                    {
                        "move_type": "in_invoice",
                        "company_id": cls.env.user.company_id.id,
                        "journal_id": cls.journal.id,
                    }
                ),
            }
        )
        cls.journal.write({"alias_id": journal_alias.id})

    def test_supplier_invoice_mailed_from_supplier(self):
        """this test is mainly inspired from
        addons.account.tests.test_account_incoming_supplier_invoice
        python module but we make sure account move is draft without
        name
        """
        message_parsed = {
            "message_id": "message-id-dead-beef",
            "subject": "Incoming bill",
            "from": f"{self.supplier_partner.name} " f"<{self.supplier_partner.email}>",
            "to": f"{self.journal.alias_id.alias_name}@"
            f"{self.journal.alias_id.alias_domain}",
            "body": "You know, that thing that you bought.",
            "attachments": [b"Hello, invoice"],
        }

        invoice = (
            self.env["account.move"]
            .with_context(
                tracking_disable=False,
                mail_create_nolog=False,
                mail_create_nosubscribe=False,
                mail_notrack=False,
            )
            .message_new(
                message_parsed,
                {"move_type": "in_invoice", "journal_id": self.journal.id},
            )
        )

        message_ids = invoice.message_ids
        self.assertEqual(
            len(message_ids), 1, "Only one message should be posted in the chatter"
        )
        self.assertEqual(
            message_ids.body,
            "<p>Vendor Bill Created</p>",
            "Only the invoice creation should be posted",
        )

        following_partners = invoice.message_follower_ids.mapped("partner_id")
        self.assertEqual(following_partners, self.env.user.partner_id)
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(invoice.name, "/")
