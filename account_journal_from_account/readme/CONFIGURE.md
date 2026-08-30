# Account Journal Creation from Chart of Accounts

This document explains how to configure the module to enable journal creation from the Chart of Accounts.

---

## 1. Configure Payment Accounts

To automatically assign payment accounts in newly created journals:

1. Go to **Accounting > Configuration > Settings**.
2. Locate the payment account configuration section.
3. Set the following fields:
   - **Inbound Payment Account**
   - **Outbound Payment Account**
4. Save the settings.

**Notes:**

- These accounts will be automatically assigned when creating a new journal.
- If not configured, journals will be created without predefined payment accounts.

---

## 2. Prepare Chart of Accounts

Ensure that the accounts from which you want to create journals are properly configured:

1. Go to **Accounting > Configuration > Chart of Accounts**.
2. Identify accounts of type:
   - **Bank**
3. These account types are used to determine the journal type during creation.

---

## 3. Server Action Availability

The module provides a **server action** to create journals:

1. Go to **Accounting > Configuration > Chart of Accounts**.
2. Select one or multiple accounts.
3. Use the **Action** menu to trigger journal creation.

---