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

-- Procedure: build_projection
-- Purpose: Generates a complete daily balance projection for an account and scenario over a specified horizon.
-- Runs in a single atomic transaction. Rolls back completely on any error.
DROP PROCEDURE IF EXISTS build_projection//
CREATE PROCEDURE build_projection(
    IN p_scenario_id INT,
    IN p_account_id INT,
    IN p_horizon_days INT,
    OUT p_run_id INT
)
proc_block: BEGIN
    DECLARE v_anchor_date DATE;
    DECLARE v_anchor_balance DECIMAL(12,2);
    DECLARE v_start_date DATE;
    DECLARE v_end_date DATE;
    DECLARE v_buffer_min DECIMAL(12,2);
    DECLARE v_min_balance DECIMAL(12,2);
    DECLARE v_min_balance_date DATE;
    DECLARE v_first_breach_date DATE;
    DECLARE v_days_below_buffer INT;

    -- Exit handler for transaction rollback
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        DROP TEMPORARY TABLE IF EXISTS tmp_occ;
        DROP TEMPORARY TABLE IF EXISTS tmp_net;
        RESIGNAL;
    END;

    -- Step 1: Input Validation
    IF NOT EXISTS (SELECT 1 FROM account WHERE account_id = p_account_id AND is_active = TRUE) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Account is inactive or does not exist',
                MYSQL_ERRNO = 45002;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM scenario WHERE scenario_id = p_scenario_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Scenario does not exist',
                MYSQL_ERRNO = 45006;
    END IF;

    IF p_horizon_days < 1 OR p_horizon_days > 730 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Horizon must be between 1 and 730 days',
                MYSQL_ERRNO = 45003;
    END IF;

    -- Step 2: Start Transaction
    START TRANSACTION;

    -- Step 3: Find anchor checkpoint (latest checkpoint on or before CURDATE)
    SELECT as_of_date, balance
    INTO v_anchor_date, v_anchor_balance
    FROM balance_checkpoint
    WHERE account_id = p_account_id AND as_of_date <= CURDATE()
    ORDER BY as_of_date DESC
    LIMIT 1;

    IF v_anchor_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No valid checkpoint found for this account on or before today',
                MYSQL_ERRNO = 45001;
    END IF;

    -- Projection starts the day after the anchor checkpoint (Decision D8)
    SET v_start_date = DATE_ADD(v_anchor_date, INTERVAL 1 DAY);
    SET v_end_date = DATE_ADD(v_start_date, INTERVAL (p_horizon_days - 1) DAY);

    -- Step 4: Expand occurrences into temporary table
    DROP TEMPORARY TABLE IF EXISTS tmp_occ;
    CREATE TEMPORARY TABLE tmp_occ (
        temp_id INT AUTO_INCREMENT PRIMARY KEY,
        source_type ENUM('RULE', 'EVENT') NOT NULL,
        source_id INT NOT NULL,
        account_id INT NOT NULL,
        category_id INT NOT NULL,
        label VARCHAR(80) NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        due_date DATE NOT NULL
    );

    INSERT INTO tmp_occ (source_type, source_id, account_id, category_id, label, amount, due_date)
    SELECT source_type, source_id, account_id, category_id, label, amount, due_date
    FROM v_rule_occurrence
    WHERE account_id = p_account_id
      AND due_date BETWEEN DATE_SUB(v_start_date, INTERVAL 90 DAY) AND DATE_ADD(v_end_date, INTERVAL 90 DAY)
    UNION ALL
    SELECT 'EVENT', event_id, account_id, category_id, label, amount, event_date
    FROM one_off_event
    WHERE account_id = p_account_id
      AND event_date BETWEEN DATE_SUB(v_start_date, INTERVAL 90 DAY) AND DATE_ADD(v_end_date, INTERVAL 90 DAY);

    -- Step 5: Apply scenario changes if not baseline (Order: SKIP, then SHIFT_DAYS, then SCALE)
    IF p_scenario_id <> 1 THEN
        -- 5a. SKIP
        DELETE o FROM tmp_occ o
        JOIN scenario_change sc ON sc.scenario_id = p_scenario_id AND sc.action = 'SKIP'
          AND ((o.source_type = 'RULE' AND o.source_id = sc.rule_id) OR (o.source_type = 'EVENT' AND o.source_id = sc.event_id))
          AND o.due_date BETWEEN sc.from_date AND sc.to_date;

        -- 5b. SHIFT_DAYS
        UPDATE tmp_occ o
        JOIN scenario_change sc ON sc.scenario_id = p_scenario_id AND sc.action = 'SHIFT_DAYS'
          AND ((o.source_type = 'RULE' AND o.source_id = sc.rule_id) OR (o.source_type = 'EVENT' AND o.source_id = sc.event_id))
          AND o.due_date BETWEEN sc.from_date AND sc.to_date
        SET o.due_date = DATE_ADD(o.due_date, INTERVAL CAST(sc.value AS SIGNED) DAY);

        -- 5c. SCALE (Round to 2 decimals once - Decision D9)
        UPDATE tmp_occ o
        JOIN scenario_change sc ON sc.scenario_id = p_scenario_id AND sc.action = 'SCALE'
          AND ((o.source_type = 'RULE' AND o.source_id = sc.rule_id) OR (o.source_type = 'EVENT' AND o.source_id = sc.event_id))
          AND o.due_date BETWEEN sc.from_date AND sc.to_date
        SET o.amount = ROUND(o.amount * sc.value, 2);
    END IF;

    -- Retain only occurrences within the projection horizon
    DELETE FROM tmp_occ WHERE due_date < v_start_date OR due_date > v_end_date;

    -- Step 6: Aggregate daily net into tmp_net
    DROP TEMPORARY TABLE IF EXISTS tmp_net;
    CREATE TEMPORARY TABLE tmp_net (
        day DATE NOT NULL PRIMARY KEY,
        net DECIMAL(12,2) NOT NULL
    );

    INSERT INTO tmp_net (day, net)
    SELECT cd.day, COALESCE(SUM(o.amount), 0.00) AS net
    FROM calendar_day cd
    LEFT JOIN tmp_occ o ON o.due_date = cd.day
    WHERE cd.day BETWEEN v_start_date AND v_end_date
    GROUP BY cd.day;

    -- Step 7: Insert projection_run header
    INSERT INTO projection_run (
        scenario_id, account_id, horizon_start, horizon_end,
        anchor_date, anchor_balance, min_balance, min_balance_date,
        first_breach_date, days_below_buffer
    ) VALUES (
        p_scenario_id, p_account_id, v_start_date, v_end_date,
        v_anchor_date, v_anchor_balance, NULL, NULL, NULL, 0
    );
    SET p_run_id = LAST_INSERT_ID();

    -- Step 8: Insert projection_event rows
    INSERT INTO projection_event (
        run_id, due_date, source_type, source_id, label, category_id, amount
    )
    SELECT 
        p_run_id, due_date, source_type, source_id, label, category_id, amount
    FROM tmp_occ
    ORDER BY due_date, source_type, source_id;

    -- Step 9: Insert projection_day with running balance
    INSERT INTO projection_day (run_id, day, net, balance)
    SELECT 
        p_run_id,
        tn.day,
        tn.net,
        v_anchor_balance + SUM(tn.net) OVER (
            ORDER BY tn.day 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS balance
    FROM tmp_net tn
    ORDER BY tn.day;

    -- Step 10: Update header with lowest balance, first breach date, and days below buffer
    SELECT buffer_min INTO v_buffer_min FROM account WHERE account_id = p_account_id;

    SELECT 
        MIN(balance),
        MIN(CASE WHEN balance < v_buffer_min THEN day END),
        SUM(CASE WHEN balance < v_buffer_min THEN 1 ELSE 0 END)
    INTO v_min_balance, v_first_breach_date, v_days_below_buffer
    FROM projection_day
    WHERE run_id = p_run_id;

    SELECT day INTO v_min_balance_date
    FROM projection_day
    WHERE run_id = p_run_id AND balance = v_min_balance
    ORDER BY day ASC
    LIMIT 1;

    UPDATE projection_run
    SET min_balance = v_min_balance,
        min_balance_date = v_min_balance_date,
        first_breach_date = v_first_breach_date,
        days_below_buffer = v_days_below_buffer
    WHERE run_id = p_run_id;

    -- Step 11: Cleanup temporary tables and commit
    DROP TEMPORARY TABLE IF EXISTS tmp_occ;
    DROP TEMPORARY TABLE IF EXISTS tmp_net;

    COMMIT;
END//

-- Procedure: add_scenario_change
-- Purpose: Adds a scenario override row with parent-row locking to avoid trigger race conditions (Decision D7).
DROP PROCEDURE IF EXISTS add_scenario_change//
CREATE PROCEDURE add_scenario_change(
    IN p_scenario_id INT,
    IN p_rule_id INT,
    IN p_event_id INT,
    IN p_action VARCHAR(20),
    IN p_value DECIMAL(10,2),
    IN p_from_date DATE,
    IN p_to_date DATE,
    OUT p_change_id INT
)
BEGIN
    DECLARE v_parent_id INT;

    START TRANSACTION;

    -- Lock parent scenario row to serialize concurrent inserts for this scenario
    SELECT scenario_id INTO v_parent_id
    FROM scenario
    WHERE scenario_id = p_scenario_id
    FOR UPDATE;

    IF v_parent_id IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Scenario does not exist',
                MYSQL_ERRNO = 45006;
    END IF;

    INSERT INTO scenario_change (
        scenario_id, rule_id, event_id, action, value, from_date, to_date
    ) VALUES (
        p_scenario_id, p_rule_id, p_event_id, p_action, p_value, p_from_date, p_to_date
    );
    SET p_change_id = LAST_INSERT_ID();

    COMMIT;
END//

-- Procedure: compare_scenarios
-- Purpose: Compares two scenarios for an account, returning the difference in minimum balance, breach date, and days below buffer.
-- If no run exists for either scenario, it builds a default 365-day run first.
DROP PROCEDURE IF EXISTS compare_scenarios//
CREATE PROCEDURE compare_scenarios(
    IN p_scenario_a INT,
    IN p_scenario_b INT,
    IN p_account_id INT
)
BEGIN
    DECLARE v_run_a INT;
    DECLARE v_run_b INT;

    -- Ensure run A exists
    SELECT MAX(run_id) INTO v_run_a
    FROM projection_run
    WHERE account_id = p_account_id AND scenario_id = p_scenario_a;

    IF v_run_a IS NULL THEN
        CALL build_projection(p_scenario_a, p_account_id, 365, v_run_a);
    END IF;

    -- Ensure run B exists
    SELECT MAX(run_id) INTO v_run_b
    FROM projection_run
    WHERE account_id = p_account_id AND scenario_id = p_scenario_b;

    IF v_run_b IS NULL THEN
        CALL build_projection(p_scenario_b, p_account_id, 365, v_run_b);
    END IF;

    -- Return comparison row
    SELECT 
        p_account_id AS account_id,
        acc.name AS account_name,
        sa.scenario_id AS scenario_a_id,
        sa.name AS scenario_a_name,
        ra.run_id AS run_a_id,
        ra.min_balance AS min_balance_a,
        ra.first_breach_date AS first_breach_a,
        ra.days_below_buffer AS days_below_a,
        sb.scenario_id AS scenario_b_id,
        sb.name AS scenario_b_name,
        rb.run_id AS run_b_id,
        rb.min_balance AS min_balance_b,
        rb.first_breach_date AS first_breach_b,
        rb.days_below_buffer AS days_below_b,
        (rb.min_balance - ra.min_balance) AS min_balance_delta,
        DATEDIFF(rb.first_breach_date, ra.first_breach_date) AS breach_shift_days,
        (rb.days_below_buffer - ra.days_below_buffer) AS days_below_delta
    FROM projection_run ra
    JOIN projection_run rb ON ra.run_id = v_run_a AND rb.run_id = v_run_b
    JOIN account acc ON acc.account_id = p_account_id
    JOIN scenario sa ON sa.scenario_id = p_scenario_a
    JOIN scenario sb ON sb.scenario_id = p_scenario_b;
END//

-- Procedure: explain_day
-- Purpose: Returns all events up to a given day, largest outflows first, with running total and category breakdown.
-- Acceptance criteria: sum of listed events plus anchor balance equals stored day balance (AC1).
DROP PROCEDURE IF EXISTS explain_day//
CREATE PROCEDURE explain_day(
    IN p_run_id INT,
    IN p_day DATE
)
BEGIN
    DECLARE v_anchor_balance DECIMAL(12,2);
    DECLARE v_anchor_date DATE;
    DECLARE v_stored_balance DECIMAL(12,2);

    SELECT anchor_balance, anchor_date INTO v_anchor_balance, v_anchor_date
    FROM projection_run WHERE run_id = p_run_id;

    SELECT balance INTO v_stored_balance
    FROM projection_day WHERE run_id = p_run_id AND day = p_day;

    -- Result Set 1: Day summary
    SELECT 
        p_run_id AS run_id,
        p_day AS query_day,
        v_anchor_date AS anchor_date,
        v_anchor_balance AS anchor_balance,
        v_stored_balance AS stored_day_balance;

    -- Result Set 2: Events up to query day with running contribution
    SELECT 
        pe.event_id,
        pe.due_date,
        pe.source_type,
        pe.source_id,
        pe.label,
        c.name AS category_name,
        c.is_essential,
        pe.amount,
        v_anchor_balance + SUM(pe.amount) OVER (
            ORDER BY pe.due_date, pe.amount ASC, pe.event_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_balance
    FROM projection_event pe
    JOIN category c ON c.category_id = pe.category_id
    WHERE pe.run_id = p_run_id AND pe.due_date <= p_day
    ORDER BY pe.due_date, pe.amount ASC, pe.event_id;

    -- Result Set 3: Category breakdown up to query day
    SELECT 
        c.category_id,
        c.name AS category_name,
        c.is_essential,
        COUNT(*) AS event_count,
        SUM(pe.amount) AS total_amount
    FROM projection_event pe
    JOIN category c ON c.category_id = pe.category_id
    WHERE pe.run_id = p_run_id AND pe.due_date <= p_day
    GROUP BY c.category_id, c.name, c.is_essential
    ORDER BY total_amount ASC;
END//

-- Procedure: suggest_fixes
-- Purpose: Identifies fewest discretionary outflows before the first breach that cover the shortfall.
-- Scope note: Addresses the first breach only.
DROP PROCEDURE IF EXISTS suggest_fixes//
CREATE PROCEDURE suggest_fixes(
    IN p_run_id INT
)
BEGIN
    DECLARE v_account_id INT;
    DECLARE v_buffer_min DECIMAL(12,2);
    DECLARE v_min_balance DECIMAL(12,2);
    DECLARE v_first_breach DATE;
    DECLARE v_shortfall DECIMAL(12,2);

    SELECT pr.account_id, a.buffer_min, pr.min_balance, pr.first_breach_date
    INTO v_account_id, v_buffer_min, v_min_balance, v_first_breach
    FROM projection_run pr
    JOIN account a ON a.account_id = pr.account_id
    WHERE pr.run_id = p_run_id;

    IF v_first_breach IS NULL THEN
        SELECT 
            'No breach detected in this run; no fixes required.' AS message,
            0.00 AS shortfall_target;
    ELSE
        SET v_shortfall = v_buffer_min - v_min_balance;

        WITH cand AS (
            SELECT 
                pe.event_id,
                pe.source_type,
                pe.source_id,
                pe.due_date,
                pe.label,
                c.name AS category_name,
                -pe.amount AS saving
            FROM projection_event pe
            JOIN category c ON c.category_id = pe.category_id
            WHERE pe.run_id = p_run_id
              AND c.is_essential = FALSE
              AND pe.amount < 0
              AND pe.due_date <= v_first_breach
        ),
        ranked AS (
            SELECT 
                cand.*,
                SUM(saving) OVER (
                    ORDER BY saving DESC, due_date, event_id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cum_saving
            FROM cand
        )
        SELECT 
            event_id,
            source_type,
            source_id,
            due_date,
            label,
            category_name,
            saving,
            cum_saving,
            v_shortfall AS shortfall_target,
            'Addresses the first breach only' AS scope_note
        FROM ranked
        WHERE cum_saving - saving < v_shortfall
        ORDER BY saving DESC, due_date;
    END IF;
END//

-- Procedure: backtest
-- Purpose: Evaluates past forecast error against actual recorded checkpoints.
DROP PROCEDURE IF EXISTS backtest//
CREATE PROCEDURE backtest(
    IN p_account_id INT
)
BEGIN
    DECLARE v_chk_count INT;

    SELECT COUNT(*) INTO v_chk_count
    FROM balance_checkpoint
    WHERE account_id = p_account_id;

    IF v_chk_count < 2 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'At least two balance checkpoints are required for backtesting',
                MYSQL_ERRNO = 45001;
    END IF;

    SELECT 
        bc.checkpoint_id,
        bc.account_id,
        bc.as_of_date AS checkpoint_date,
        bc.balance AS actual_balance,
        pr.run_id AS projected_run_id,
        pr.anchor_date AS projection_anchor_date,
        pd.balance AS projected_balance,
        (pd.balance - bc.balance) AS error_amount,
        ABS(pd.balance - bc.balance) AS absolute_error,
        CASE 
            WHEN bc.balance <> 0 THEN ROUND((ABS(pd.balance - bc.balance) / ABS(bc.balance)) * 100.0, 2)
            ELSE 0.00 
        END AS percent_error
    FROM balance_checkpoint bc
    JOIN projection_day pd ON pd.day = bc.as_of_date
    JOIN projection_run pr ON pr.run_id = pd.run_id 
                         AND pr.account_id = bc.account_id 
                         AND pr.anchor_date < bc.as_of_date
                         AND pr.scenario_id = 1
    WHERE bc.account_id = p_account_id
    ORDER BY bc.as_of_date ASC, pr.run_id DESC;
END//

DELIMITER ;
