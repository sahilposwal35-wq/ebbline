import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import { api } from '../api';
import { Account, Scenario, ProjectionData } from '../types';

interface Props {
  accounts: Account[];
  scenarios: Scenario[];
  selectedAccountId: number;
  onSelectAccount: (id: number) => void;
}

export const ProjectionScreen: React.FC<Props> = ({
  accounts,
  scenarios,
  selectedAccountId,
  onSelectAccount
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<number>(1);
  const [horizonDays, setHorizonDays] = useState<number>(365);
  const [data, setData] = useState<ProjectionData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const executeBuild = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.buildProjection(selectedAccountId, selectedScenarioId, horizonDays);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to build projection');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeBuild();
  }, [selectedAccountId, selectedScenarioId, horizonDays]);

  const handleExportCsv = () => {
    if (!data) return;
    const header = 'day,net,balance\n';
    const rows = data.ledger.map((r) => `${r.day},${r.net},${r.balance}`).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ebbline_projection_run_${data.run_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportText = () => {
    if (!data) return;
    const lines = [
      `Ebbline Projection Report for Run ${data.run_id}`,
      `Anchor Balance: ${data.anchor_balance_formatted} as of ${data.anchor_date_formatted}`,
      `Horizon: ${data.horizon_start_formatted} to ${data.horizon_end_formatted}`,
      `Lowest Balance: ${data.min_balance_formatted} on ${data.min_balance_date_formatted}`,
      `First Breach Date: ${data.first_breach_date_formatted}`,
      `Days Below Buffer: ${data.days_below_buffer}`,
      '',
      'Day, Net Amount, Projected Balance',
      ...data.ledger.map((r) => `${r.day_formatted}, ${r.net_formatted}, ${r.balance_formatted}`)
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ebbline_projection_run_${data.run_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="ebb-page-header">
        <h1 className="ebb-page-title">Cash Flow Projection</h1>
        <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'flex-end' }}>
          <div>
            <label className="ebb-form-label">Account</label>
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

          <div>
            <label className="ebb-form-label">Scenario</label>
            <select
              className="ebb-select"
              style={{ width: 260 }}
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(Number(e.target.value))}
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="ebb-form-label">Horizon ({horizonDays} days)</label>
            <input
              type="range"
              min={30}
              max={730}
              step={15}
              value={horizonDays}
              onChange={(e) => setHorizonDays(Number(e.target.value))}
              style={{ width: 180, accentColor: 'var(--primary-teal)' }}
            />
          </div>

          <button className="ebb-btn-primary" onClick={executeBuild} disabled={loading}>
            {loading ? 'Building...' : 'Build Projection'}
          </button>
        </div>
      </div>

      {error && <div className="ebb-error-banner">{error}</div>}

      {data && (
        <>
          <div className="ebb-card-grid-4">
            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Anchor Balance</div>
              <div className="ebb-metric-value">{data.anchor_balance_formatted}</div>
              <div className="ebb-metric-sub">As of {data.anchor_date_formatted}</div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Lowest Balance</div>
              <div className="ebb-metric-value">{data.min_balance_formatted}</div>
              <div className="ebb-metric-sub">Recorded on {data.min_balance_date_formatted}</div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">First Breach Date</div>
              <div
                className="ebb-metric-value"
                style={{ color: data.first_breach_date ? 'var(--breach-red)' : 'var(--safe-green)' }}
              >
                {data.first_breach_date_formatted}
              </div>
              <div className="ebb-metric-sub">
                {data.first_breach_date ? 'Safety buffer breached' : 'Safe across entire horizon'}
              </div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Days Below Buffer</div>
              <div
                className="ebb-metric-value"
                style={{ color: data.days_below_buffer > 0 ? 'var(--breach-red)' : 'var(--safe-green)' }}
              >
                {data.days_below_buffer}
              </div>
              <div className="ebb-metric-sub">Safety buffer target {data.safety_buffer_formatted}</div>
            </div>
          </div>

          <div className="ebb-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-ink)' }}>
                Projected Balance Runway
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-slate)', display: 'flex', gap: 16 }}>
                <span>Balance line: <strong style={{ color: '#0F6B73' }}>Deep Teal</strong></span>
                <span>Buffer line: <strong style={{ color: '#D9922E' }}>Amber Dashed</strong></span>
                <span>Breach: <strong style={{ color: '#D2453D' }}>Coral Red</strong></span>
              </div>
            </div>

            <div style={{ width: '100%', height: 380 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.ledger} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4DDCF" vertical={false} />
                  <XAxis
                    dataKey="day_formatted"
                    tick={{ fill: '#5B6B73', fontSize: 12 }}
                    tickMargin={10}
                    interval={Math.floor(data.ledger.length / 8)}
                  />
                  <YAxis
                    tick={{ fill: '#5B6B73', fontSize: 12 }}
                    tickFormatter={(val) => `INR ${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(val: any) => [`INR ${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, 'Balance']}
                    labelFormatter={(label) => `Date: ${label}`}
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E4DDCF', borderRadius: 6, fontSize: 13 }}
                  />
                  <ReferenceLine
                    y={data.safety_buffer}
                    stroke="#D9922E"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    label={{
                      value: `Safety buffer ${data.safety_buffer_formatted}`,
                      fill: '#D9922E',
                      position: 'top',
                      fontSize: 12
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance"
                    stroke="#0F6B73"
                    strokeWidth={2.5}
                    dot={(props: any) => {
                      if (props.payload.is_breach && props.index % 5 === 0) {
                        return (
                          <circle
                            key={props.index}
                            cx={props.cx}
                            cy={props.cy}
                            r={3}
                            fill="#D2453D"
                            stroke="#D2453D"
                          />
                        );
                      }
                      return <React.Fragment key={props.index} />;
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="ebb-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-ink)' }}>
                Daily Ledger
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="ebb-btn-secondary" onClick={handleExportCsv}>
                  Download CSV
                </button>
                <button className="ebb-btn-secondary" onClick={handleExportText}>
                  Download Text
                </button>
              </div>
            </div>

            <div style={{ maxHeight: 380, overflowY: 'auto' }}>
              <table className="ebb-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th style={{ textAlign: 'right' }}>Net Flow</th>
                    <th style={{ textAlign: 'right' }}>Projected Balance</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.ledger.map((row) => (
                    <tr key={row.day}>
                      <td>{row.day_formatted}</td>
                      <td
                        style={{
                          textAlign: 'right',
                          fontWeight: 600,
                          color: row.net < 0 ? 'var(--breach-red)' : row.net > 0 ? 'var(--safe-green)' : 'inherit'
                        }}
                      >
                        {row.net_formatted}
                      </td>
                      <td
                        style={{
                          textAlign: 'right',
                          fontWeight: 600,
                          color: row.is_breach ? 'var(--breach-red)' : 'var(--text-ink)'
                        }}
                      >
                        {row.balance_formatted}
                      </td>
                      <td>
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            color: row.is_breach ? 'var(--breach-red)' : 'var(--safe-green)'
                          }}
                        >
                          {row.is_breach ? 'Below buffer' : 'Healthy'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
