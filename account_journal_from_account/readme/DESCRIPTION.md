# Account Journal Creation from Chart of Accounts

## Overview

This module enhances the accounting functionality by allowing users to **create bank journals directly from the Chart of Accounts (COA)**.

It simplifies journal creation, ensures consistency, and reduces manual configuration effort by providing smart defaults and user confirmation handling.

---

## Key Features

### 1. Create Journal from Chart of Accounts

- Adds a **"Create Journal"** button in the Chart of Accounts (tree view).
- Provides a **server action** to create journals from selected accounts.
- Supports creation of:
  - **Bank journals**

---

### 2. Smart Duplicate Handling

- If a journal already exists for the selected account:
  - A **confirmation wizard** is displayed.
  - Message:  
    _"Journal is already available for this account. Do you want to create it again?"_
- Users can:
  - **Cancel** → No new journal is created
  - **Confirm** → A new journal is created

---

### 3. Automatic Payment Account Configuration

- Adds configuration fields in Accounting Settings:
  - `inbound_payment_account_id`
  - `outbound_payment_account_id`

- When these accounts are configured:
  - Newly created journals automatically set:
    - **Incoming Payments Account**
    - **Outgoing Payments Account**

---

### 4. Automated Journal Setup

When creating a journal from COA:

- Journal type is determined based on account type:
  - Bank → Bank Journal
- Payment methods are automatically configured
- Payment accounts are assigned based on system configuration

---

## Use Cases

- Quickly create journals for newly created accounts
- Bulk journal creation from multiple accounts
- Standardize payment account setup across journals
- Avoid duplicate journal creation with user confirmation
