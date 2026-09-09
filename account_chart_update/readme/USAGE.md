The wizard, accesible from *Accounting \> Settings \> Update Chart
Template*, lets the user select what kind of objects must be
checked/updated, and whether old records must be checked for changes and
updates.

It will display all the objects to be created / updated / deactivated
with some information about the detected differences, and allow the user
to exclude records individually.

In *General options*, *Continue on errors* tells the wizard what to do
when the chart template cannot be applied completely, typically because
it references a record that does not exist in the company. Left unset
(the default), the update is aborted and nothing is changed, and the
problems found are shown in the error message. Set, the changes that
could be applied are kept, and the problems are reported in the log of
the last step.

In *Field options \> Taxes*, *Update tax accounts* and *Update tax tags*
control whether the account and the tags of the existing tax repartition
lines are overwritten with the ones of the template. Uncheck them to
keep values that were set manually on those lines; the taxes are then
not even reported as different when that is the only change.
