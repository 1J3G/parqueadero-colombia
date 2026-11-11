USE autos_colombia;

ALTER TABLE contracts
  ADD COLUMN starts_on DATE NULL AFTER status;

UPDATE contracts c
JOIN (
  SELECT contract_id, MIN(DATE(created_at)) AS starts_on
  FROM payments
  WHERE status = 'Registrado'
  GROUP BY contract_id
) p ON p.contract_id = c.id
SET c.starts_on = p.starts_on;

UPDATE contracts
SET starts_on = DATE(created_at)
WHERE starts_on IS NULL
  AND expires_on IS NOT NULL;
