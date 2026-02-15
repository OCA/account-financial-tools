# Account Account Tag Enhancement

[![License: AGPL-3](https://img.shields.io/badge/License-AGPL%203-blue.svg)](http://www.gnu.org/licenses/agpl-3.0)
[![OCA](https://img.shields.io/badge/oca-18.0-blue.svg)](https://github.com/OCA/account-financial-tools)

Enhance the Odoo account.account.tag model with additional configuration options and administrative features.

## Overview

This module extends the native Odoo account tag functionality by adding:

- **Company Association**: Link account tags to specific companies with a many-to-many relationship
- **Tag Codes**: Unique alphanumeric codes for better tag identification and organization
- **Hierarchical Tags**: Support for parent-child relationships between tags
- **Enhanced Management Interface**: Dedicated configuration views in the Invoicing module

This module is inspired by account_tag_menu for Odoo 12.0, that can be found here:
https://github.com/OCA/account-financial-tools/, branch 12.0.

## Features

### Account Tag Enhancement

- **Code Field**: Each tag can have a unique code for easy reference and integration
- **Multi-Company Support**: Tags can be assigned to multiple companies simultaneously
- **Tag Hierarchy**: Create parent-child relationships for tag organization
- **Color Coding**: Visual distinction of tags using custom colors
- **Applicability**: Configure tag applicability (Purchases, Sales, Both)
- **Country-Specific**: Assign tags to specific countries for localized configurations

### Management Interface

The module provides a comprehensive management interface accessible through:
**Invoicing / Configuration / Accounting / Account Tags**

Features include:
- List view with sortable columns (Code, Name, Parent, Applicability, Color, Country, Companies)
- Detailed form view for creating and editing tags
- Quick access to child tags from parent tag form
- Multi-company filtering and management
- Status management (Active/Archived)

## Requirements

- Odoo 18.0 Community Edition
- `account` module (native Odoo)

## Installation

1. Clone this repository into your Odoo addons directory
2. Restart odoo
3. Update the module list in Odoo
4. Install the module from the Apps menu

```bash
git clone https://github.com/yourusername/account_tag.git /path/to/odoo/addons/
```

## Usage

### Creating Account Tags

1. Navigate to **Invoicing / Configuration / Accounting / Account Tags**
2. Click **Create** to add a new tag
3. Fill in the tag details:
   - **Tag Name**: Unique name for the tag
   - **Code**: Unique alphanumeric code
   - **Parent Tag**: (Optional) Select a parent tag for hierarchy
   - **Applicability**: Choose Purchases, Sales, or Both
   - **Color**: Select a color for visual identification
   - **Companies**: Select which companies this tag applies to
   - **Country**: (Optional) Specify a country for localization

### Managing Child Tags

1. Open a parent tag in the form view
2. In the **Child Tags** section, add or manage child tags directly

### Organizing Tags

- Use the hierarchy feature to organize tags by category
- Apply company filtering to manage multi-company setups
- Use codes for programmatic access and reporting

## Configuration

No additional configuration is required beyond module installation. All settings are managed through the standard Odoo interface.

## API Usage

### Creating Tags Programmatically

```python
tag = self.env['account.account.tag'].create({
    'name': 'Example Tag',
    'code': 'EXG',
    'company_ids': [(6, 0, [company_id])],
    'parent_id': parent_tag_id,
})
```

### Filtering by Company

```python
tags = self.env['account.account.tag'].search([
    ('company_ids', 'in', company_id)
])
```

### Finding by Code

```python
tag = self.env['account.account.tag'].search([
    ('code', '=', 'TAG_CODE')
], limit=1)
```

## Known Issues

None at this time. Please report any issues on the GitHub repository.

## Roadmap

No further enhancements planed for this module.

## Credits

**Author**: Michael Blickenstorfer  
**Website**: https://github.com/michi-blicki/account_tag
**Created**: 2026-02-15
**Last Update**: 2026-02-15

## License

This module is licensed under **AGPL-3**. See LICENSE file for details.

---

## Contributing

We welcome contributions! Please follow the OCA Contributing Guidelines.

## Maintainer

[![michi.blicki](https://img.shields.io/badge/Maintained%20by-michi.blicki-blue.svg)](https://github.com/michi-blicki/account_tag)
