User Guide
================

Getting Started
-----------------
This module enhances the functionality of account tags in Odoo by allowing you to define 
custom tags and company-specific tags. It also enhances the standard account tags with
additional fields such as company_ids, code, parent_id and child_ids.

Permissions required
--------------------
To use this module, you need to have the following permissions:
- Access to the Accounting module
- Group `account.group_account_readonly`.

Basic Usage
-----------------
#. Navigate to the Accounting module in Odoo.
#. Go to Configuration > Account Tags.
#. Click on the "Create" button to create a new account tag.
#. Fill in the required fields

.. list-table:: Account Tag Fields
   :header-rows: 1

   * - Field
     - Description
     - Required
   * - Tag Name
     - The name of the account tag.
     - Yes
   * - Active
     - Whether the account tag is active or archived.
     - No
   * - Code
     - A unique code for the account tag.
     - Yes
   * - Parent Tag
     - The parent tag of this account tag, if any.
     - No
   * - Applicability
     - The applicability of the account tag (e.g., "Accounts", "Taxes", "Products").
     - Yes
   * - Color Index
     - The color associated with this account tag.
     - No
   * - Companies
     - The companies for which this account tag is applicable.
     - No
   * - Country
     - The country for which this account tag is applicable, if any.
     - No
   * - Child Tags
     - The child tags of this account tag, if any.
     - No

Managing Tag Hierarchies
-------------------------
You can create hierarchical relationships between account tags by setting the "Parent Tag" field.
This allows you to organize your tags in a tree structure. For example, you could have a parent 
tag called "Revenue" with child tags like "Product Sales" and "Service Sales".

**Example Hierarchy**:
```
├─ Financial Tags
│  ├─ Assets
│  ├─ Liabilities
│  └─ Equity
├─ Tax Tags
│  ├─ VAT
│  └─ Income Tax
└─ Reporting Tags
   ├─ Profit Center
   └─ Cost Center
```

Color Coding
-----------------
You can assign a color to each account tag to visually differentiate them in reports and views.

Use colors strategically:
- **Red**: High-priority or tax-related tags
- **Green**: Assets and income tags
- **Blue**: General operational tags
- **Yellow**: Cost centers and special reporting
