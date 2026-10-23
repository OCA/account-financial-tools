Optional wizard flag to update tax repartition lines in-place when posted move
lines reference them, avoiding the OCA ``(5, 0, 0)`` delete/recreate that
triggers PostgreSQL RESTRICT on ``account_move_line.tax_repartition_line_id``.