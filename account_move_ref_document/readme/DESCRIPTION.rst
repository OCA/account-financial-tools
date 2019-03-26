The objective of this module is to create permanent link from journal entries back to
the source document that create it. For example, validating invoice creates journal entry. Invoice will be
source document, and journal entry will have permanent link back its source.

This module add new field Document Ref to Journal Entry, as ``document_id``, ``document_ref``
to account.move and ``document_id`` to account.move.line.

After installing this module, following modules that helps calculate the link will be auto installed,

- account_move_ref_account
- account_move_ref_expense
