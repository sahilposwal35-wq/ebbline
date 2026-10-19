-- Test T31: Compare Baseline with itself
-- Expected: min_balance_delta = 0, breach_shift_days = 0, days_below_delta = 0

CALL compare_scenarios(1, 1, 1);
