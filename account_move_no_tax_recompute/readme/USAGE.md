1.  Open a journal entry in draft mode.
2.  Go to *Other Info*.
3.  Enable *No Recompute Taxes*.
4.  Edit journal items as needed.
5.  Save the entry.

Once enabled, the dynamic tax synchronization logic is skipped for that
journal entry, preventing automatic tax line recomputation.

Notes:

- This option is designed for manual accounting scenarios.
- It is only effective on entries with `move_type = 'entry'`.
- Use it carefully, as tax consistency checks are no longer
  automatically enforced by dynamic synchronization for the entry.
