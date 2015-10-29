Account Constraints
===================

Add constraints in the accounting module of OpenERP to avoid bad usage
by users that lead to corrupted datas. This is based on our experiences
and legal state of the art in other software.

Summary of constraints are:

* For manual entries when multicurrency:

  a. Validation on the use of the 'Currency' and 'Currency Amount'
     fields as it is possible to enter one without the other
  b. Validation to prevent a Credit amount with a positive
     'Currency Amount', or a Debit with a negative 'Currency Amount'

* Add a check on entries that user cannot provide a secondary currency
  if the same than the company one.

* Remove the possibility to modify or delete a move line related to an
  invoice or a bank statement or a payment order, no matter what the status of the move
  (draft, validated or posted).
  This way you ensure that the user cannot make mistakes even in draft state, he must pass through
  the parent object to make his modification.

  Contributors
  * Stéphane Bidoul <stephane.bidoul@acsone.eu>

