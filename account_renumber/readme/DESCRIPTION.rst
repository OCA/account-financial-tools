This module extends the functionality of accounting to allow the accounting
manager to renumber account moves by date only for admin.

The wizard, which is accesible from the "End of Period" menuitem,
lets you select journals, periods, and a starting number. When
launched, it renumbers all posted moves that match selected criteria
(after ordering them by date).

It will recreate the sequence number for each account move
using its journal sequence, which means that:

- Sequences per journal are supported.
- Sequences with prefixes and suffixes based on the move date are also
  supported.
