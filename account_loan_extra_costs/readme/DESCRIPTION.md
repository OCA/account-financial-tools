This module extends `account_loan` to manage extra costs attached to a
loan: insurance premiums, application fees, management fees, etc.

Each cost is booked on its own account in every journal entry (or
invoice line in leasing), so the bookkeeping can be reconciled with the
lender's amortization table line by line.

Four calculation methods are supported:

- Fixed amount per installment
- Rate on initial capital
- Rate on remaining capital, recomputed every period
- Rate on remaining capital at the loan anniversary date

Costs can be flagged as `upfront` (booked once at loan posting time and
deducted from the cash received) or `periodic` (added to every
installment).
