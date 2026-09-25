## 19.0.1.0.0

In this version we have extract leasing stuff from account_loan and create the new module account_leasing, while refactoring following change occured:

 * remove the `has_invoices` computed field on `account.loan.line` which was exactly the same has `has_moves` field
 * rename loan_type into loan_method
 * add loan_type computed store field to easily filter group by loan / borrow / leasing
 * add support to mark future moves as auto_post

## 16.0.1.0.0

Due to the changes on 16, we will generate two moves on leasings, one
for the invoice, and another one for the change from long to short term.
