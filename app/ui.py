import sys
import os
import io
import datetime
from decimal import Decimal
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import pandas as pd
import altair as alt
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.db
from app.formatters import format_inr, format_date
from app.import_csv import import_actuals_csv

# Page configuration
st.set_page_config(
    page_title="Ebbline",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom shoreline theme styling
CUSTOM_CSS = """
<style>
    body {
        background-color: #F7F3EA;
        color: #13303A;
        font-family: sans-serif;
    }
    .stApp {
        background-color: #F7F3EA;
    }
    .ebb-card {
        background-color: #FFFFFF;
        border: 1px solid #E4DDCF;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .ebb-card-title {
        font-size: 13px;
        color: #5B6B73;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .ebb-card-val {
        font-size: 22px;
        font-weight: 600;
        color: #13303A;
    }
    .ebb-card-sub {
        font-size: 12px;
        color: #5B6B73;
        margin-top: 4px;
    }
    .ebb-error-box {
        background-color: #FDF2F1;
        border: 1px solid #F5C6C3;
        border-radius: 6px;
        padding: 14px;
        color: #D2453D;
        font-size: 14px;
        margin-bottom: 16px;
    }
    .ebb-success-box {
        background-color: #F0F8F5;
        border: 1px solid #C2E2D6;
        border-radius: 6px;
        padding: 14px;
        color: #2E8B6B;
        font-size: 14px;
        margin-bottom: 16px;
    }
    .ebb-header-title {
        font-size: 28px;
        font-weight: 700;
        color: #0F6B73;
        margin-bottom: 2px;
    }
    .ebb-header-sub {
        font-size: 15px;
        color: #5B6B73;
        margin-bottom: 24px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Helper DB access functions
def get_accounts():
    return app.db.fetch_all("SELECT account_id, name, buffer_min FROM account WHERE is_active = TRUE ORDER BY account_id")

def get_scenarios():
    return app.db.fetch_all("SELECT scenario_id, name, description FROM scenario ORDER BY scenario_id")

def get_categories():
    return app.db.fetch_all("SELECT category_id, name, is_essential FROM category ORDER BY category_id")

# Header component
def render_header():
    st.markdown("""
        <div class="ebb-header-title">Ebbline</div>
        <div class="ebb-header-sub">Know the day your balance dips, before it does.</div>
    """, unsafe_allow_html=True)

# Screen 1: Rules and Events
def screen_rules_and_events():
    st.subheader("Rules and Events")
    accounts = get_accounts()
    if not accounts:
        st.write("No active accounts found.")
        return

    acc_options = {f"{a['name']} (ID {a['account_id']})": a['account_id'] for a in accounts}
    selected_acc_label = st.selectbox("Select Account", list(acc_options.keys()))
    selected_acc_id = acc_options[selected_acc_label]
    categories = get_categories()
    cat_map = {c['category_id']: f"{c['name']} ({'Essential' if c['is_essential'] else 'Discretionary'})" for c in categories}

    tab_rules, tab_events, tab_add_rule, tab_add_event, tab_import = st.tabs([
        "Recurring Rules", "One Off Events", "Add Recurring Rule", "Add One Off Event", "Import CSV"
    ])

    with tab_rules:
        rules = app.db.fetch_all(
            "SELECT r.rule_id, r.label, r.amount, r.unit, r.every_n, r.start_date, r.end_date, r.is_active, c.name AS category_name, c.is_essential "
            "FROM recurring_rule r JOIN category c ON c.category_id = r.category_id "
            "WHERE r.account_id = %s ORDER BY r.rule_id",
            (selected_acc_id,)
        )
        if rules:
            display_rows = []
            for r in rules:
                display_rows.append({
                    "Rule ID": r['rule_id'],
                    "Label": r['label'],
                    "Category": r['category_name'],
                    "Nature": "Essential" if r['is_essential'] else "Discretionary",
                    "Amount": format_inr(r['amount']),
                    "Cadence": f"Every {r['every_n']} {r['unit'].lower()}(s)",
                    "Start Date": format_date(r['start_date']),
                    "End Date": format_date(r['end_date']) if r['end_date'] else "Ongoing",
                    "Status": "Active" if r['is_active'] else "Inactive"
                })
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True)

            st.write("Toggle Rule Status:")
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                toggle_rule_id = st.selectbox("Select Rule to Toggle", [r['rule_id'] for r in rules], format_func=lambda x: f"Rule {x}: {next(r['label'] for r in rules if r['rule_id'] == x)}")
            with col_t2:
                current_rule = next(r for r in rules if r['rule_id'] == toggle_rule_id)
                new_status = not current_rule['is_active']
                btn_label = f"Set to {'Active' if new_status else 'Inactive'}"
                if st.button(btn_label):
                    app.db.execute_query("UPDATE recurring_rule SET is_active = %s WHERE rule_id = %s", (new_status, toggle_rule_id))
                    st.success(f"Rule {toggle_rule_id} status updated to {'Active' if new_status else 'Inactive'}.")
                    st.rerun()
        else:
            st.write("No recurring rules recorded for this account.")

    with tab_events:
        events = app.db.fetch_all(
            "SELECT e.event_id, e.event_date, e.label, e.amount, c.name AS category_name, c.is_essential "
            "FROM one_off_event e JOIN category c ON c.category_id = e.category_id "
            "WHERE e.account_id = %s ORDER BY e.event_date",
            (selected_acc_id,)
        )
        if events:
            display_events = []
            for e in events:
                display_events.append({
                    "Event ID": e['event_id'],
                    "Date": format_date(e['event_date']),
                    "Label": e['label'],
                    "Category": e['category_name'],
                    "Nature": "Essential" if e['is_essential'] else "Discretionary",
                    "Amount": format_inr(e['amount'])
                })
            st.dataframe(pd.DataFrame(display_events), use_container_width=True)
        else:
            st.write("No one-off events recorded for this account.")

    with tab_add_rule:
        with st.form("form_add_rule"):
            f_label = st.text_input("Rule Label", placeholder="e.g. Monthly Broadband")
            f_cat = st.selectbox("Category", list(cat_map.keys()), format_func=lambda x: cat_map[x])
            f_amt = st.number_input("Amount (negative for expense, positive for income)", value=-1500.00, step=100.00)
            f_unit = st.selectbox("Frequency Unit", ["MONTH", "WEEK"])
            f_every = st.number_input("Every N units", min_value=1, max_value=52, value=1)
            f_start = st.date_input("Start Date", value=datetime.date.today())
            has_end = st.checkbox("Has End Date")
            f_end = st.date_input("End Date", value=datetime.date.today() + datetime.timedelta(days=365)) if has_end else None
            submit_rule = st.form_submit_button("Save Recurring Rule")

            if submit_rule:
                if not f_label.strip():
                    st.error("Rule label cannot be empty.")
                elif f_amt == 0:
                    st.error("Amount cannot be zero.")
                elif has_end and f_end < f_start:
                    st.error("End date cannot be earlier than start date.")
                else:
                    try:
                        app.db.execute_query(
                            "INSERT INTO recurring_rule (account_id, category_id, label, amount, unit, every_n, start_date, end_date, is_active) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)",
                            (selected_acc_id, f_cat, f_label.strip(), f_amt, f_unit, f_every, f_start, f_end if has_end else None)
                        )
                        st.success("Recurring rule added successfully.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Database error: {ex}")

    with tab_add_event:
        with st.form("form_add_event"):
            fe_label = st.text_input("Event Label", placeholder="e.g. Annual Home Insurance Renewal")
            fe_cat = st.selectbox("Category", list(cat_map.keys()), format_func=lambda x: cat_map[x], key="fe_cat")
            fe_amt = st.number_input("Amount (negative for expense, positive for income)", value=-5000.00, step=500.00, key="fe_amt")
            fe_date = st.date_input("Event Date", value=datetime.date.today(), key="fe_date")
            submit_event = st.form_submit_button("Save One Off Event")

            if submit_event:
                if not fe_label.strip():
                    st.error("Event label cannot be empty.")
                elif fe_amt == 0:
                    st.error("Amount cannot be zero.")
                else:
                    try:
                        app.db.execute_query(
                            "INSERT INTO one_off_event (account_id, category_id, label, amount, event_date) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (selected_acc_id, fe_cat, fe_label.strip(), fe_amt, fe_date)
                        )
                        st.success("One off event added successfully.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Database error: {ex}")

    with tab_import:
        st.write("Upload actual transactions CSV file. Columns expected: txn_date, amount, label. Optional: account_id, rule_id.")
        uploaded_file = st.file_uploader("Select CSV File", type=["csv"])
        if uploaded_file is not None:
            if st.button("Execute CSV Import"):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                res = import_actuals_csv(tmp_path, default_account_id=selected_acc_id, rollback_on_error=True)
                os.remove(tmp_path)
                if res['success']:
                    st.markdown(f"""
                        <div class="ebb-success-box">
                            Import completed successfully.<br>
                            Rows inserted: {res['inserted']}<br>
                            Duplicates skipped: {res['duplicates']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="ebb-error-box">
                            Import failed and was rolled back completely.<br>
                            Error details: {res['error']}
                        </div>
                    """, unsafe_allow_html=True)

# Screen 2: Projection
def screen_projection():
    st.subheader("Cash Flow Projection")
    accounts = get_accounts()
    scenarios = get_scenarios()
    if not accounts:
        st.write("No active accounts found.")
        return

    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 2, 1.5])
    with col_ctrl1:
        acc_dict = {f"{a['name']} (ID {a['account_id']})": a['account_id'] for a in accounts}
        acc_label = st.selectbox("Account", list(acc_dict.keys()), key="proj_acc")
        acc_id = acc_dict[acc_label]
    with col_ctrl2:
        scen_dict = {f"{s['name']} (ID {s['scenario_id']})": s['scenario_id'] for s in scenarios}
        scen_label = st.selectbox("Scenario", list(scen_dict.keys()), key="proj_scen")
        scen_id = scen_dict[scen_label]
    with col_ctrl3:
        horizon_days = st.slider("Horizon Days", min_value=30, max_value=730, value=365, step=15)
    with col_ctrl4:
        st.write("")
        st.write("")
        build_clicked = st.button("Build Projection", use_container_width=True)

    # State management for current run
    if "current_run_id" not in st.session_state or build_clicked:
        try:
            conn = app.db.get_connection()
            cur = conn.cursor()
            res = cur.callproc("build_projection", [scen_id, acc_id, horizon_days, 0])
            st.session_state["current_run_id"] = res[3]
            cur.close()
            conn.close()
        except Exception as ex:
            st.markdown(f"""
                <div class="ebb-error-box">
                    Database procedure error: {ex}
                </div>
            """, unsafe_allow_html=True)
            return

    run_id = st.session_state.get("current_run_id")
    if not run_id:
        st.write("No projection built yet.")
        return

    # Load run header and account buffer
    run_header = app.db.fetch_one("SELECT * FROM projection_run WHERE run_id = %s", (run_id,))
    account_row = app.db.fetch_one("SELECT buffer_min FROM account WHERE account_id = %s", (run_header['account_id'],))
    buffer_min = float(account_row['buffer_min'])

    # Display Four Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Anchor Balance</div>
                <div class="ebb-card-val">{format_inr(run_header['anchor_balance'])}</div>
                <div class="ebb-card-sub">As of {format_date(run_header['anchor_date'])}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Lowest Balance</div>
                <div class="ebb-card-val">{format_inr(run_header['min_balance'])}</div>
                <div class="ebb-card-sub">Recorded on {format_date(run_header['min_balance_date'])}</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        breach_text = format_date(run_header['first_breach_date']) if run_header['first_breach_date'] else "None"
        sub_text = "Safe across entire horizon" if not run_header['first_breach_date'] else "Safety buffer breached"
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">First Breach Date</div>
                <div class="ebb-card-val" style="color: {'#D2453D' if run_header['first_breach_date'] else '#2E8B6B'};">{breach_text}</div>
                <div class="ebb-card-sub">{sub_text}</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Days Below Buffer</div>
                <div class="ebb-card-val" style="color: {'#D2453D' if run_header['days_below_buffer'] > 0 else '#2E8B6B'};">{run_header['days_below_buffer']}</div>
                <div class="ebb-card-sub">Safety buffer target {format_inr(buffer_min)}</div>
            </div>
        """, unsafe_allow_html=True)

    # Fetch daily rows
    days_data = app.db.fetch_all(
        "SELECT day, net, balance FROM projection_day WHERE run_id = %s ORDER BY day",
        (run_id,)
    )
    if not days_data:
        st.write("No daily projection rows found.")
        return

    df_days = pd.DataFrame(days_data)
    df_days['day_str'] = df_days['day'].astype(str)
    df_days['balance_float'] = df_days['balance'].astype(float)
    df_days['buffer_float'] = buffer_min
    df_days['is_breach'] = df_days['balance_float'] < buffer_min

    # Build Altair Shoreline Chart
    base_chart = alt.Chart(df_days).encode(x=alt.X('day:T', title='Timeline Date'))

    balance_line = base_chart.mark_line(color='#0F6B73', strokeWidth=2.5).encode(
        y=alt.Y('balance_float:Q', title='Account Balance (INR)')
    )

    buffer_rule = base_chart.mark_line(color='#D9922E', strokeDash=[6, 4], strokeWidth=2).encode(
        y=alt.Y('buffer_float:Q')
    )

    breach_points = base_chart.filter(alt.datum.is_breach == True).mark_point(
        color='#D2453D', size=25, filled=True
    ).encode(
        y='balance_float:Q'
    )

    chart = balance_line + buffer_rule + breach_points

    # Annotate First Breach if present
    if run_header['first_breach_date']:
        fb_df = pd.DataFrame([{
            'day': str(run_header['first_breach_date']),
            'balance_float': float(run_header['min_balance']),
            'label': 'First breach'
        }])
        fb_text = alt.Chart(fb_df).mark_text(
            align='left', dx=8, dy=-10, color='#D2453D', fontSize=12, fontWeight='bold'
        ).encode(
            x='day:T', y='balance_float:Q', text='label:N'
        )
        chart = chart + fb_text

    st.altair_chart(chart.properties(height=380, width='container'), use_container_width=True)
    st.caption("Balance line drawn in deep teal. Safety buffer drawn as amber dashed line. Breach days indicated in coral red.")

    # Data table and Export options
    col_t_title, col_t_exp = st.columns([3, 1])
    with col_t_title:
        st.write("Daily Projection Ledger:")
    with col_t_exp:
        # Export as CSV or plain text
        export_format = st.selectbox("Export Format", ["CSV", "Plain Text"], key="exp_fmt")
        if export_format == "CSV":
            csv_buf = io.StringIO()
            df_export = df_days[['day', 'net', 'balance']].copy()
            df_export.to_csv(csv_buf, index=False)
            st.download_button("Download Ledger CSV", csv_buf.getvalue(), file_name=f"ebbline_projection_run_{run_id}.csv", mime="text/csv")
        else:
            txt_lines = [
                f"Ebbline Projection Report for Run {run_id}",
                f"Anchor Balance: {format_inr(run_header['anchor_balance'])} as of {format_date(run_header['anchor_date'])}",
                f"Horizon: {format_date(run_header['horizon_start'])} to {format_date(run_header['horizon_end'])}",
                f"Lowest Balance: {format_inr(run_header['min_balance'])} on {format_date(run_header['min_balance_date'])}",
                f"First Breach Date: {format_date(run_header['first_breach_date']) if run_header['first_breach_date'] else 'None'}",
                f"Days Below Buffer: {run_header['days_below_buffer']}",
                "",
                "Day, Net Amount, Projected Balance"
            ]
            for _, r in df_days.iterrows():
                txt_lines.append(f"{format_date(r['day'])}, {format_inr(r['net'])}, {format_inr(r['balance'])}")
            st.download_button("Download Ledger Text", "\n".join(txt_lines), file_name=f"ebbline_projection_run_{run_id}.txt", mime="text/plain")

    display_df = df_days[['day', 'net', 'balance']].copy()
    display_df['Day'] = display_df['day'].apply(format_date)
    display_df['Net Flow'] = display_df['net'].apply(format_inr)
    display_df['Projected Balance'] = display_df['balance'].apply(format_inr)
    st.dataframe(display_df[['Day', 'Net Flow', 'Projected Balance']], use_container_width=True)

# Screen 3: Scenario Compare
def screen_scenario_compare():
    st.subheader("Scenario Comparison")
    accounts = get_accounts()
    scenarios = get_scenarios()
    if len(scenarios) < 2:
        st.write("At least two scenarios are required for comparison.")
        return

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        acc_dict = {f"{a['name']} (ID {a['account_id']})": a['account_id'] for a in accounts}
        sel_acc_label = st.selectbox("Account", list(acc_dict.keys()), key="comp_acc")
        sel_acc_id = acc_dict[sel_acc_label]
    with col_c2:
        scen_a_dict = {f"{s['name']} (ID {s['scenario_id']})": s['scenario_id'] for s in scenarios}
        sel_a_label = st.selectbox("Scenario A (Baseline)", list(scen_a_dict.keys()), index=0, key="comp_a")
        scen_a_id = scen_a_dict[sel_a_label]
    with col_c3:
        scen_b_dict = {f"{s['name']} (ID {s['scenario_id']})": s['scenario_id'] for s in scenarios if s['scenario_id'] != scen_a_id}
        if not scen_b_dict:
            st.write("Please create a second scenario to compare.")
            return
        sel_b_label = st.selectbox("Scenario B (Comparison)", list(scen_b_dict.keys()), index=0, key="comp_b")
        scen_b_id = scen_b_dict[sel_b_label]

    # Run procedure compare_scenarios
    try:
        conn = app.db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("compare_scenarios", [scen_a_id, scen_b_id, sel_acc_id])
        results = list(cur.stored_results())
        row = results[0].fetchone() if results else None
        cur.close()
        conn.close()
    except Exception as ex:
        st.markdown(f"""
            <div class="ebb-error-box">
                Comparison error: {ex}
            </div>
        """, unsafe_allow_html=True)
        return

    if not row:
        st.write("No comparison data returned.")
        return

    # Comparison Delta Cards
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Lowest Balance Delta</div>
                <div class="ebb-card-val" style="color: {'#2E8B6B' if row['min_balance_delta'] >= 0 else '#D2453D'};">
                    {format_inr(row['min_balance_delta'])}
                </div>
                <div class="ebb-card-sub">A: {format_inr(row['min_balance_a'])} | B: {format_inr(row['min_balance_b'])}</div>
            </div>
        """, unsafe_allow_html=True)
    with d2:
        shift_val = row['breach_shift_days']
        shift_str = f"{shift_val} days later" if shift_val and shift_val > 0 else (f"{abs(shift_val)} days earlier" if shift_val and shift_val < 0 else "No shift")
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Breach Date Shift</div>
                <div class="ebb-card-val">{shift_str}</div>
                <div class="ebb-card-sub">A: {format_date(row['first_breach_a']) if row['first_breach_a'] else 'None'} | B: {format_date(row['first_breach_b']) if row['first_breach_b'] else 'None'}</div>
            </div>
        """, unsafe_allow_html=True)
    with d3:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Days Below Buffer Delta</div>
                <div class="ebb-card-val" style="color: {'#2E8B6B' if row['days_below_delta'] <= 0 else '#D2453D'};">
                    {row['days_below_delta']} days
                </div>
                <div class="ebb-card-sub">A: {row['days_below_a']} days | B: {row['days_below_b']} days</div>
            </div>
        """, unsafe_allow_html=True)

    # Overlaid Chart
    run_a_id = row['run_a_id']
    run_b_id = row['run_b_id']
    days_a = app.db.fetch_all("SELECT day, balance FROM projection_day WHERE run_id = %s ORDER BY day", (run_a_id,))
    days_b = app.db.fetch_all("SELECT day, balance FROM projection_day WHERE run_id = %s ORDER BY day", (run_b_id,))

    acc_info = app.db.fetch_one("SELECT buffer_min FROM account WHERE account_id = %s", (sel_acc_id,))
    buffer_val = float(acc_info['buffer_min'])

    df_a = pd.DataFrame(days_a)
    df_a['scenario'] = f"{row['scenario_a_name']} (Scenario A)"
    df_a['balance_float'] = df_a['balance'].astype(float)

    df_b = pd.DataFrame(days_b)
    df_b['scenario'] = f"{row['scenario_b_name']} (Scenario B)"
    df_b['balance_float'] = df_b['balance'].astype(float)

    df_comb = pd.concat([df_a, df_b], ignore_index=True)
    df_comb['buffer'] = buffer_val

    chart_lines = alt.Chart(df_comb).mark_line(strokeWidth=2.5).encode(
        x=alt.X('day:T', title='Timeline Date'),
        y=alt.Y('balance_float:Q', title='Account Balance (INR)'),
        color=alt.Color('scenario:N', scale=alt.Scale(
            domain=[f"{row['scenario_a_name']} (Scenario A)", f"{row['scenario_b_name']} (Scenario B)"],
            range=['#0F6B73', '#4F6FA8']
        ))
    )

    buf_rule = alt.Chart(df_comb).mark_line(color='#D9922E', strokeDash=[6, 4], strokeWidth=2).encode(
        x='day:T',
        y='buffer:Q'
    )

    st.altair_chart((chart_lines + buf_rule).properties(height=380, width='container'), use_container_width=True)
    st.caption("Scenario A drawn in deep teal. Scenario B drawn in dusk blue. Safety buffer drawn as amber dashed line.")

    # Create New Scenario Form
    st.write("")
    st.subheader("Create New What If Scenario")
    with st.form("form_create_scenario"):
        new_scen_name = st.text_input("Scenario Name", placeholder="e.g. Cut Discretionary Spending 50 Percent")
        new_scen_desc = st.text_input("Description", placeholder="e.g. Reduce dining and cancel gym membership")
        
        rules = app.db.fetch_all("SELECT rule_id, label, amount FROM recurring_rule WHERE account_id = %s AND is_active = TRUE", (sel_acc_id,))
        rule_map = {r['rule_id']: f"Rule {r['rule_id']}: {r['label']} ({format_inr(r['amount'])})" for r in rules}
        
        target_rule = st.selectbox("Target Rule (or leave blank for event)", [None] + list(rule_map.keys()), format_func=lambda x: rule_map.get(x, "None"))
        action = st.selectbox("Action", ["SKIP", "SHIFT_DAYS", "SCALE"])
        act_val = st.number_input("Action Value (e.g. 5 for shift days, 0.50 for scale)", value=0.00, step=0.10)
        from_d = st.date_input("From Date", value=datetime.date.today())
        to_d = st.date_input("To Date", value=datetime.date.today() + datetime.timedelta(days=90))
        
        btn_save_scen = st.form_submit_button("Save Scenario & Changes")
        if btn_save_scen:
            if not new_scen_name.strip():
                st.error("Scenario name is required.")
            elif to_d < from_d:
                st.error("To Date cannot be earlier than From Date.")
            elif not target_rule:
                st.error("Please select a target rule.")
            else:
                try:
                    # Insert scenario
                    app.db.execute_query(
                        "INSERT INTO scenario (name, description) VALUES (%s, %s)",
                        (new_scen_name.strip(), new_scen_desc.strip())
                    )
                    new_s = app.db.fetch_one("SELECT scenario_id FROM scenario WHERE name = %s", (new_scen_name.strip(),))
                    new_s_id = new_s['scenario_id']
                    
                    # Call procedure add_scenario_change to get overlap and lock protection
                    cur_p = app.db.get_connection().cursor()
                    cur_p.callproc("add_scenario_change", [
                        new_s_id, target_rule, None, action, act_val if action != "SKIP" else None, from_d, to_d
                    ])
                    cur_p.close()
                    st.success(f"Scenario '{new_scen_name}' created successfully with override change.")
                    st.rerun()
                except Exception as ex:
                    st.markdown(f"""
                        <div class="ebb-error-box">
                            Failed to save scenario change: {ex}
                        </div>
                    """, unsafe_allow_html=True)

# Screen 4: Explain and Fix
def screen_explain_and_fix():
    st.subheader("Explain Day and Suggest Fixes")
    accounts = get_accounts()
    if not accounts:
        st.write("No active accounts found.")
        return

    col_acc, col_run = st.columns(2)
    with col_acc:
        acc_dict = {f"{a['name']} (ID {a['account_id']})": a['account_id'] for a in accounts}
        sel_acc_label = st.selectbox("Account", list(acc_dict.keys()), key="exp_acc")
        sel_acc_id = acc_dict[sel_acc_label]
    with col_run:
        runs = app.db.fetch_all(
            "SELECT pr.run_id, pr.scenario_id, s.name AS scenario_name, pr.first_breach_date, pr.min_balance "
            "FROM projection_run pr JOIN scenario s ON s.scenario_id = pr.scenario_id "
            "WHERE pr.account_id = %s ORDER BY pr.run_id DESC LIMIT 10",
            (sel_acc_id,)
        )
        if not runs:
            st.write("No projection runs recorded for this account. Build a projection first.")
            return
        run_options = {f"Run {r['run_id']} - {r['scenario_name']} (Lowest: {format_inr(r['min_balance'])})": r['run_id'] for r in runs}
        sel_run_label = st.selectbox("Select Projection Run", list(run_options.keys()))
        sel_run_id = run_options[sel_run_label]

    run_info = next(r for r in runs if r['run_id'] == sel_run_id)
    default_day = run_info['first_breach_date'] or datetime.date.today()

    target_day = st.date_input("Query Day to Explain (defaults to First Breach Date)", value=default_day)

    # Call explain_day procedure
    try:
        conn = app.db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("explain_day", [sel_run_id, target_day])
        results = list(cur.stored_results())
        summary = results[0].fetchone() if len(results) > 0 else None
        events = results[1].fetchall() if len(results) > 1 else []
        categories = results[2].fetchall() if len(results) > 2 else []
        cur.close()
        conn.close()
    except Exception as ex:
        st.markdown(f"""
            <div class="ebb-error-box">
                Explain day procedure error: {ex}
            </div>
        """, unsafe_allow_html=True)
        return

    if summary:
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.markdown(f"""
                <div class="ebb-card">
                    <div class="ebb-card-title">Anchor Balance</div>
                    <div class="ebb-card-val">{format_inr(summary['anchor_balance'])}</div>
                    <div class="ebb-card-sub">As of {format_date(summary['anchor_date'])}</div>
                </div>
            """, unsafe_allow_html=True)
        with ec2:
            st.markdown(f"""
                <div class="ebb-card">
                    <div class="ebb-card-title">Day Stored Balance</div>
                    <div class="ebb-card-val">{format_inr(summary['stored_day_balance'])}</div>
                    <div class="ebb-card-sub">On {format_date(summary['query_day'])}</div>
                </div>
            """, unsafe_allow_html=True)
        with ec3:
            net_change = Decimal(str(summary['stored_day_balance'])) - Decimal(str(summary['anchor_balance']))
            st.markdown(f"""
                <div class="ebb-card">
                    <div class="ebb-card-title">Cumulative Net Flow</div>
                    <div class="ebb-card-val" style="color: {'#2E8B6B' if net_change >= 0 else '#D2453D'};">
                        {format_inr(net_change)}
                    </div>
                    <div class="ebb-card-sub">{len(events)} events driving the balance</div>
                </div>
            """, unsafe_allow_html=True)

    # Events driving dip
    st.write("Events Driving Balance up to Query Day (Largest Outflows First):")
    if events:
        event_rows = []
        for e in events:
            event_rows.append({
                "Date": format_date(e['due_date']),
                "Amount": format_inr(e['amount']),
                "Label": e['label'],
                "Category": e['category_name'],
                "Nature": "Essential" if e['is_essential'] else "Discretionary",
                "Running Balance": format_inr(e['running_balance'])
            })
        st.dataframe(pd.DataFrame(event_rows), use_container_width=True)

    # Category breakdown
    if categories:
        st.write("Category Outflows Driving the Dip:")
        cat_rows = []
        for c in categories:
            cat_rows.append({
                "Category": c['name'],
                "Nature": "Essential" if c['is_essential'] else "Discretionary",
                "Event Count": c['event_count'],
                "Total Amount": format_inr(c['total_amount'])
            })
        st.dataframe(pd.DataFrame(cat_rows), use_container_width=True)

    # Suggest Fixes section
    st.write("")
    st.subheader("Actionable Fix Suggestions")
    try:
        conn = app.db.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.callproc("suggest_fixes", [sel_run_id])
        res_fixes = list(cur.stored_results())
        fixes = res_fixes[0].fetchall() if res_fixes else []
        cur.close()
        conn.close()
    except Exception as ex:
        st.markdown(f"""
            <div class="ebb-error-box">
                Fix suggestion procedure error: {ex}
            </div>
        """, unsafe_allow_html=True)
        return

    if not fixes or "shortfall_target" not in fixes[0]:
        st.write("No breach detected in this run; no fixes required.")
    else:
        st.markdown(f"""
            <div class="ebb-card">
                <div class="ebb-card-title">Shortfall to Cover</div>
                <div class="ebb-card-val" style="color: #D2453D;">{format_inr(fixes[0]['shortfall_target'])}</div>
                <div class="ebb-card-sub">Note: {fixes[0]['scope_note']}</div>
            </div>
        """, unsafe_allow_html=True)

        fix_display = []
        for f in fixes:
            fix_display.append({
                "Action": f"Skip {f['source_type'].lower()} {f['source_id']}",
                "Due Date": format_date(f['due_date']),
                "Label": f['label'],
                "Category": f['category_name'],
                "Immediate Saving": format_inr(f['saving']),
                "Cumulative Saving": format_inr(f['cum_saving'])
            })
        st.dataframe(pd.DataFrame(fix_display), use_container_width=True)

        # Button to save suggestions as a new scenario
        if st.button("Save Suggestions as New Scenario"):
            try:
                new_name = f"Fix for Run {sel_run_id} ({datetime.date.today().strftime('%d %b %Y')})"
                app.db.execute_query(
                    "INSERT INTO scenario (name, description) VALUES (%s, %s)",
                    (new_name, "Automated fix scenario skipping discretionary outflows to prevent first breach")
                )
                new_scen = app.db.fetch_one("SELECT scenario_id FROM scenario WHERE name = %s", (new_name,))
                new_scen_id = new_scen['scenario_id']

                for f in fixes:
                    rule_id = f['source_id'] if f['source_type'] == 'RULE' else None
                    event_id = f['source_id'] if f['source_type'] == 'EVENT' else None
                    app.db.execute_query(
                        "INSERT INTO scenario_change (scenario_id, rule_id, event_id, action, value, from_date, to_date) "
                        "VALUES (%s, %s, %s, 'SKIP', NULL, %s, %s)",
                        (new_scen_id, rule_id, event_id, f['due_date'], f['due_date'])
                    )
                st.markdown(f"""
                    <div class="ebb-success-box">
                        New scenario '{new_name}' created with {len(fixes)} skip changes.
                    </div>
                """, unsafe_allow_html=True)
            except Exception as ex:
                st.markdown(f"""
                    <div class="ebb-error-box">
                        Failed to create automated fix scenario: {ex}
                    </div>
                """, unsafe_allow_html=True)

# Screen 5: Reserve and Accuracy
def screen_reserve_and_accuracy():
    st.subheader("Reserve Schedule and Forecast Accuracy")
    accounts = get_accounts()
    if not accounts:
        st.write("No active accounts found.")
        return

    acc_dict = {f"{a['name']} (ID {a['account_id']})": a['account_id'] for a in accounts}
    sel_acc_label = st.selectbox("Select Account", list(acc_dict.keys()), key="res_acc")
    sel_acc_id = acc_dict[sel_acc_label]

    tab_reserve, tab_plan, tab_backtest = st.tabs([
        "Reserve Schedule", "Plan vs Actual", "Forecast Backtest"
    ])

    with tab_reserve:
        st.write("Monthly reserve set-aside required for quarterly and yearly obligations:")
        reserves = app.db.fetch_all(
            "SELECT label, total_obligation, unit, every_n, period_months, monthly_set_aside "
            "FROM v_reserve_schedule WHERE account_id = %s ORDER BY monthly_set_aside DESC",
            (sel_acc_id,)
        )
        if reserves:
            res_rows = []
            total_monthly_set_aside = Decimal('0.00')
            for r in reserves:
                total_monthly_set_aside += Decimal(str(r['monthly_set_aside']))
                res_rows.append({
                    "Obligation": r['label'],
                    "Total Amount": format_inr(r['total_obligation']),
                    "Cycle": f"Every {r['every_n']} {r['unit'].lower()}(s) ({r['period_months']} months)",
                    "Monthly Set-Aside": format_inr(r['monthly_set_aside'])
                })
            st.markdown(f"""
                <div class="ebb-card">
                    <div class="ebb-card-title">Total Monthly Reserve Needed</div>
                    <div class="ebb-card-val">{format_inr(total_monthly_set_aside)}</div>
                    <div class="ebb-card-sub">Sum of set-asides across {len(reserves)} recurring long term obligations</div>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(res_rows), use_container_width=True)
        else:
            st.write("No quarterly or yearly obligations found for this account.")

    with tab_plan:
        st.write("Comparison of planned rule amounts against posted actuals per month with a 3-month rolling average:")
        plan_data = app.db.fetch_all(
            "SELECT rule_label, ym, planned_amount, actual_amount, variance, variance_pct, avg_3m "
            "FROM v_plan_vs_actual WHERE account_id = %s ORDER BY ym DESC, rule_label",
            (sel_acc_id,)
        )
        if plan_data:
            p_rows = []
            for p in plan_data:
                p_rows.append({
                    "Month": p['ym'],
                    "Rule": p['rule_label'],
                    "Planned": format_inr(p['planned_amount']),
                    "Actual": format_inr(p['actual_amount']),
                    "Variance": format_inr(p['variance']),
                    "Variance Pct": f"{p['variance_pct']}%",
                    "3-Month Avg": format_inr(p['avg_3m'])
                })
            st.dataframe(pd.DataFrame(p_rows), use_container_width=True)
        else:
            st.write("No plan vs actual data recorded.")

    with tab_backtest:
        st.write("Forecast error evaluated against recorded past checkpoints:")
        st.info("Backtest on synthetic data does not show real world accuracy.")
        try:
            conn = app.db.get_connection()
            cur = conn.cursor(dictionary=True)
            cur.callproc("backtest", [sel_acc_id])
            res = list(cur.stored_results())
            rows = res[0].fetchall() if res else []
            cur.close()
            conn.close()

            if rows:
                b_rows = []
                for r in rows:
                    b_rows.append({
                        "Checkpoint Date": format_date(r['checkpoint_date']),
                        "Actual Balance": format_inr(r['actual_balance']),
                        "Projected Balance": format_inr(r['projected_balance']),
                        "Absolute Error": format_inr(r['abs_error']),
                        "Percentage Error": f"{r['pct_error']}%",
                        "MAE": format_inr(r['overall_mae']),
                        "RMSE": format_inr(r['overall_rmse'])
                    })
                st.dataframe(pd.DataFrame(b_rows), use_container_width=True)
            else:
                st.write("No historical projection checkpoints available for backtest comparison on this account.")
        except Exception as ex:
            if "45001" in str(ex):
                st.write("Account has fewer than 2 checkpoints; at least 2 checkpoints are required to perform a forecast backtest.")
            else:
                st.markdown(f"""
                    <div class="ebb-error-box">
                        Backtest error: {ex}
                    </div>
                """, unsafe_allow_html=True)

# Main Application Router
def main():
    render_header()
    
    # Left side navigation
    st.sidebar.title("Navigation")
    screen = st.sidebar.radio(
        "Go to",
        ["Rules and Events", "Projection", "Scenario Compare", "Explain and Fix", "Reserve and Accuracy"]
    )
    st.sidebar.write("")
    st.sidebar.caption("Ebbline Personal Finance Engine v1.0")

    if screen == "Rules and Events":
        screen_rules_and_events()
    elif screen == "Projection":
        screen_projection()
    elif screen == "Scenario Compare":
        screen_scenario_compare()
    elif screen == "Explain and Fix":
        screen_explain_and_fix()
    elif screen == "Reserve and Accuracy":
        screen_reserve_and_accuracy()

if __name__ == "__main__":
    main()
