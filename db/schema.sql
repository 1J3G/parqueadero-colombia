CREATE DATABASE IF NOT EXISTS autos_colombia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE autos_colombia;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  document VARCHAR(30) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('Operario', 'Administrador') NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  revoked_at DATETIME(6) NULL,
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  document_type ENUM('CC', 'CE', 'NIT') NOT NULL,
  document VARCHAR(30) NOT NULL UNIQUE,
  full_name VARCHAR(160) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  plate VARCHAR(6) NOT NULL UNIQUE,
  vehicle_type ENUM('Carro', 'Moto', 'Camioneta') NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contracts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  customer_id BIGINT UNSIGNED NOT NULL,
  vehicle_id BIGINT UNSIGNED NOT NULL,
  status ENUM('Pendiente de Pago', 'Activo', 'Vencido', 'Cancelado') NOT NULL DEFAULT 'Pendiente de Pago',
  starts_on DATE NULL,
  expires_on DATE NULL,
  cancelled_by BIGINT UNSIGNED NULL,
  cancellation_justification VARCHAR(1000) NULL,
  cancelled_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_contracts_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
  CONSTRAINT fk_contracts_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
  CONSTRAINT fk_contracts_cancelled_by FOREIGN KEY (cancelled_by) REFERENCES users(id),
  INDEX ix_contracts_vehicle_created (vehicle_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cells (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  label VARCHAR(30) NOT NULL UNIQUE,
  category ENUM('Carro', 'Moto', 'Camioneta', 'Discapacitado') NOT NULL,
  status ENUM('Libre', 'Ocupado', 'En mantenimiento') NOT NULL DEFAULT 'Libre'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cash_openings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  base_amount DECIMAL(12, 2) NOT NULL,
  opened_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  closed_at DATETIME(6) NULL,
  CONSTRAINT fk_cash_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX ix_cash_user_open (user_id, closed_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transits (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  vehicle_id BIGINT UNSIGNED NOT NULL,
  contract_id BIGINT UNSIGNED NOT NULL,
  cell_id BIGINT UNSIGNED NOT NULL,
  operator_id BIGINT UNSIGNED NOT NULL,
  direction ENUM('Entrada', 'Salida') NOT NULL,
  occurred_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_transits_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
  CONSTRAINT fk_transits_contract FOREIGN KEY (contract_id) REFERENCES contracts(id),
  CONSTRAINT fk_transits_cell FOREIGN KEY (cell_id) REFERENCES cells(id),
  CONSTRAINT fk_transits_operator FOREIGN KEY (operator_id) REFERENCES users(id),
  INDEX ix_transits_vehicle_time (vehicle_id, occurred_at, id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS novelties (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  transit_id BIGINT UNSIGNED NOT NULL,
  novelty_type ENUM('Daño físico', 'Acceso excepcional') NOT NULL,
  damage_type ENUM('Golpe', 'Rayón', 'Falla') NULL,
  description VARCHAR(1000) NOT NULL,
  severity ENUM('Leve', 'Moderada', 'Grave') NULL,
  recorded_by BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_novelties_transit FOREIGN KEY (transit_id) REFERENCES transits(id),
  CONSTRAINT fk_novelties_user FOREIGN KEY (recorded_by) REFERENCES users(id),
  INDEX ix_novelties_transit (transit_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  contract_id BIGINT UNSIGNED NOT NULL,
  cash_opening_id BIGINT UNSIGNED NOT NULL,
  operator_id BIGINT UNSIGNED NOT NULL,
  net_amount DECIMAL(12, 2) NOT NULL,
  tax_amount DECIMAL(12, 2) NOT NULL,
  total_amount DECIMAL(12, 2) NOT NULL,
  paid_months INT UNSIGNED NOT NULL,
  payment_method ENUM('Efectivo', 'Transferencia Bancaria', 'Tarjeta Crédito/Débito') NOT NULL,
  reference_code VARCHAR(120) NULL,
  status ENUM('Registrado', 'Anulado') NOT NULL DEFAULT 'Registrado',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_payments_contract FOREIGN KEY (contract_id) REFERENCES contracts(id),
  CONSTRAINT fk_payments_cash FOREIGN KEY (cash_opening_id) REFERENCES cash_openings(id),
  CONSTRAINT fk_payments_operator FOREIGN KEY (operator_id) REFERENCES users(id),
  INDEX ix_payments_contract_created (contract_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS receipt_counters (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  last_number BIGINT UNSIGNED NOT NULL
) ENGINE=InnoDB;

INSERT IGNORE INTO receipt_counters (id, last_number) VALUES (1, 0);

CREATE TABLE IF NOT EXISTS receipts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  payment_id BIGINT UNSIGNED NOT NULL UNIQUE,
  consecutive_number BIGINT UNSIGNED NOT NULL UNIQUE,
  customer_document_type ENUM('CC', 'CE', 'NIT') NOT NULL,
  customer_document VARCHAR(30) NOT NULL,
  customer_full_name VARCHAR(160) NOT NULL,
  net_amount DECIMAL(12, 2) NOT NULL,
  tax_amount DECIMAL(12, 2) NOT NULL,
  total_amount DECIMAL(12, 2) NOT NULL,
  issued_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_receipts_payment FOREIGN KEY (payment_id) REFERENCES payments(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment_audit (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  payment_id BIGINT UNSIGNED NOT NULL,
  administrator_id BIGINT UNSIGNED NOT NULL,
  justification VARCHAR(1000) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_payment_audit_payment FOREIGN KEY (payment_id) REFERENCES payments(id),
  CONSTRAINT fk_payment_audit_admin FOREIGN KEY (administrator_id) REFERENCES users(id)
) ENGINE=InnoDB;

DELIMITER //

DROP TRIGGER IF EXISTS prevent_transit_update//
CREATE TRIGGER prevent_transit_update
BEFORE UPDATE ON transits
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transit records are immutable';
END//

DROP TRIGGER IF EXISTS validate_novelty_insert//
CREATE TRIGGER validate_novelty_insert
BEFORE INSERT ON novelties
FOR EACH ROW
BEGIN
  IF NEW.novelty_type = 'Daño físico'
     AND (NEW.damage_type IS NULL OR NEW.severity IS NULL OR CHAR_LENGTH(TRIM(NEW.description)) = 0) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Physical novelties require a type, description and severity';
  END IF;
  IF NEW.novelty_type = 'Acceso excepcional'
     AND (NEW.damage_type IS NOT NULL OR NEW.severity IS NOT NULL OR CHAR_LENGTH(TRIM(NEW.description)) = 0) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Exceptional access novelties require only a description';
  END IF;
END//

DROP TRIGGER IF EXISTS validate_payment_insert//
CREATE TRIGGER validate_payment_insert
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
  IF NEW.net_amount <= 0 OR NEW.paid_months = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment amount and paid months must be positive';
  END IF;
  IF NEW.payment_method = 'Transferencia Bancaria'
     AND (NEW.reference_code IS NULL OR CHAR_LENGTH(TRIM(NEW.reference_code)) = 0) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bank transfers require a reference';
  END IF;
END//

DROP TRIGGER IF EXISTS prevent_transit_delete//
CREATE TRIGGER prevent_transit_delete
BEFORE DELETE ON transits
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Transit records are immutable';
END//

DROP TRIGGER IF EXISTS prevent_novelty_update//
CREATE TRIGGER prevent_novelty_update
BEFORE UPDATE ON novelties
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Novelty records are immutable';
END//

DROP TRIGGER IF EXISTS prevent_novelty_delete//
CREATE TRIGGER prevent_novelty_delete
BEFORE DELETE ON novelties
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Novelty records are immutable';
END//

DROP TRIGGER IF EXISTS prevent_payment_delete//
CREATE TRIGGER prevent_payment_delete
BEFORE DELETE ON payments
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payments cannot be deleted';
END//

DELIMITER ;
