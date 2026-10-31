USE autos_colombia;

ALTER TABLE cells
  MODIFY status ENUM(
    'Disponible',
    'Ocupada',
    'Libre',
    'Ocupado',
    'En mantenimiento'
  ) NOT NULL DEFAULT 'Libre';

UPDATE cells SET status = 'Libre' WHERE status = 'Disponible';
UPDATE cells SET status = 'Ocupado' WHERE status = 'Ocupada';

ALTER TABLE cells
  MODIFY status ENUM('Libre', 'Ocupado', 'En mantenimiento') NOT NULL DEFAULT 'Libre';
