import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Account, ExplainData, SuggestFixesData } from '../types';

interface Props {
  accounts: Account[];
  selectedAccountId: number;
  onSelectAccount: (id: number) => void;
  onRefreshScenarios: () => void;
}

export const ExplainAndFixScreen: React.FC<Props> = ({
  accounts,
  selectedAccountId,
  onSelectAccount,
  onRefreshScenarios
}) => {
  const [runId, setRunId] = useState<number>(1);
  const [targetDate, setTargetDate] = useState<string>('2026-10-18');
  const [explainData, setExplainData] = useState<ExplainData | null>(null);
  const [fixesData, setFixesData] = useState<SuggestFixesData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Automatically fetch latest run for the selected account
  const initLatestRun = async () => {
    try {
      const proj = await api.buildProjection(selectedAccountId, 1, 365);
      setRunId(proj.run_id);
      if (proj.first_breach_date) {
        setTargetDate(proj.first_breach_date);
      } else {
        setTargetDate(proj.min_balance_date || '2026-10-18');
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    initLatestRun();
  }, [selectedAccountId]);

  const loadAnalytics = async () => {
    if (!runId || !targetDate) return;
    setLoading(true);
    setError(null);
    try {
      const [exp, fix] = await Promise.all([
        api.explainDay(runId, targetDate),
        api.suggestFixes(runId)
      ]);
      setExplainData(exp);
      setFixesData(fix);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [runId, targetDate]);

  const handleSaveFixes = async () => {
    if (!runId) return;
    setError(null);
    setMessage(null);
    try {
      const res = await api.saveFixes(runId);
      setMessage(`Automated fix scenario '${res.name}' created with ${res.fixes_count} skips.`);
      onRefreshScenarios();
    } catch (err: any) {
      setError(err.message || 'Failed to save fixes');
    }
  };

  return (
    <div>
      <div className="ebb-page-header">
        <h1 className="ebb-page-title">Explain Day and Suggest Fixes</h1>
        <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'flex-end' }}>
          <div>
            <label className="ebb-form-label">Account</label>
            <select
              className="ebb-select"
              style={{ width: 300 }}
              value={selectedAccountId}
              onChange={(e) => onSelectAccount(Number(e.target.value))}
            >
              {accounts.map((a) => (
                <option key={a.account_id} value={a.account_id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="ebb-form-label">Run ID</label>
            <input
              type="number"
              className="ebb-input"
              style={{ width: 120 }}
              value={runId}
              onChange={(e) => setRunId(Number(e.target.value))}
            />
          </div>

          <div>
            <label className="ebb-form-label">Query Day to Explain</label>
            <input
              type="date"
              className="ebb-input"
              style={{ width: 180 }}
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
            />
          </div>

          <button className="ebb-btn-primary" onClick={loadAnalytics} disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {error && <div className="ebb-error-banner">{error}</div>}
      {message && <div className="ebb-success-banner">{message}</div>}

      {explainData && (
        <>
          <div className="ebb-card-grid-3">
            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Anchor Balance</div>
              <div className="ebb-metric-value">{explainData.anchor_balance_formatted}</div>
              <div className="ebb-metric-sub">As of {explainData.anchor_date_formatted}</div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Day Stored Balance</div>
              <div className="ebb-metric-value">{explainData.stored_day_balance_formatted}</div>
              <div className="ebb-metric-sub">On {explainData.query_day_formatted}</div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Cumulative Net Outflow</div>
              <div
                className="ebb-metric-value"
                style={{ color: explainData.cumulative_net >= 0 ? 'var(--safe-green)' : 'var(--breach-red)' }}
              >
                {explainData.cumulative_net_formatted}
              </div>
              <div className="ebb-metric-sub">{explainData.events.length} transactions driving the balance</div>
            </div>
          </div>

          <div className="ebb-card">
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-ink)' }}>
              Events Driving Balance up to Query Day (Largest Outflows First)
            </h2>
            <div style={{ maxHeight: 340, overflowY: 'auto' }}>
              <table className="ebb-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th style={{ textAlign: 'right' }}>Amount</th>
                    <th>Label</th>
                    <th>Category</th>
                    <th>Nature</th>
                    <th style={{ textAlign: 'right' }}>Running Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {explainData.events.map((e) => (
                    <tr key={e.event_id}>
                      <td>{e.due_date_formatted}</td>
                      <td
                        style={{
                          textAlign: 'right',
                          fontWeight: 600,
                          color: e.amount < 0 ? 'var(--breach-red)' : 'var(--safe-green)'
                        }}
                      >
                        {e.amount_formatted}
                      </td>
                      <td style={{ fontWeight: 600 }}>{e.label}</td>
                      <td>{e.category_name}</td>
                      <td>{e.is_essential ? 'Essential' : 'Discretionary'}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>{e.running_balance_formatted}</td>
                    </tr>
                  ))}
                  {explainData.events.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 20, color: 'var(--text-slate)' }}>
                        No transactions found prior to this date.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="ebb-card">
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-ink)' }}>
              Category Totals Driving the Dip
            </h2>
            <table className="ebb-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Nature</th>
                  <th style={{ textAlign: 'right' }}>Event Count</th>
                  <th style={{ textAlign: 'right' }}>Total Outflow</th>
                </tr>
              </thead>
              <tbody>
                {explainData.categories.map((c, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{c.category_name}</td>
                    <td>{c.is_essential ? 'Essential' : 'Discretionary'}</td>
                    <td style={{ textAlign: 'right' }}>{c.event_count}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: c.total_amount < 0 ? 'var(--breach-red)' : 'var(--safe-green)' }}>
                      {c.total_amount_formatted}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {fixesData && (
        <div className="ebb-card" style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--text-ink)' }}>
                Actionable Fix Suggestions
              </h2>
              {fixesData.scope_note && (
                <div style={{ fontSize: 12, color: 'var(--text-slate)', marginTop: 4 }}>
                  Scope note: {fixesData.scope_note}
                </div>
              )}
            </div>

            {fixesData.has_breach && (
              <button className="ebb-btn-primary" onClick={handleSaveFixes}>
                Save Suggestions as New Scenario
              </button>
            )}
          </div>

          {!fixesData.has_breach ? (
            <div style={{ color: 'var(--safe-green)', fontWeight: 600, padding: 12 }}>
              {fixesData.message || 'No breach detected in this run; no fixes required.'}
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 16, padding: 14, backgroundColor: '#FDF2F1', borderRadius: 6, display: 'inline-block' }}>
                <span style={{ fontSize: 13, color: 'var(--text-slate)' }}>Shortfall Target to Cover: </span>
                <strong style={{ fontSize: 16, color: 'var(--breach-red)' }}>
                  {fixesData.shortfall_target_formatted}
                </strong>
              </div>

              <table className="ebb-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Due Date</th>
                    <th>Label</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Immediate Saving</th>
                    <th style={{ textAlign: 'right' }}>Cumulative Saving</th>
                  </tr>
                </thead>
                <tbody>
                  {fixesData.fixes?.map((f, idx) => (
                    <tr key={idx}>
                      <td>
                        <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600, backgroundColor: '#F0F6F6', color: 'var(--primary-teal)' }}>
                          Skip {f.source_type.toLowerCase()} {f.source_id}
                        </span>
                      </td>
                      <td>{f.due_date_formatted}</td>
                      <td style={{ fontWeight: 600 }}>{f.label}</td>
                      <td>{f.category_name}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--safe-green)' }}>
                        {f.saving_formatted}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>
                        {f.cum_saving_formatted}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
};
