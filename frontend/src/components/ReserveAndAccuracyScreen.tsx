import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Account, ReserveScheduleData, PlanVsActualRow, BacktestData } from '../types';

interface Props {
  accounts: Account[];
  selectedAccountId: number;
  onSelectAccount: (id: number) => void;
}

export const ReserveAndAccuracyScreen: React.FC<Props> = ({
  accounts,
  selectedAccountId,
  onSelectAccount
}) => {
  const [activeTab, setActiveTab] = useState<'reserve' | 'plan' | 'backtest'>('reserve');
  const [reserveData, setReserveData] = useState<ReserveScheduleData | null>(null);
  const [planRows, setPlanRows] = useState<PlanVsActualRow[]>([]);
  const [backtestData, setBacktestData] = useState<BacktestData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [res, pl, bk] = await Promise.all([
        api.getReserveSchedule(selectedAccountId),
        api.getPlanVsActual(selectedAccountId),
        api.getBacktest(selectedAccountId)
      ]);
      setReserveData(res);
      setPlanRows(pl);
      setBacktestData(bk);
    } catch (err: any) {
      setError(err.message || 'Failed to load reserve and accuracy data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedAccountId]);

  return (
    <div>
      <div className="ebb-page-header">
        <h1 className="ebb-page-title">Reserve Schedule and Forecast Accuracy</h1>
        <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-slate)' }}>Account:</label>
          <select
            className="ebb-select"
            style={{ width: 320 }}
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
      </div>

      {error && <div className="ebb-error-banner">{error}</div>}

      <div className="ebb-tabs">
        <button
          className={`ebb-tab ${activeTab === 'reserve' ? 'active' : ''}`}
          onClick={() => setActiveTab('reserve')}
        >
          Reserve Schedule
        </button>
        <button
          className={`ebb-tab ${activeTab === 'plan' ? 'active' : ''}`}
          onClick={() => setActiveTab('plan')}
        >
          Plan vs Actual
        </button>
        <button
          className={`ebb-tab ${activeTab === 'backtest' ? 'active' : ''}`}
          onClick={() => setActiveTab('backtest')}
        >
          Forecast Backtest
        </button>
      </div>

      {activeTab === 'reserve' && reserveData && (
        <>
          <div className="ebb-card" style={{ maxWidth: 400 }}>
            <div className="ebb-metric-label">Total Monthly Reserve Needed</div>
            <div className="ebb-metric-value">{reserveData.total_monthly_reserve_formatted}</div>
            <div className="ebb-metric-sub">
              Sum of set-asides across {reserveData.rows.length} long term recurring obligations
            </div>
          </div>

          <div className="ebb-card">
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-ink)' }}>
              Quarterly and Annual Obligation Breakdown
            </h2>
            <table className="ebb-table">
              <thead>
                <tr>
                  <th>Obligation</th>
                  <th style={{ textAlign: 'right' }}>Total Amount</th>
                  <th>Cadence</th>
                  <th style={{ textAlign: 'right' }}>Monthly Set-Aside Required</th>
                </tr>
              </thead>
              <tbody>
                {reserveData.rows.map((r, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{r.label}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{r.total_obligation_formatted}</td>
                    <td>{r.cycle_formatted}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--primary-teal)' }}>
                      {r.monthly_set_aside_formatted}
                    </td>
                  </tr>
                ))}
                {reserveData.rows.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: 20, color: 'var(--text-slate)' }}>
                      No quarterly or yearly recurring obligations registered for this account.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'plan' && (
        <div className="ebb-card">
          <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-ink)' }}>
            Plan vs Actual Performance
          </h2>
          <table className="ebb-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Rule Label</th>
                <th style={{ textAlign: 'right' }}>Planned</th>
                <th style={{ textAlign: 'right' }}>Actual</th>
                <th style={{ textAlign: 'right' }}>Variance</th>
                <th style={{ textAlign: 'right' }}>Variance Pct</th>
                <th style={{ textAlign: 'right' }}>3-Month Rolling Avg</th>
              </tr>
            </thead>
            <tbody>
              {planRows.map((p, idx) => (
                <tr key={idx}>
                  <td>{p.month}</td>
                  <td style={{ fontWeight: 600 }}>{p.rule_label}</td>
                  <td style={{ textAlign: 'right' }}>{p.planned_formatted}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{p.actual_formatted}</td>
                  <td
                    style={{
                      textAlign: 'right',
                      fontWeight: 600,
                      color: p.variance < 0 ? 'var(--breach-red)' : 'var(--safe-green)'
                    }}
                  >
                    {p.variance_formatted}
                  </td>
                  <td style={{ textAlign: 'right' }}>{p.variance_pct}%</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{p.avg_3m_formatted}</td>
                </tr>
              ))}
              {planRows.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 20, color: 'var(--text-slate)' }}>
                    No posted actual transactions recorded for this account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'backtest' && backtestData && (
        <>
          {backtestData.disclaimer && (
            <div style={{ padding: '12px 16px', backgroundColor: '#F0F6F6', borderRadius: 6, fontSize: 13, color: 'var(--primary-teal)', fontWeight: 500, marginBottom: 20 }}>
              {backtestData.disclaimer}
            </div>
          )}

          {backtestData.error ? (
            <div className="ebb-card" style={{ color: 'var(--text-slate)', padding: 24, textAlign: 'center' }}>
              {backtestData.error}
            </div>
          ) : (
            <>
              <div className="ebb-card-grid-3">
                <div className="ebb-metric-card">
                  <div className="ebb-metric-label">Mean Absolute Error (MAE)</div>
                  <div className="ebb-metric-value">{backtestData.overall_mae_formatted}</div>
                  <div className="ebb-metric-sub">Average projection deviation across past checkpoints</div>
                </div>

                <div className="ebb-metric-card">
                  <div className="ebb-metric-label">Root Mean Square Error (RMSE)</div>
                  <div className="ebb-metric-value">{backtestData.overall_rmse_formatted}</div>
                  <div className="ebb-metric-sub">Penalizes large forecast variance outliers</div>
                </div>

                <div className="ebb-metric-card">
                  <div className="ebb-metric-label">Checkpoints Compared</div>
                  <div className="ebb-metric-value">{backtestData.comparisons.length}</div>
                  <div className="ebb-metric-sub">Historical real checkpoints evaluated</div>
                </div>
              </div>

              <div className="ebb-card">
                <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-ink)' }}>
                  Checkpoint Comparison Ledger
                </h2>
                <table className="ebb-table">
                  <thead>
                    <tr>
                      <th>Checkpoint Date</th>
                      <th style={{ textAlign: 'right' }}>Actual Stored Balance</th>
                      <th style={{ textAlign: 'right' }}>Forecasted Balance</th>
                      <th style={{ textAlign: 'right' }}>Absolute Error</th>
                      <th style={{ textAlign: 'right' }}>Percentage Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtestData.comparisons.map((c, idx) => (
                      <tr key={idx}>
                        <td>{c.checkpoint_date_formatted}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>{c.actual_balance_formatted}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>{c.projected_balance_formatted}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--breach-red)' }}>
                          {c.abs_error_formatted}
                        </td>
                        <td style={{ textAlign: 'right' }}>{c.pct_error}%</td>
                      </tr>
                    ))}
                    {backtestData.comparisons.length === 0 && (
                      <tr>
                        <td colSpan={5} style={{ textAlign: 'center', padding: 20, color: 'var(--text-slate)' }}>
                          No comparative checkpoints available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};
