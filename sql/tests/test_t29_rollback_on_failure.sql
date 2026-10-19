-- Test T29: Atomic Transaction Rollback on Failure
-- Validates that any error during build_projection leaves zero orphaned header, day, or event rows.

SELECT COUNT(*) INTO @runs_before FROM projection_run;
SELECT COUNT(*) INTO @days_before FROM projection_day;
SELECT COUNT(*) INTO @events_before FROM projection_event;

-- Attempt projection with bad horizon (731 days exceeds max 730)
-- Should raise error 45003 and roll back
-- (Run via Python test runner to verify error code and count stability)
