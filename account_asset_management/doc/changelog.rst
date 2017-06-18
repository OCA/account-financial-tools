.. _changelog:

Changelog
=========

`V2.0`
------

Enhancements/changes made by Noviat (www.noviat.com)

- New Time Method: Number of Years

- New Computation Method: Degressive-Linear

- Fiscal Year based depreciation table calculation.

   The table calculation logic has been rewritten:
   - The calculation takes into account fiscal year start/stop dates.
     Fiscal year start/stop dates can be different from calendar year start/stop dates.
     Also extended/shortened fiscal years are supported.
   - The first entry will contain the Year-To-Date depreciation amount.
   - The depreciation table is calculated in 2 steps:
     - Step 1: calculate the amount for the fiscal years.
     - Step 2: spread this amount over the fiscal year according to the selected depreciation period duration.
   - Rounding deviations caused by the cost spreading over the fiscal are compensated as follows:
     - year 1: compensation on the first depreciation date
     - others years: compensation on the last depreciation date of the fiscal year.
   - Fiscal year dates and duration are not known yet at the time of asset creation.
     The initial depreciation table calculation assumes undefined fiscal years to be equal to a calendar year.
     Fiscal year duration changes are automatically taken into account by recomputing the depreciation table when running the periodical asset posting wizard.
   - Depreciation dates are always equal to the last date of a Fiscal Year/Quarter/Month.

- Time Methods

   The Time Method 'Number of Years' should be used for Financial Assets.
   
   The Time Methods 'Ending Date' and 'Number of Depreciations' have been adapted for Deferred Cost/Income and Cost/Income Spreading purposes.
   As a consequence, the calculation is always 'pro rata' for these Time Methods and the 'Set to Removed' button is not available. 

- Accounting entry corrections
   Negative depreciation amounts are correctly handled (e.g. to compensate for excessive depreciation in case of period duration change).

- Foreign currency support

   Purchases in foreign currency are converted to company currency using the exchange rate at the purchase date.
   The depreciation table is calculated in company currency. 

- The 'Journal Entries' button now opens a list view of the 'Journal Entries'. 

   The 'Journal Items' remain available via the 'Journal Items' link and the History tab.

- An extra button is added to the depreciation lines to facilitate the access to the accounting entry associated with a depreciation line.

- The Accounting Entry Reference field can be customised via the '_get_depreciation_entry_name' method.

- account.asset.asset,purchase_date (Purchase Date) field renamed to date_start (Depreciation Start Date), since an asset can be composed of different purchases.

- Assets with accounting entries in previous/closed fy's/periods are supported via 'Initial Balance Entries' in the depreciation table.

- Extra controls have been added to guarantee consistency between depreciation lines amounts and accounting entry values:
    - an accounting entry linked to an asset cannot be changed
    - an asset_id cannot be added to an accounting entry
    - a depreciation line with a linked accounting entry cannot be changed
   

- Depreciation line 'sequence' field removed (replaced by m2o to previous line)

- Database fields replaced by computed fields:
    - account.asset.asset : asset_value
    - account.asset.depreciation.line :  remaining_value, depreciated_value

- parent_id concept has been changed : parent = type 'view'|'normal'. Hierarchy view shows subtotal calculation.

- new (calculated) asset field 'value_depreciated', UI (form, list, hierarchy) adapted to show fields value, depreciated, remaining

- new field on account.account : asset_category_id used as default asset category on sale invoice invoice line with asset account

- Support the Purchase Journal 'Group Invoice Lines' option

- account.asset.depreciation.line renamed to account.asset.line with types 'create'|'depreciate'|'dispose' since this table is now used to track the complete lifecycle of an asset.

- 'Remove' button to generate the asset removal accounting moves.

- Extra security
    - 'Set to Draft' button reserved for users of the 'Accounting & Finance / Manager' group.
    - 'Asset Removal' button reserved for users of the 'Accounting & Finance / Manager' group.
    - 'Remove accounting entry' button reserved for users of the 'Accounting & Finance / Manager' group.

- Fixes for Time Methods 'Number of Depreciations' and 'Ending Date'
    - Pro Rata Temporis: include asset start date in number of days for first depreciation
    - Fix logic for recompute of table with posted entries
    - Fix rounding errors in depreciation table computation

- Selection lists for fields 'method' and 'method_time' have been moved to object methods so that they can be modified in an inherited module.

- Migration code has been added to upgrade asset database tables via the standard module upgrade process.

`V2.1`
------

Enhancements/changes made by Noviat (www.noviat.com)

- Support assets without depreciation table (e.g. properties that keep their value). Specify 'method_number' = 0 for such assets.

`V2.2`
------

Enhancements/changes

- Generation of accounting entries in case of early removal.

`V3.0`
------

A summary of the main changes

- Major performance boost primarily by removing the calculated fields on the 'view' assets.

- Performance optimisation in the 'recompute trigger'.
  Recomputes are now limited to changes in fiscal year duration.
 
- Code refactoring : OCA guidelines compliancy, new api, removal of all "cr.execute"

- Cost/Revenue Spreading now possible via the new add-on module 'account_asset_management_method_number_end'.
  This module enables the Time Methods 'Number' and 'End'.
  The logic for these time methods is included in the 'account_asset_management' module (as it was before)
  but a number of bugs for these time methods have now been made and tests suites are added for these methods.

- New Computation Methods : linear-limit and degressive-limit.
  As a consequence we now support the 'double-declining-balance depreciation'.
  Tests are added to ensure that this depreciation method will not be broken in the future.

 - Tests have been added to cover quarterly depreciations.

- Rounding errors are now consistently adjusted at the last posting date of the fiscal year.
  Incorrect postings via uploading historical depreciations in 'init' entries are now always adjusted in the first unposted entry.

- Tests have also been added to the account_asset_management_xls module.

- Table renames to avoid technical conflicts with the standard addons 'account_asset' module.
