.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

========================
Currency rate date check
========================

This module adds a check on dates when doing currency conversion in Odoo.
It checks that the currency rate used to make the conversion
is not more than N days away from the date of the amount to convert.

The maximum number of days of the interval can be
configured on the company form.

On invoice, for example, rate date check can block validation if nearset date rate is older than number of days configured on company. 

.. figure:: currency_rate_date_check/static/description/date_check_error_popup.jpg
    :width: 600 px
    :alt: Date check error popup

Configuration
=============

To configure this module, you need to:

#. Go to ...

Company views form and set 

.. figure:: currency_rate_date_check/static/description/date_check_company_config.jpg
    :width: 600 px
    :alt: Config date check on company


Usage
=====

To use this module, you need to:

#. Go to ...

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. 
In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>
* Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>

Do not contact contributors directly about support or help with technical issues.

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
