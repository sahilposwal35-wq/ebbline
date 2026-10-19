-- Ebbline Core Schema Definition
-- Engine: MySQL 8.0 or later (InnoDB, utf8mb4)

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS projection_event;
DROP TABLE IF EXISTS projection_day;
DROP TABLE IF EXISTS projection_run;
DROP TABLE IF EXISTS actual_txn;
DROP TABLE IF EXISTS scenario_change;
DROP TABLE IF EXISTS scenario;
DROP TABLE IF EXISTS rule_history;
DROP TABLE IF EXISTS recurring_rule;
DROP TABLE IF EXISTS one_off_event;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS balance_checkpoint;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS calendar_day;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Account table
CREATE TABLE account (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE,
    account_type ENUM('SAVINGS', 'CURRENT', 'WALLET', 'CASH') NOT NULL,
    buffer_min DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_account_buffer CHECK (buffer_min >= 0.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Balance checkpoint table
CREATE TABLE balance_checkpoint (
    checkpoint_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    as_of_date DATE NOT NULL,
    balance DECIMAL(12,2) NOT NULL,
    CONSTRAINT uq_checkpoint_account_date UNIQUE (account_id, as_of_date),
    CONSTRAINT fk_checkpoint_account FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Category table
CREATE TABLE category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE,
    is_essential BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Recurring rule table
CREATE TABLE recurring_rule (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    category_id INT NOT NULL,
    label VARCHAR(80) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    unit ENUM('WEEK', 'MONTH') NOT NULL,
    every_n TINYINT UNSIGNED NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_rule_amount CHECK (amount <> 0.00),
    CONSTRAINT ck_rule_every CHECK (every_n >= 1),
    CONSTRAINT ck_rule_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT fk_rule_account FOREIGN KEY (account_id) REFERENCES account(account_id),
    CONSTRAINT fk_rule_category FOREIGN KEY (category_id) REFERENCES category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. One off event table
CREATE TABLE one_off_event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    category_id INT NOT NULL,
    event_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    label VARCHAR(80) NOT NULL,
    CONSTRAINT ck_event_amount CHECK (amount <> 0.00),
    CONSTRAINT fk_event_account FOREIGN KEY (account_id) REFERENCES account(account_id),
    CONSTRAINT fk_event_category FOREIGN KEY (category_id) REFERENCES category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Scenario table
CREATE TABLE scenario (
    scenario_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Scenario change table
CREATE TABLE scenario_change (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    rule_id INT NULL,
    event_id INT NULL,
    action ENUM('SKIP', 'SHIFT_DAYS', 'SCALE') NOT NULL,
    value DECIMAL(10,2) NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    CONSTRAINT ck_change_target CHECK ((rule_id IS NULL) <> (event_id IS NULL)),
    CONSTRAINT ck_change_range CHECK (to_date >= from_date),
    CONSTRAINT ck_change_value CHECK (action = 'SKIP' OR value IS NOT NULL),
    CONSTRAINT fk_change_scenario FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    CONSTRAINT fk_change_rule FOREIGN KEY (rule_id) REFERENCES recurring_rule(rule_id),
    CONSTRAINT fk_change_event FOREIGN KEY (event_id) REFERENCES one_off_event(event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Actual transaction table
CREATE TABLE actual_txn (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    txn_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    label VARCHAR(80) NULL,
    rule_id INT NULL,
    event_id INT NULL,
    source_hash CHAR(64) NULL UNIQUE,
    CONSTRAINT fk_actual_account FOREIGN KEY (account_id) REFERENCES account(account_id),
    CONSTRAINT fk_actual_rule FOREIGN KEY (rule_id) REFERENCES recurring_rule(rule_id),
    CONSTRAINT fk_actual_event FOREIGN KEY (event_id) REFERENCES one_off_event(event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Projection run header table
CREATE TABLE projection_run (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    account_id INT NOT NULL,
    horizon_start DATE NOT NULL,
    horizon_end DATE NOT NULL,
    anchor_date DATE NOT NULL,
    anchor_balance DECIMAL(12,2) NOT NULL,
    min_balance DECIMAL(12,2) NULL,
    min_balance_date DATE NULL,
    first_breach_date DATE NULL,
    days_below_buffer INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_run_horizon CHECK (horizon_end > horizon_start),
    CONSTRAINT fk_run_scenario FOREIGN KEY (scenario_id) REFERENCES scenario(scenario_id) ON DELETE CASCADE,
    CONSTRAINT fk_run_account FOREIGN KEY (account_id) REFERENCES account(account_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Projection day table
CREATE TABLE projection_day (
    run_id INT NOT NULL,
    day DATE NOT NULL,
    net DECIMAL(12,2) NOT NULL,
    balance DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (run_id, day),
    CONSTRAINT fk_day_run FOREIGN KEY (run_id) REFERENCES projection_run(run_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Projection event table
CREATE TABLE projection_event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    due_date DATE NOT NULL,
    source_type ENUM('RULE', 'EVENT') NOT NULL,
    source_id INT NOT NULL,
    label VARCHAR(80) NOT NULL,
    category_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    INDEX idx_proj_event_run_date (run_id, due_date),
    CONSTRAINT fk_proj_event_run FOREIGN KEY (run_id) REFERENCES projection_run(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_proj_event_category FOREIGN KEY (category_id) REFERENCES category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Rule history table
CREATE TABLE rule_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_amount DECIMAL(12,2) NULL,
    new_amount DECIMAL(12,2) NULL,
    old_start DATE NULL,
    new_start DATE NULL,
    old_end DATE NULL,
    new_end DATE NULL,
    old_active BOOLEAN NULL,
    new_active BOOLEAN NULL,
    CONSTRAINT fk_history_rule FOREIGN KEY (rule_id) REFERENCES recurring_rule(rule_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Calendar day table
CREATE TABLE calendar_day (
    day DATE NOT NULL PRIMARY KEY
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Base seed: Baseline scenario
INSERT INTO scenario (scenario_id, name, description)
VALUES (1, 'Baseline', 'Default baseline plan without what-if overrides')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Base seed: Core categories
INSERT INTO category (category_id, name, is_essential) VALUES
(1, 'Salary and Income', TRUE),
(2, 'Housing and Rent', TRUE),
(3, 'Utilities and Bills', TRUE),
(4, 'Groceries', TRUE),
(5, 'Loan EMIs', TRUE),
(6, 'Insurance', TRUE),
(7, 'Investments and SIPs', TRUE),
(8, 'Subscriptions', FALSE),
(9, 'Dining and Leisure', FALSE),
(10, 'Shopping', FALSE)
ON DUPLICATE KEY UPDATE name = VALUES(name), is_essential = VALUES(is_essential);
