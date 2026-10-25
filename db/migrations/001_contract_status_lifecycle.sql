USE autos_colombia;

ALTER TABLE contracts
  ADD COLUMN cancelled_by BIGINT UNSIGNED NULL AFTER expires_on,
  ADD COLUMN cancellation_justification VARCHAR(1000) NULL AFTER cancelled_by,
  ADD COLUMN cancelled_at DATETIME(6) NULL AFTER cancellation_justification,
  ADD CONSTRAINT fk_contracts_cancelled_by
    FOREIGN KEY (cancelled_by) REFERENCES users(id);
