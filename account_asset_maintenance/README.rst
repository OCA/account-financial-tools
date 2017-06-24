.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Account Asset Maintenance
=========================

By installing this module, it will introduce a relationship between assets and
equipment. This will allow you to relate an asset to an equipment and the other
way around.

Moreover, this module improves the action of scrapping an equipment, sending a
message and automatically setting the scrap date when the action is performed.

Configuration
=============

To configure this module, you need to:

#. Go to 'Settings' -> 'Technical' -> 'Email' -> 'Templates' and create a new template you wish to use for equipment scrapping notifications
#. Go to 'Accounting' -> 'Configuration' -> 'Settings'
#. You will find a new section called 'Scrapping', there you will be able to select the mail template just created as 'Equipment Scrap Template Email'
#. Go to 'Maintenance' -> 'Equipments' and create a new equipment or select an already existing one
#. You will be able to select the mail template you previously created as 'Equipment Scrap Template Email' (for new equipments, the one selected in the settings will be automatically proposed)

Usage
=====

If you want to set a relationship between an equipment and an asset, you need to:

#. Go to 'Maintenance' -> 'Equipments' and create a new equipment or select an already existing one
#. Select an asset in the new 'Asset' field
OR
#. Go to 'Accounting' -> 'Adviser' -> 'Assets' and create a new asset or select an already existing one
#. Select an equipment in the new 'Equipment' field

Notice that, whatever path you choose, you will have a two-ways relationship (you'll find the asset on the equipment and the equipment on the asset)

If you want to scrap an equipment, you need to:

#. Go to 'Maintenance' -> 'Equipments' and select an already existing equipment
#. Click the button 'Scrap'
#. On the wizard select a date for the field 'Scrap Date' and click 'Scrap'

You will find that the selected date was automatically set to the 'Scrap Date' field of the equipment.
Moreover, if on the equipment an 'Equipment Scrap Template Email' was set, such template was used to generate a message to notify that the equipment was scrapped.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Antonio Esposito <a.esposito@onestein.nl>
* Andrea Stirpe <a.stirpe@onestein.nl>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
