-- Ebbline Stored Procedures
-- Engine: MySQL 8.0 or later

DELIMITER //

-- Procedure: add_checkpoint
-- Purpose: Records a known real balance for an account as of a date.
-- Business rule: Checkpoints in the future are rejected with error 45004.
DROP PROCEDURE IF EXISTS add_checkpoint//
CREATE PROCEDURE add_checkpoint(
    IN p_account_id INT,
    IN p_as_of_date DATE,
    IN p_balance DECIMAL(12,2)
)
BEGIN
    IF p_as_of_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Checkpoints cannot be in the future',
                MYSQL_ERRNO = 45004;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM account WHERE account_id = p_account_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Account does not exist',
                MYSQL_ERRNO = 45002;
    END IF;

    INSERT INTO balance_checkpoint (account_id, as_of_date, balance)
    VALUES (p_account_id, p_as_of_date, p_balance)
    ON DUPLICATE KEY UPDATE balance = VALUES(balance);
END//

DELIMITER ;
