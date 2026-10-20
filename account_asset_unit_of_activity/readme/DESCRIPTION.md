This module adds a new depreciation method on asset profiles: **Unit of
Activity**.

With this method, the depreciation board is not computed automatically by
Odoo. The depreciation lines are created manually each time the asset is used,
through the *Add Unit of Activity* button available on the asset form.

For each usage, the user enters a quantity and the depreciation amount is
computed as:

    depreciation base / total number of use * quantity
