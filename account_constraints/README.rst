Account Constraints
===================

Add constraints in the accounting module of OpenERP to avoid bad usage
by users that lead to corrupted datas. This is based on our experiences
and legal state of the art in other software.

Summary of constraints are:

* Add a constraint on account move: you cannot pickup a date that is not
  in the fiscal year of the concerned period (configurable per journal)

* For manual entries when multicurrency:

  a. Validation on the use of the 'Currency' and 'Currency Amount'
     fields as it is possible to enter one without the other
  b. Validation to prevent a Credit amount with a positive
     'Currency Amount', or a Debit with a negative 'Currency Amount'

* Add a check on entries that user cannot provide a secondary currency
  if the same than the company one.

* Remove the possibility to modify or delete a move line related to an
  invoice or a bank statement, no matter what the status of the move
  (draft, validated or posted). This is useful in a standard context but
  even more if you're using `account_default_draft_move`. This way you ensure
  that the user cannot make mistakes even in draft state, he must pass
  through the parent object to make his modification.

Contributors
============

  * Stéphane Bidoul <stephane.bidoul@acsone.eu>
  * Joel Grand-Guillaume (Camptocamp SA)
