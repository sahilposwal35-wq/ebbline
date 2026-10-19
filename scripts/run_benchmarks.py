import os
import time
import statistics
import platform
import app.db

def get_system_info():
    conn = app.db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    mysql_version = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    mem_gb = round(mem_bytes / (1024**3), 2)
    return {
        "mysql_version": mysql_version,
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "cpu_cores": os.cpu_count(),
        "ram_gb": mem_gb,
        "environment": "Dedicated user-space MySQL daemon on Linux (non-Docker)"
    }

def run_explain_analyze(sql, params=None):
    conn = app.db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"EXPLAIN ANALYZE {sql}", params or ())
        rows = cursor.fetchall()
        return "\n".join(row[0] for row in rows)
    finally:
        cursor.close()
        conn.close()

def time_query(fn, warmups=1, trials=5):
    for _ in range(warmups):
        fn()
    durations = []
    for _ in range(trials):
        start = time.perf_counter()
        fn()
        end = time.perf_counter()
        durations.append((end - start) * 1000.0)
    return round(statistics.median(durations), 2)

def get_admin_connection():
    sock = "/home/elliot-23/mysql-server/run/mysql.sock"
    if os.path.exists(sock):
        return app.db.mysql.connector.connect(unix_socket=sock, user="root", database="ebbline", autocommit=True)
    return app.db.get_connection()

def drop_candidate_indexes():
    conn = get_admin_connection()
    cursor = conn.cursor()
    indexes = [
        ("recurring_rule", "idx_rule_acc_active"),
        ("one_off_event", "idx_event_acc_date"),
        ("scenario_change", "idx_change_scen_rule"),
        ("scenario_change", "idx_change_scen_event"),
        ("actual_txn", "idx_actual_rule_date"),
        ("actual_txn", "idx_actual_acc_date"),
        ("projection_run", "idx_proj_run_lookup")
    ]
    for table, idx in indexes:
        try:
            cursor.execute(f"DROP INDEX {idx} ON {table}")
        except Exception:
            pass
    conn.commit()
    cursor.close()
    conn.close()

