-- Query Q11: How wrong were past forecasts?
-- Technique: Join run days to checkpoints, absolute and percent error
-- Parameters: @account_id

SELECT 
    bc.checkpoint_id,
    bc.as_of_date,
    bc.balance AS actual_balance,
    pd.balance AS forecast_balance,
    (pd.balance - bc.balance) AS error,
    ABS(pd.balance - bc.balance) AS absolute_error,
    ROUND((ABS(pd.balance - bc.balance) / ABS(bc.balance)) * 100.0, 2) AS percent_error
FROM balance_checkpoint bc
JOIN projection_day pd ON pd.day = bc.as_of_date
JOIN projection_run pr ON pr.run_id = pd.run_id 
                     AND pr.account_id = bc.account_id
                     AND pr.anchor_date < bc.as_of_date
                     AND pr.scenario_id = 1
WHERE bc.account_id = @account_id
ORDER BY bc.as_of_date ASC;
