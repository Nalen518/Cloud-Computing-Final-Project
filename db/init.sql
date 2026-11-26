-- Runs once, when the MySQL data volume is first created.
CREATE TABLE IF NOT EXISTS items (
  item_id       CHAR(36)     NOT NULL PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  folder        VARCHAR(50)  NOT NULL DEFAULT 'Unsorted',
  quantity      INT UNSIGNED NOT NULL,
  unit          VARCHAR(20)  NOT NULL,
  reorder_level INT UNSIGNED NOT NULL,
  created_at    DATETIME     NOT NULL,
  updated_at    DATETIME     NOT NULL
);
