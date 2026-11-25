Prevent partner company changes when journal entries exist in other companies.

This module adds a constraint on the partner model to ensure that if a partner has already been used in journal entries (moves or move lines) in one or more companies, the partner's company cannot be changed to a different one. This ensures data consistency and prevents accounting errors where a partner is linked to transactions in companies they are not supposed to belong to.
