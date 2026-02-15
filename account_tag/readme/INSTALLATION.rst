Installation Guide
==================

Prerequisites
-------------
- Odoo 18.0 Community or Enterprise edition

Dependencies
----------------
This module depends on the following Odoo modules:
- `account`

Download Steps
------------------

Option 1: Download via GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#. Navigate to some Download directory
#. Clone the repository:
   .. code-block:: bash

      git clone https://github.com/OCA/account-financial-tools.git
#. Change to the account-financial-tools directory:
    .. code-block:: bash
        
       cd account-financial-tools
#. Copy the account_tag directory to your Odoo addons directory:
    .. code-block:: bash
        
       cp -r account_tag /path/to/odoo/addons/

Option 2: Download via ZIP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#. Navigate to the GitHub repository:
    `OCA/account-financial-tools <https://github.com/michi-blicki/account-financial-tools>`_.
#. Download the ZIP file and extract it.
#. Copy the account_tag directory to your Odoo addons directory.

Installation Steps
------------------
#. Restart your Odoo server to recognize the new module.
#. Go to the Apps menu in Odoo and update the app list.
#. Search for **"Account Account Tag Enhancement"** and click **"Activate"**.

Upgrade Steps
------------------
#. Go to the Apps menu in Odoo.
#. Search for **"Account Account Tag Enhancement"**.
#. Click on the module to open its details page.
#. Click the **"Upgrade"** button and confirm the upgrade.

Uninstallation Steps
--------------------
#. Go to the Apps menu in Odoo.
#. Search for **"Account Account Tag Enhancement"**.
#. Click on the module to open its details page.
#. Click the **"Uninstall"** button and confirm the uninstallation.