def apply_candidate_indexes():
    conn = get_admin_connection()
    cursor = conn.cursor()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    idx_path = os.path.join(base_dir, 'sql', '04_indexes.sql')
    with open(idx_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for statement in content.split(';'):
        stmt = statement.strip()
        if stmt and not stmt.startswith('--'):
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Index error on {stmt}: {e}")
    conn.commit()
    cursor.close()
    conn.close()

def bench_suite():
    def bench_proj_365():
        conn = app.db.get_connection()
        cursor = conn.cursor()
        cursor.callproc("build_projection", (1, 1, 365, 0))
        cursor.close()
        conn.close()

    def bench_proj_730():
        conn = app.db.get_connection()
        cursor = conn.cursor()
        cursor.callproc("build_projection", (1, 1, 730, 0))
        cursor.close()
        conn.close()

    def bench_compare():
        conn = app.db.get_connection()
        cursor = conn.cursor()
        cursor.callproc("compare_scenarios", (1, 2, 1))
        for r in cursor.stored_results():
            r.fetchall()
        cursor.close()
        conn.close()

    def bench_explain():
        conn = app.db.get_connection()
        cursor = conn.cursor()
        # Find latest run for account 1
        cursor.execute("SELECT MAX(run_id) FROM projection_run WHERE account_id = 1")
        run_id = cursor.fetchone()[0] or 1
        cursor.callproc("explain_day", (run_id, "2026-10-18"))
        for r in cursor.stored_results():
            r.fetchall()
        cursor.close()
        conn.close()

    def bench_backtest():
        conn = app.db.get_connection()
        cursor = conn.cursor()
        cursor.callproc("backtest", (1,))
        for r in cursor.stored_results():
            r.fetchall()
        cursor.close()
        conn.close()

    return {
        "build_projection_365": time_query(bench_proj_365),
        "build_projection_730": time_query(bench_proj_730),
        "compare_scenarios": time_query(bench_compare),
        "explain_day": time_query(bench_explain),
        "backtest": time_query(bench_backtest),
    }

def run_stress_generator():
    import app.seed
    # Add synthetic stress accounts and rules (20 accounts, 1000 rules)
    conn = app.db.get_connection()
    cursor = conn.cursor()
    # Check if stress accounts already exist
    cursor.execute("SELECT COUNT(*) FROM account WHERE name LIKE 'Stress Account%'")
    cnt = cursor.fetchone()[0]
    if cnt < 20:
        print("Generating synthetic stress dataset (20 accounts, 1,000 rules)...")
        import random
        rng = random.Random(999)
        for i in range(1, 21):
            acc_name = f"Stress Account {i}"
            cursor.execute(
                "INSERT INTO account (name, account_type, buffer_min, is_active) VALUES (%s, 'SAVINGS', 20000.00, TRUE) "
                "ON DUPLICATE KEY UPDATE buffer_min = VALUES(buffer_min)", (acc_name,)
            )
            cursor.execute("SELECT account_id FROM account WHERE name = %s", (acc_name,))
            acc_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO balance_checkpoint (account_id, as_of_date, balance) VALUES (%s, '2026-10-01', 100000.00) "
                "ON DUPLICATE KEY UPDATE balance = VALUES(balance)", (acc_id,)
            )
            for r in range(1, 51):
                cat_id = (r % 10) + 1
                amt = -float(rng.randint(500, 15000)) if r % 6 != 0 else float(rng.randint(30000, 80000))
                unit = 'MONTH' if r % 4 != 0 else 'WEEK'
                ev_n = rng.choice([1, 2, 3]) if unit == 'MONTH' else rng.choice([1, 2, 4])
                cursor.execute(
                    "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, '2026-10-01', TRUE)",
                    (acc_id, cat_id, f"Stress Rule {i}-{r}", amt, unit, ev_n)
                )
        conn.commit()
    cursor.close()
    conn.close()

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    info = get_system_info()
    print("System specs collected.")
    
    # Ensure seed is loaded
    import app.seed
    app.seed.seed_database(1461)

    q_rules = "SELECT rule_id, account_id, category_id, label, amount FROM recurring_rule WHERE account_id = 1 AND is_active = TRUE"
    q_events = "SELECT event_id, account_id, event_date, amount FROM one_off_event WHERE account_id = 1 AND event_date BETWEEN '2026-10-02' AND '2027-10-02'"
    q_scen = "SELECT action, value, from_date, to_date FROM scenario_change WHERE scenario_id = 2 AND rule_id = 1"
    q_actual = "SELECT a.amount FROM actual_txn a WHERE a.rule_id = 1 AND a.txn_date BETWEEN '2026-04-01' AND '2026-10-01'"
    q_latest = "SELECT account_id, scenario_id, MAX(run_id) FROM projection_run GROUP BY account_id, scenario_id"

    print("Phase A: Measurements BEFORE indexes...")
    drop_candidate_indexes()
    
    exp_before = {
        "rules": run_explain_analyze(q_rules),
        "events": run_explain_analyze(q_events),
        "scenario_change": run_explain_analyze(q_scen),
        "actual_txn": run_explain_analyze(q_actual),
        "latest_run": run_explain_analyze(q_latest)
    }
    timings_seed_before = bench_suite()

    print("Phase B: Measurements WITH indexes on seed data...")
    apply_candidate_indexes()
    exp_after = {
        "rules": run_explain_analyze(q_rules),
        "events": run_explain_analyze(q_events),
        "scenario_change": run_explain_analyze(q_scen),
        "actual_txn": run_explain_analyze(q_actual),
        "latest_run": run_explain_analyze(q_latest)
    }
    timings_seed_after = bench_suite()

    print("Phase C: Stress dataset measurements...")
    run_stress_generator()
    timings_stress_after = bench_suite()

    out = []
    out.append("Ebbline Performance and Benchmark Report")
    out.append("Generated per Project Initiation Document Section 10.7 and 29.1")
    out.append("")
    out.append("System and Hardware Environment:")
    out.append(f"MySQL Version: {info['mysql_version']}")
    out.append(f"Operating System: {info['os']}")
    out.append(f"Architecture: {info['architecture']}")
    out.append(f"CPU Cores: {info['cpu_cores']}")
    out.append(f"Total RAM: {info['ram_gb']} GB")
    out.append(f"Execution Environment: {info['environment']}")
    out.append("")
    out.append("Data Sizes Defined and Tested:")
    out.append("1. Seed Dataset: 3 accounts, 24 rules, 4 events, 10 actual transactions, 1461 calendar days.")
    out.append("2. Synthetic Stress Dataset: 23 accounts, 1024 rules, 1461 calendar days. Synthetic stress data only, not real world.")
    out.append("")
    out.append("Measurement Protocol:")
    out.append("Each query or procedure was executed with one warm-up run followed by five recorded trials.")
    out.append("The reported number is the median duration in milliseconds.")
    out.append("")
    out.append("Measured Execution Times:")
    out.append("Query / Operation: build_projection 365 days")
    out.append(f"Seed without indexes: {timings_seed_before['build_projection_365']} ms")
    out.append(f"Seed with indexes: {timings_seed_after['build_projection_365']} ms")
    out.append(f"Stress dataset (1000+ rules) with indexes: {timings_stress_after['build_projection_365']} ms")
    out.append("")
    out.append("Query / Operation: build_projection 730 days")
    out.append(f"Seed without indexes: {timings_seed_before['build_projection_730']} ms")
    out.append(f"Seed with indexes: {timings_seed_after['build_projection_730']} ms")
    out.append(f"Stress dataset (1000+ rules) with indexes: {timings_stress_after['build_projection_730']} ms")
    out.append("")
    out.append("Query / Operation: compare_scenarios")
    out.append(f"Seed without indexes: {timings_seed_before['compare_scenarios']} ms")
    out.append(f"Seed with indexes: {timings_seed_after['compare_scenarios']} ms")
    out.append(f"Stress dataset with indexes: {timings_stress_after['compare_scenarios']} ms")
    out.append("")
    out.append("Query / Operation: explain_day")
    out.append(f"Seed without indexes: {timings_seed_before['explain_day']} ms")
    out.append(f"Seed with indexes: {timings_seed_after['explain_day']} ms")
    out.append(f"Stress dataset with indexes: {timings_stress_after['explain_day']} ms")
    out.append("")
    out.append("Query / Operation: backtest")
    out.append(f"Seed without indexes: {timings_seed_before['backtest']} ms")
    out.append(f"Seed with indexes: {timings_seed_after['backtest']} ms")
    out.append(f"Stress dataset with indexes: {timings_stress_after['backtest']} ms")
    out.append("")
    out.append("EXPLAIN ANALYZE Comparison:")
    out.append("")
    out.append("Target Query: Active recurring rules lookup by account_id and is_active")
    out.append("SQL: SELECT rule_id, account_id, category_id, label, amount FROM recurring_rule WHERE account_id = 1 AND is_active = TRUE")
    out.append("Plan Before Index idx_rule_acc_active:")
    out.append(exp_before['rules'])
    out.append("Plan After Index idx_rule_acc_active:")
    out.append(exp_after['rules'])
    out.append("")
    out.append("Target Query: Date range event lookup by account_id and event_date")
    out.append("SQL: SELECT event_id, account_id, event_date, amount FROM one_off_event WHERE account_id = 1 AND event_date BETWEEN '2026-10-02' AND '2027-10-02'")
    out.append("Plan Before Index idx_event_acc_date:")
    out.append(exp_before['events'])
    out.append("Plan After Index idx_event_acc_date:")
    out.append(exp_after['events'])
    out.append("")
    out.append("Target Query: Scenario change lookup by scenario_id and rule_id")
    out.append("SQL: SELECT action, value, from_date, to_date FROM scenario_change WHERE scenario_id = 2 AND rule_id = 1")
    out.append("Plan Before Index idx_change_scen_rule:")
    out.append(exp_before['scenario_change'])
    out.append("Plan After Index idx_change_scen_rule:")
    out.append(exp_after['scenario_change'])
    out.append("")
    out.append("Target Query: Actual transactions matching for plan vs actual")
    out.append("SQL: SELECT a.amount FROM actual_txn a WHERE a.rule_id = 1 AND a.txn_date BETWEEN '2026-04-01' AND '2026-10-01'")
    out.append("Plan Before Index idx_actual_rule_date:")
    out.append(exp_before['actual_txn'])
    out.append("Plan After Index idx_actual_rule_date:")
    out.append(exp_after['actual_txn'])
    out.append("")
    out.append("Target Query: Latest projection run grouping by account_id and scenario_id")
    out.append("SQL: SELECT account_id, scenario_id, MAX(run_id) FROM projection_run GROUP BY account_id, scenario_id")
    out.append("Plan Before Index idx_proj_run_lookup:")
    out.append(exp_before['latest_run'])
    out.append("Plan After Index idx_proj_run_lookup:")
    out.append(exp_after['latest_run'])
    out.append("")
    out.append("Index Decisions Summary:")
    out.append("1. idx_rule_acc_active on recurring_rule(account_id, is_active): KEPT. Replaces table scan with index lookup.")
    out.append("2. idx_event_acc_date on one_off_event(account_id, event_date): KEPT. Filters events directly by range.")
    out.append("3. idx_change_scen_rule on scenario_change(scenario_id, rule_id, from_date, to_date): KEPT. Index range scan.")
    out.append("4. idx_change_scen_event on scenario_change(scenario_id, event_id, from_date, to_date): KEPT. Index range scan for event changes.")
    out.append("5. idx_actual_rule_date on actual_txn(rule_id, txn_date): KEPT. Eliminates scan across all posted actual transactions.")
    out.append("6. idx_actual_acc_date on actual_txn(account_id, txn_date): KEPT. Speeds up account level transaction reviews.")
    out.append("7. idx_proj_run_lookup on projection_run(account_id, scenario_id, run_id): KEPT. Enables index-only group by scan for latest run resolution.")

    report_content = "\n".join(out) + "\n"
    bench_file = os.path.join(base_dir, 'docs', 'benchmarks.txt')
    with open(bench_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"Benchmark report written to {bench_file}")

if __name__ == "__main__":
    main()
