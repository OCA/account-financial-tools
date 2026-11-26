# Workflow Guide

To use the Intercompany Transaction module:

1. Go to **Accounting → Accounting → Intercompany Transaction Config**.
2. Create a new intercompany configuration for your companies:
   - Set **From Company** and **To Company**.
   - Configure **Debit Account (From Company)**, **Credit Account (To Company)**, **Debit Account (To Company)**, and **To Company Journal**.
3. Create a journal entry in the **source company**:
   - Set the **Target Company** on the move line if applicable.
   - Complete the journal entry lines as usual.
4. Post the journal entry in the source company:
   - The system automatically creates the corresponding intercompany entry in the **target company** journal.
   - Users in the target company receive email notifications about the created entry.
5. Cancel a source company journal entry:
   - If the linked intercompany entries in the target company are in **draft state**, they will automatically be cancelled.
   - Users receive email notifications for the cancelled entries.
   - If the target entries are already **posted**, the system prevents cancelling or resetting the source entry and shows a warning:
     ```
     The linked intercompany journal entry in the target "Company Name" is already posted. You cannot reset the journal entry to Draft.
     ```
6. Monitor intercompany entries in **Accounting → Accounting → Intercompany Transaction**.