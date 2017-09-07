.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================
Account Renumber Options
========================

* New option in Account Setting Configuration, Renumber by period, this 
  field will be activated by default. When it is activated, the renumber 
  wizard will work as always. In the other hand if the check is not activated,
  the renumber wizard will not take into account the account move periods, 
  so the renumbering will be processed only by date. 

* In the renumber wizard, the secuence assignment is the same as in the base 
  process, so if the sequence is defined as "No gap" and there are gaps in 
  previous moves, is possible that the final moves sequences are not concurrent
  because some moves will be used to fill the gaps.

Usage
=====

New "Renumber by period" configuration field in *Configuration > Configuration > Account Setting Configuration 

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/account_financial_tools/8.0

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

For further information, please visit:

* https://www.odoo.com/forum/help-1


Known Issues
============

This module uses the Python *csv* module for the reading of the input csv file.
The input csv file should take into account the limitations of the *csv* module:

Unicode input is not supported. Also, there are some issues regarding ASCII NUL characters.
Accordingly, all input should be UTF-8 or printable ASCII.
Results are unpredictable when this is not the case.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------
* Ainara Galdona <ainaragaldona@avanzosc.es>
* Ana Juaristi <anajuaristi@avanzosc.es>

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
