import sys
import os
import datetime
from decimal import Decimal
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db
from app.formatters import format_inr, format_date
from app.import_csv import import_actuals_csv

app = FastAPI(
    title="Ebbline API",
    description="Cash flow forecasting engine API powered by MySQL 8",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class AccountResponse(BaseModel):
    account_id: int
    name: str
    account_type: str
    buffer_min: float
    buffer_min_formatted: str

class CategoryResponse(BaseModel):
    category_id: int
    name: str
    is_essential: bool

class ScenarioResponse(BaseModel):
    scenario_id: int
    name: str
    description: Optional[str] = None

class RuleCreateRequest(BaseModel):
    account_id: int
    category_id: int
    label: str
    amount: float
    unit: str
    every_n: int = 1
    start_date: str
    end_date: Optional[str] = None

class EventCreateRequest(BaseModel):
    account_id: int
    category_id: int
    label: str
    amount: float
    event_date: str

class ProjectionBuildRequest(BaseModel):
    account_id: int
    scenario_id: int = 1
    horizon_days: int = 365

class ScenarioCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_type: str = "RULE"
    target_id: int
    action: str
    value: Optional[float] = None
    from_date: str
    to_date: str

@app.get("/api/accounts", response_model=List[AccountResponse])
def list_accounts():
    rows = db.fetch_all("SELECT account_id, name, account_type, buffer_min FROM account WHERE is_active = TRUE ORDER BY account_id")
    res = []
    for r in rows:
        b = float(r['buffer_min'])
        res.append(AccountResponse(
            account_id=r['account_id'],
            name=r['name'],
            account_type=r['account_type'],
            buffer_min=b,
            buffer_min_formatted=format_inr(b)
        ))
    return res

@app.get("/api/categories", response_model=List[CategoryResponse])
def list_categories():
    rows = db.fetch_all("SELECT category_id, name, is_essential FROM category ORDER BY category_id")
    return [CategoryResponse(**r) for r in rows]

@app.get("/api/scenarios", response_model=List[ScenarioResponse])
def list_scenarios():
    rows = db.fetch_all("SELECT scenario_id, name, description FROM scenario ORDER BY scenario_id")
    return [ScenarioResponse(**r) for r in rows]

@app.get("/api/rules")
def list_rules(account_id: int = Query(...)):
    rows = db.fetch_all(
        "SELECT r.rule_id, r.label, r.amount, r.unit, r.every_n, r.start_date, r.end_date, r.is_active, "
        "c.name AS category_name, c.is_essential "
        "FROM recurring_rule r JOIN category c ON c.category_id = r.category_id "
        "WHERE r.account_id = %s ORDER BY r.rule_id",
        (account_id,)
    )
    res = []
    for r in rows:
        amt = float(r['amount'])
        res.append({
            "rule_id": r['rule_id'],
            "label": r['label'],
            "category_name": r['category_name'],
            "is_essential": bool(r['is_essential']),
            "amount": amt,
            "amount_formatted": format_inr(amt),
            "unit": r['unit'],
            "every_n": r['every_n'],
            "cadence_formatted": f"Every {r['every_n']} {r['unit'].lower()}(s)",
            "start_date": str(r['start_date']),
            "start_date_formatted": format_date(r['start_date']),
            "end_date": str(r['end_date']) if r['end_date'] else None,
            "end_date_formatted": format_date(r['end_date']) if r['end_date'] else "Ongoing",
            "is_active": bool(r['is_active'])
        })
    return res

@app.post("/api/rules")
def create_rule(req: RuleCreateRequest):
    if not req.label.strip():
        raise HTTPException(status_code=400, detail="Rule label cannot be empty.")
    if req.amount == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero.")
    try:
        db.execute_query(
            "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date, end_date, is_active) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)",
            (req.account_id, req.category_id, req.label.strip(), req.amount, req.unit, req.every_n, req.start_date, req.end_date)
        )
        return {"success": True, "message": "Recurring rule created successfully."}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.patch("/api/rules/{rule_id}/toggle")
def toggle_rule(rule_id: int):
    rule = db.fetch_one("SELECT is_active FROM recurring_rule WHERE rule_id = %s", (rule_id,))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    new_status = not rule['is_active']
    db.execute_query("UPDATE recurring_rule SET is_active = %s WHERE rule_id = %s", (new_status, rule_id))
    return {"success": True, "rule_id": rule_id, "is_active": new_status}

@app.get("/api/events")
def list_events(account_id: int = Query(...)):
    rows = db.fetch_all(
        "SELECT e.event_id, e.event_date, e.label, e.amount, c.name AS category_name, c.is_essential "
        "FROM one_off_event e JOIN category c ON c.category_id = e.category_id "
        "WHERE e.account_id = %s ORDER BY e.event_date",
        (account_id,)
    )
    res = []
    for r in rows:
        amt = float(r['amount'])
        res.append({
            "event_id": r['event_id'],
            "event_date": str(r['event_date']),
            "event_date_formatted": format_date(r['event_date']),
            "label": r['label'],
            "category_name": r['category_name'],
            "is_essential": bool(r['is_essential']),
            "amount": amt,
            "amount_formatted": format_inr(amt)
        })
    return res

@app.post("/api/events")
def create_event(req: EventCreateRequest):
    if not req.label.strip():
        raise HTTPException(status_code=400, detail="Event label cannot be empty.")
    if req.amount == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero.")
    try:
        db.execute_query(
            "INSERT INTO one_off_event (account_id, category_id, label, amount, event_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            (req.account_id, req.category_id, req.label.strip(), req.amount, req.event_date)
        )
        return {"success": True, "message": "One off event created successfully."}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/projections/build")
def build_projection_endpoint(req: ProjectionBuildRequest):
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        res = cur.callproc("build_projection", [req.scenario_id, req.account_id, req.horizon_days, 0])
        run_id = res[3]
        cur.close()
        conn.close()

        run_header = db.fetch_one("SELECT * FROM projection_run WHERE run_id = %s", (run_id,))
        acc = db.fetch_one("SELECT buffer_min FROM account WHERE account_id = %s", (req.account_id,))
        buf = float(acc['buffer_min'])

        days = db.fetch_all("SELECT day, net, balance FROM projection_day WHERE run_id = %s ORDER BY day", (run_id,))
        day_rows = []
        for d in days:
            b_val = float(d['balance'])
            n_val = float(d['net'])
            day_rows.append({
                "day": str(d['day']),
                "day_formatted": format_date(d['day']),
                "net": n_val,
                "net_formatted": format_inr(n_val),
                "balance": b_val,
                "balance_formatted": format_inr(b_val),
                "is_breach": b_val < buf
            })

        min_bal = float(run_header['min_balance'])
        anchor_bal = float(run_header['anchor_balance'])

        return {
            "run_id": run_id,
            "account_id": req.account_id,
            "scenario_id": req.scenario_id,
            "anchor_date": str(run_header['anchor_date']),
            "anchor_date_formatted": format_date(run_header['anchor_date']),
            "anchor_balance": anchor_bal,
            "anchor_balance_formatted": format_inr(anchor_bal),
            "horizon_start": str(run_header['horizon_start']),
            "horizon_start_formatted": format_date(run_header['horizon_start']),
            "horizon_end": str(run_header['horizon_end']),
            "horizon_end_formatted": format_date(run_header['horizon_end']),
            "safety_buffer": buf,
            "safety_buffer_formatted": format_inr(buf),
            "min_balance": min_bal,
            "min_balance_formatted": format_inr(min_bal),
            "min_balance_date": str(run_header['min_balance_date']) if run_header['min_balance_date'] else None,
            "min_balance_date_formatted": format_date(run_header['min_balance_date']) if run_header['min_balance_date'] else "None",
            "first_breach_date": str(run_header['first_breach_date']) if run_header['first_breach_date'] else None,
            "first_breach_date_formatted": format_date(run_header['first_breach_date']) if run_header['first_breach_date'] else "None",
            "days_below_buffer": run_header['days_below_buffer'],
            "ledger": day_rows
        }
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.get("/api/scenarios/compare")
def compare_scenarios_endpoint(account_id: int = Query(...), scenario_a: int = Query(1), scenario_b: int = Query(...)):
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("compare_scenarios", [scenario_a, scenario_b, account_id])
        results = list(cur.stored_results())
        row = results[0].fetchone() if results else None
        cur.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Comparison data not found.")

        acc = db.fetch_one("SELECT buffer_min FROM account WHERE account_id = %s", (account_id,))
        buf = float(acc['buffer_min'])

        days_a = db.fetch_all("SELECT day, balance FROM projection_day WHERE run_id = %s ORDER BY day", (row['run_a_id'],))
        days_b = db.fetch_all("SELECT day, balance FROM projection_day WHERE run_id = %s ORDER BY day", (row['run_b_id'],))

        b_map = {str(d['day']): float(d['balance']) for d in days_b}
        combined_series = []
        for d in days_a:
            ds = str(d['day'])
            combined_series.append({
                "day": ds,
                "day_formatted": format_date(d['day']),
                "balance_a": float(d['balance']),
                "balance_b": b_map.get(ds, None),
                "safety_buffer": buf
            })

        min_a = float(row['min_balance_a'])
        min_b = float(row['min_balance_b'])
        delta_min = float(row['min_balance_delta'])

        return {
            "account_id": account_id,
            "account_name": row['account_name'],
            "scenario_a_id": row['scenario_a_id'],
            "scenario_a_name": row['scenario_a_name'],
            "run_a_id": row['run_a_id'],
            "min_balance_a": min_a,
            "min_balance_a_formatted": format_inr(min_a),
            "first_breach_a": str(row['first_breach_a']) if row['first_breach_a'] else None,
            "first_breach_a_formatted": format_date(row['first_breach_a']) if row['first_breach_a'] else "None",
            "days_below_a": row['days_below_a'],
            "scenario_b_id": row['scenario_b_id'],
            "scenario_b_name": row['scenario_b_name'],
            "run_b_id": row['run_b_id'],
            "min_balance_b": min_b,
            "min_balance_b_formatted": format_inr(min_b),
            "first_breach_b": str(row['first_breach_b']) if row['first_breach_b'] else None,
            "first_breach_b_formatted": format_date(row['first_breach_b']) if row['first_breach_b'] else "None",
            "days_below_b": row['days_below_b'],
            "min_balance_delta": delta_min,
            "min_balance_delta_formatted": format_inr(delta_min),
            "breach_shift_days": row['breach_shift_days'],
            "days_below_delta": row['days_below_delta'],
            "series": combined_series
        }
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/scenarios")
def create_scenario_endpoint(req: ScenarioCreateRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Scenario name is required.")
    if req.to_date < req.from_date:
        raise HTTPException(status_code=400, detail="To date cannot be earlier than from date.")
    try:
        db.execute_query(
            "INSERT INTO scenario (name, description) VALUES (%s, %s)",
            (req.name.strip(), req.description.strip() if req.description else None)
        )
        new_s = db.fetch_one("SELECT scenario_id FROM scenario WHERE name = %s", (req.name.strip(),))
        new_s_id = new_s['scenario_id']

        rule_id = req.target_id if req.target_type == "RULE" else None
        event_id = req.target_id if req.target_type == "EVENT" else None

        cur_p = db.get_connection().cursor()
        cur_p.callproc("add_scenario_change", [
            new_s_id, rule_id, event_id, req.action, req.value if req.action != "SKIP" else None, req.from_date, req.to_date
        ])
        cur_p.close()
        return {"success": True, "scenario_id": new_s_id, "name": req.name}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.get("/api/analytics/explain")
def explain_day_endpoint(run_id: int = Query(...), date: str = Query(...)):
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("explain_day", [run_id, date])
        results = list(cur.stored_results())
        summary = results[0].fetchone() if len(results) > 0 else None
        events = results[1].fetchall() if len(results) > 1 else []
        categories = results[2].fetchall() if len(results) > 2 else []
        cur.close()
        conn.close()

        if not summary:
            raise HTTPException(status_code=404, detail="Run not found.")

        anchor_bal = float(summary['anchor_balance'])
        stored_bal = float(summary['stored_day_balance'])
        net_change = stored_bal - anchor_bal

        event_rows = []
        for e in events:
            amt = float(e['amount'])
            rb = float(e['running_balance'])
            event_rows.append({
                "event_id": e['event_id'],
                "due_date": str(e['due_date']),
                "due_date_formatted": format_date(e['due_date']),
                "label": e['label'],
                "category_name": e['category_name'],
                "is_essential": bool(e['is_essential']),
                "amount": amt,
                "amount_formatted": format_inr(amt),
                "running_balance": rb,
                "running_balance_formatted": format_inr(rb)
            })

        cat_rows = []
        for c in categories:
            tot = float(c['total_amount'])
            cat_rows.append({
                "category_name": c['name'],
                "is_essential": bool(c['is_essential']),
                "event_count": c['event_count'],
                "total_amount": tot,
                "total_amount_formatted": format_inr(tot)
            })

        return {
            "run_id": run_id,
            "query_day": str(summary['query_day']),
            "query_day_formatted": format_date(summary['query_day']),
            "anchor_date": str(summary['anchor_date']),
            "anchor_date_formatted": format_date(summary['anchor_date']),
            "anchor_balance": anchor_bal,
            "anchor_balance_formatted": format_inr(anchor_bal),
            "stored_day_balance": stored_bal,
            "stored_day_balance_formatted": format_inr(stored_bal),
            "cumulative_net": net_change,
            "cumulative_net_formatted": format_inr(net_change),
            "events": event_rows,
            "categories": cat_rows
        }
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.get("/api/analytics/suggest-fixes")
def suggest_fixes_endpoint(run_id: int = Query(...)):
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("suggest_fixes", [run_id])
        results = list(cur.stored_results())
        fixes = results[0].fetchall() if results else []
        cur.close()
        conn.close()

        if not fixes or "shortfall_target" not in fixes[0]:
            return {"has_breach": False, "message": "No breach detected in this run; no fixes required."}

        target = float(fixes[0]['shortfall_target'])
        fix_rows = []
        for f in fixes:
            sav = float(f['saving'])
            csav = float(f['cum_saving'])
            fix_rows.append({
                "source_type": f['source_type'],
                "source_id": f['source_id'],
                "due_date": str(f['due_date']),
                "due_date_formatted": format_date(f['due_date']),
                "label": f['label'],
                "category_name": f['category_name'],
                "saving": sav,
                "saving_formatted": format_inr(sav),
                "cum_saving": csav,
                "cum_saving_formatted": format_inr(csav)
            })

        return {
            "has_breach": True,
            "shortfall_target": target,
            "shortfall_target_formatted": format_inr(target),
            "scope_note": fixes[0]['scope_note'],
            "fixes": fix_rows
        }
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/analytics/save-fixes")
def save_fixes_endpoint(run_id: int = Query(...)):
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("suggest_fixes", [run_id])
        results = list(cur.stored_results())
        fixes = results[0].fetchall() if results else []
        cur.close()
        conn.close()

        if not fixes or "shortfall_target" not in fixes[0]:
            raise HTTPException(status_code=400, detail="No fixes available to save.")

        today_str = datetime.date.today().strftime('%d %b %Y')
        new_name = f"Fix for Run {run_id} ({today_str})"
        db.execute_query(
            "INSERT INTO scenario (name, description) VALUES (%s, %s)",
            (new_name, "Automated fix scenario skipping discretionary outflows to prevent first breach")
        )
        new_scen = db.fetch_one("SELECT scenario_id FROM scenario WHERE name = %s", (new_name,))
        new_scen_id = new_scen['scenario_id']

        for f in fixes:
            rule_id = f['source_id'] if f['source_type'] == 'RULE' else None
            event_id = f['source_id'] if f['source_type'] == 'EVENT' else None
            db.execute_query(
                "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
                "VALUES (%s, %s, %s, 'SKIP', NULL, %s, %s)",
                (new_scen_id, rule_id, event_id, f['due_date'], f['due_date'])
            )

        return {"success": True, "scenario_id": new_scen_id, "name": new_name, "fixes_count": len(fixes)}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@app.get("/api/analytics/reserve")
def reserve_schedule_endpoint(account_id: int = Query(...)):
    reserves = db.fetch_all(
        "SELECT label, total_obligation, unit, every_n, period_months, monthly_set_aside "
        "FROM v_reserve_schedule WHERE account_id = %s ORDER BY monthly_set_aside DESC",
        (account_id,)
    )
    rows = []
    tot = 0.0
    for r in reserves:
        ob = float(r['total_obligation'])
        ms = float(r['monthly_set_aside'])
        tot += ms
        rows.append({
            "label": r['label'],
            "total_obligation": ob,
            "total_obligation_formatted": format_inr(ob),
            "cycle_formatted": f"Every {r['every_n']} {r['unit'].lower()}(s) ({r['period_months']} months)",
            "monthly_set_aside": ms,
            "monthly_set_aside_formatted": format_inr(ms)
        })
    return {"total_monthly_reserve": tot, "total_monthly_reserve_formatted": format_inr(tot), "rows": rows}

@app.get("/api/analytics/plan-vs-actual")
def plan_vs_actual_endpoint(account_id: int = Query(...)):
    rows = db.fetch_all(
        "SELECT rule_label, ym, planned_amount, actual_amount, variance, variance_pct, avg_3m "
        "FROM v_plan_vs_actual WHERE account_id = %s ORDER BY ym DESC, rule_label",
        (account_id,)
    )
    res = []
    for r in rows:
        p = float(r['planned_amount'])
        a = float(r['actual_amount'])
        v = float(r['variance'])
        avg3 = float(r['avg_3m']) if r['avg_3m'] is not None else 0.0
        res.append({
            "month": r['ym'],
            "rule_label": r['rule_label'],
            "planned": p,
            "planned_formatted": format_inr(p),
            "actual": a,
            "actual_formatted": format_inr(a),
            "variance": v,
            "variance_formatted": format_inr(v),
            "variance_pct": float(r['variance_pct']),
            "avg_3m": avg3,
            "avg_3m_formatted": format_inr(avg3)
        })
    return res

@app.get("/api/analytics/backtest")
def backtest_endpoint(account_id: int = Query(...)):
    try:
        conn = db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("backtest", [account_id])
        results = list(cur.stored_results())
        rows = results[0].fetchall() if results else []
        cur.close()
        conn.close()

        b_rows = []
        mae = 0.0
        rmse = 0.0
        for r in rows:
            act = float(r['actual_balance'])
            proj = float(r['projected_balance'])
            err = float(r['abs_error'])
            mae = float(r['overall_mae'])
            rmse = float(r['overall_rmse'])
            b_rows.append({
                "checkpoint_date": str(r['checkpoint_date']),
                "checkpoint_date_formatted": format_date(r['checkpoint_date']),
                "actual_balance": act,
                "actual_balance_formatted": format_inr(act),
                "projected_balance": proj,
                "projected_balance_formatted": format_inr(proj),
                "abs_error": err,
                "abs_error_formatted": format_inr(err),
                "pct_error": float(r['pct_error'])
            })
        return {
            "disclaimer": "Backtest on synthetic data does not show real world accuracy.",
            "overall_mae": mae,
            "overall_mae_formatted": format_inr(mae),
            "overall_rmse": rmse,
            "overall_rmse_formatted": format_inr(rmse),
            "comparisons": b_rows
        }
    except Exception as ex:
        if "45001" in str(ex):
            return {
                "error": "Account has fewer than 2 checkpoints; at least 2 checkpoints are required to perform a backtest.",
                "comparisons": []
            }
        raise HTTPException(status_code=400, detail=str(ex))

@app.post("/api/import-csv")
async def import_csv_endpoint(file: UploadFile = File(...), account_id: int = Query(1)):
    import tempfile
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    res = import_actuals_csv(tmp_path, default_account_id=account_id, rollback_on_error=True)
    os.remove(tmp_path)
    if res['success']:
        return {"success": True, "inserted": res['inserted'], "duplicates": res['duplicates']}
    else:
        raise HTTPException(status_code=400, detail=res['error'])

from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')
if os.path.exists(frontend_dist):
    app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='frontend')
