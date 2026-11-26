Automate the creation and management of intercompany journal entries in Odoo.
This module ensures that accounting transactions in a source company are correctly reflected in the corresponding target company according to predefined intercompany configurations.

# Features

## Automatic Intercompany Moves
- Posting a journal entry in the **source company** automatically creates the corresponding entry in the **target company** based on the intercompany configuration.

## Intercompany Configuration
- Configure settings for each company:
  - **From Company** and its **Debit Account**
  - **To Company** and its **Debit Account**, **Credit Account**
  - **Target Company Journal** for intercompany transactions

## Automatic Cancellation
- Resetting a source company journal entry to draft automatically cancels the linked intercompany journal entries in the target company, **provided they are still in draft state**.  
- Users receive email notifications for cancelled intercompany entries.

## Posting Restrictions
- If the target company intercompany entries are already posted, the source company journal entry **cannot be reset to draft**.
- Warning message for users:
  > The linked intercompany journal entry in the target company is already posted. You cannot reset the journal entry to Draft.

## Email Notifications
- Target company users receive notifications when intercompany moves are created or cancelled.

## Filtered View
- The **Intercompany Transaction** menu shows only journal entries related to intercompany transactions for easy tracking.