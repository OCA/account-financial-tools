14.0.1.0.0 (2021-01-08)
~~~~~~~~~~~~~~~~~~~~~~~

 * [BREAKING] Removed all functionality associated with `account.fiscal.year`

13.0.2.0.0 (2021-02-19)
~~~~~~~~~~~~~~~~~~~~~~~

* Add support for multi-company

13.0.1.0.0 (2019-10-21)
~~~~~~~~~~~~~~~~~~~~~~~

* Python code and views were adapted to be compatible with v13.
* When assets are created through accounting journal items,
  they are created when the journal items is posted.
* When a Bill Invoice is created or modified, at the time it is saved,
  for each line that has an Asset profile and Quantity 'N'
  greater than 1, it will be replaced by 'N' lines identical to it but
  with quantity 1. This was done to maintain the same behavior as in
  the previous version, in which for each asset created there is a
  Journal Item. In addition, this solution does not change the data
  model which does not cause migration scripts.
* The configuration option was removed so the only function of that is to
  allow the module to be uninstalled by unchecking that configuration option.
* Tests were adapted.

12.0.2.1.0 (2019-10-21)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Add option to calculate depreciation table by days

12.0.1.0.0 (2019-01-13)
~~~~~~~~~~~~~~~~~~~~~~~

* [BREAKING] account.asset: parent_path has replaced parent_left & parent_right (TODO: migration script)
* [BREAKING] account.asset.recompute.trigger: depends on date_range.py (TODO: re-implement in account_fiscal_year.py)
