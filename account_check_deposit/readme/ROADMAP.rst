* Add an option on journals that can be deposited ``grouped_move_line``
  to generate an account move with a single main line, that reconciles
  all the lines.

* Move the configuration ``check_deposit_offsetting_account`` and
  ``check_deposit_transfer_account_id`` from ``res.company`` to the
  ``account.journal`` that can be deposited.
  Make required the ``bank_journal_id`` field, only in the ``bank_account``
  option and not in the ``transfer_account`` option.

* Rename fields that belong ``check`` as this module allow to make deposit
  of checks, cash, etc...
