This module provides a wizard to post many Journal Entries in batch. it
uses the queue system introduced by the Odoo Queue job module to handle a
big quantity of moves in batch.

The posting of a move takes some time, and doing that synchronously,
in one transaction is problematic.

In this module, we leverage the power of the queue system of the
Odoo queue job module, that can be very well used without other concepts
like Backends and Bindings.

This approach provides many advantages, similar to the ones we get
using that connector for e-commerce:

- Asynchronous: the operation is done in background, and users can
  continue to work.
- Dedicated workers: the queued jobs are performed by specific workers
  (processes). This is good for a long task, since the main workers are
  busy handling HTTP requests and can be killed if operations take
  too long, for example.
- Multiple transactions: this is an operation that doesn't need to be
  atomic, and if a line out of 100,000 fails, it is possible to catch
  it, see the error message, and fix the situation. Meanwhile, all
  other jobs can proceed.
