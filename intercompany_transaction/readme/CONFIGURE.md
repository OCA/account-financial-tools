# Configuration Guide

## 1. Intercompany Transaction Configuration

1. Navigate to:
   **Accounting > Accounting > Intercompany Transaction Config**
2. Click **Create** to add a new configuration.
3. Set the following fields:
   - **From Company** – Source company for the journal entry.
   - **To Company** – Target company where intercompany entry will be created.
   - **Debit Account (From Company)** – Debit account in the source company.
   - **Debit Account (To Company)** – Debit account in the target company.
   - **Credit Account (To Company)** – Credit account in the target company.
   - **Target Company Journal** – Journal in the target company for posting intercompany entry.
4. Save the configuration.

> Each source company can have multiple intercompany rules for different target companies.

---

## 2. Viewing Intercompany Transactions

1. Navigate to:
   **Accounting > Accounting > Intercompany Transaction**
2. This menu displays **only intercompany journal entries** that were automatically created by the module.
3. You can review the status, linked source/target entries, and posted/draft states.

---

## 3. Using the Configuration

- When creating a journal entry in the **source company**:
  1. Select the **Target Company** in the journal entry lines.
  2. Accounts will be automatically set based on your intercompany configuration.
  3. Posting the source journal entry will automatically create the corresponding entry in the target company using the configured journal.
  4. Emails are automatically sent to target company users when entries are created or cancelled.

---

## Notes

- **Draft State**: Target intercompany entries in draft state can be cancelled if the source entry is cancelled.
- **Posted State**: If target entries are already posted, the source entry **cannot** be reset to draft. A warning will be shown:

  > "The linked intercompany journal entry in the target company is already posted. You cannot reset the journal entry to Draft."
