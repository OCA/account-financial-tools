from odoo.addons.stock_account.models.account_move import AccountMove


def monkey_patches():
    def _compute_show_reset_to_draft_button(self):
        # Bypassing _compute_show_reset_to_draft_button method from stock_account
        super(AccountMove, self)._compute_show_reset_to_draft_button()

    AccountMove._compute_show_reset_to_draft_button = (
        _compute_show_reset_to_draft_button
    )
