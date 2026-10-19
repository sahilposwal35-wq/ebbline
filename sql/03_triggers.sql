-- Ebbline Database Triggers
-- Engine: MySQL 8.0 or later

DELIMITER //

-- Trigger 1: trg_change_no_overlap_insert
-- Purpose: Prevents overlapping scenario changes on the same target in the same scenario (BR6).
-- Touching ranges (same end and start date) are considered overlapping.
DROP TRIGGER IF EXISTS trg_change_no_overlap_insert//
CREATE TRIGGER trg_change_no_overlap_insert
BEFORE INSERT ON scenario_change
FOR EACH ROW
BEGIN
    -- Check Baseline protection (BR: Scenario 1 Baseline cannot be modified)
    IF NEW.scenario_id = 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Changes on Baseline scenario are not allowed',
                MYSQL_ERRNO = 45006;
    END IF;

    -- Check date range validity
    IF NEW.to_date < NEW.from_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Scenario change to_date cannot be earlier than from_date',
                MYSQL_ERRNO = 45005;
    END IF;

    -- Check overlap with existing changes for the same scenario and target
    IF EXISTS (
        SELECT 1 FROM scenario_change c
        WHERE c.scenario_id = NEW.scenario_id
          AND c.rule_id <=> NEW.rule_id
          AND c.event_id <=> NEW.event_id
          AND c.from_date <= NEW.to_date
          AND c.to_date >= NEW.from_date
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Overlapping scenario change for this target',
                MYSQL_ERRNO = 45005;
    END IF;
END//

-- Trigger 2: trg_change_no_overlap_update
-- Purpose: Prevents overlapping scenario changes upon UPDATE.
DROP TRIGGER IF EXISTS trg_change_no_overlap_update//
CREATE TRIGGER trg_change_no_overlap_update
BEFORE UPDATE ON scenario_change
FOR EACH ROW
BEGIN
    IF NEW.scenario_id = 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Changes on Baseline scenario are not allowed',
                MYSQL_ERRNO = 45006;
    END IF;

    IF NEW.to_date < NEW.from_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Scenario change to_date cannot be earlier than from_date',
                MYSQL_ERRNO = 45005;
    END IF;

    IF EXISTS (
        SELECT 1 FROM scenario_change c
        WHERE c.change_id <> NEW.change_id
          AND c.scenario_id = NEW.scenario_id
          AND c.rule_id <=> NEW.rule_id
          AND c.event_id <=> NEW.event_id
          AND c.from_date <= NEW.to_date
          AND c.to_date >= NEW.from_date
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Overlapping scenario change for this target',
                MYSQL_ERRNO = 45005;
    END IF;
END//

-- Trigger 3: trg_rule_history
-- Purpose: Records audit trail of changes to recurring rules (Could feature F18, T30).
DROP TRIGGER IF EXISTS trg_rule_history//
CREATE TRIGGER trg_rule_history
AFTER UPDATE ON recurring_rule
FOR EACH ROW
BEGIN
    IF (OLD.amount <> NEW.amount) OR 
       (OLD.start_date <> NEW.start_date) OR 
       (OLD.end_date <=> NEW.end_date) = 0 OR 
       (OLD.is_active <> NEW.is_active) THEN
        INSERT INTO rule_history (
            rule_id, changed_at,
            old_amount, new_amount,
            old_start, new_start,
            old_end, new_end,
            old_active, new_active
        ) VALUES (
            NEW.rule_id, CURRENT_TIMESTAMP,
            OLD.amount, NEW.amount,
            OLD.start_date, NEW.start_date,
            OLD.end_date, NEW.end_date,
            OLD.is_active, NEW.is_active
        );
    END IF;
END//

DELIMITER ;
