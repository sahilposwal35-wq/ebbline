import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  Legend
} from 'recharts';
import { api } from '../api';
import { Account, Scenario, ComparisonData, RecurringRule } from '../types';

interface Props {
  accounts: Account[];
  scenarios: Scenario[];
  selectedAccountId: number;
  onSelectAccount: (id: number) => void;
  onRefreshScenarios: () => void;
}

export const ScenarioCompareScreen: React.FC<Props> = ({
  accounts,
  scenarios,
  selectedAccountId,
  onSelectAccount,
  onRefreshScenarios
}) => {
  const [scenarioA, setScenarioA] = useState<number>(1);
  const [scenarioB, setScenarioB] = useState<number>(scenarios.length > 1 ? scenarios[1].scenario_id : 1);
  const [compData, setCompData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Form states for creating a new scenario
  const [newScenName, setNewScenName] = useState('');
  const [newScenDesc, setNewScenDesc] = useState('');
  const [rules, setRules] = useState<RecurringRule[]>([]);
  const [targetRuleId, setTargetRuleId] = useState<number | null>(null);
  const [action, setAction] = useState<string>('SKIP');
  const [actionVal, setActionVal] = useState<number>(0);
  const [fromDate, setFromDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [toDate, setToDate] = useState<string>(
    new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0]
  );

  const loadRules = async () => {
    try {
      const r = await api.getRules(selectedAccountId);
      setRules(r.filter((x) => x.is_active));
      if (r.length > 0) {
        setTargetRuleId(r[0].rule_id);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadComparison = async () => {
    if (scenarioA === scenarioB && scenarios.length > 1) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.compareScenarios(selectedAccountId, scenarioA, scenarioB);
      setCompData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compare scenarios');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, [selectedAccountId]);

  useEffect(() => {
    if (scenarios.length > 1 && scenarioB === 1) {
      setScenarioB(scenarios[1].scenario_id);
    }
  }, [scenarios]);

  useEffect(() => {
    loadComparison();
  }, [selectedAccountId, scenarioA, scenarioB]);

  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetRuleId) return;
    setError(null);
    setMessage(null);
    try {
      await api.createScenario({
        name: newScenName,
        description: newScenDesc,
        target_type: 'RULE',
        target_id: targetRuleId,
        action,
        value: action !== 'SKIP' ? actionVal : null,
        from_date: fromDate,
        to_date: toDate
      });
      setMessage(`Scenario '${newScenName}' created successfully.`);
      setNewScenName('');
      setNewScenDesc('');
      onRefreshScenarios();
    } catch (err: any) {
      setError(err.message || 'Failed to create scenario');
    }
  };

  return (
    <div>
      <div className="ebb-page-header">
        <h1 className="ebb-page-title">Scenario Comparison</h1>
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
            <label className="ebb-form-label">Scenario A (Baseline)</label>
            <select
              className="ebb-select"
              style={{ width: 240 }}
              value={scenarioA}
              onChange={(e) => setScenarioA(Number(e.target.value))}
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="ebb-form-label">Scenario B (What-If)</label>
            <select
              className="ebb-select"
              style={{ width: 260 }}
              value={scenarioB}
              onChange={(e) => setScenarioB(Number(e.target.value))}
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && <div className="ebb-error-banner">{error}</div>}
      {message && <div className="ebb-success-banner">{message}</div>}

      {compData && (
        <>
          <div className="ebb-card-grid-3">
            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Lowest Balance Delta</div>
              <div
                className="ebb-metric-value"
                style={{ color: compData.min_balance_delta >= 0 ? 'var(--safe-green)' : 'var(--breach-red)' }}
              >
                {compData.min_balance_delta_formatted}
              </div>
              <div className="ebb-metric-sub">
                A: {compData.min_balance_a_formatted} | B: {compData.min_balance_b_formatted}
              </div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Breach Date Shift</div>
              <div className="ebb-metric-value">
                {compData.breach_shift_days !== null
                  ? compData.breach_shift_days > 0
                    ? `${compData.breach_shift_days} days later`
                    : compData.breach_shift_days < 0
                    ? `${Math.abs(compData.breach_shift_days)} days earlier`
                    : 'No shift'
                  : 'N/A'}
              </div>
              <div className="ebb-metric-sub">
                A: {compData.first_breach_a_formatted} | B: {compData.first_breach_b_formatted}
              </div>
            </div>

            <div className="ebb-metric-card">
              <div className="ebb-metric-label">Days Below Buffer Delta</div>
              <div
                className="ebb-metric-value"
                style={{ color: compData.days_below_delta <= 0 ? 'var(--safe-green)' : 'var(--breach-red)' }}
              >
                {compData.days_below_delta} days
              </div>
              <div className="ebb-metric-sub">
                A: {compData.days_below_a} days | B: {compData.days_below_b} days
              </div>
            </div>
          </div>

          <div className="ebb-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-ink)' }}>
                Trajectory Comparison
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-slate)', display: 'flex', gap: 16 }}>
                <span>Scenario A: <strong style={{ color: '#0F6B73' }}>Deep Teal</strong></span>
                <span>Scenario B: <strong style={{ color: '#4F6FA8' }}>Dusk Blue</strong></span>
                <span>Buffer: <strong style={{ color: '#D9922E' }}>Amber Dashed</strong></span>
              </div>
            </div>

            <div style={{ width: '100%', height: 380 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={compData.series} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4DDCF" vertical={false} />
                  <XAxis
                    dataKey="day_formatted"
                    tick={{ fill: '#5B6B73', fontSize: 12 }}
                    tickMargin={10}
                    interval={Math.floor(compData.series.length / 8)}
                  />
                  <YAxis
                    tick={{ fill: '#5B6B73', fontSize: 12 }}
                    tickFormatter={(val) => `INR ${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(val: any, name: any) => [
                      `INR ${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
                      name === 'balance_a' ? compData.scenario_a_name : compData.scenario_b_name
                    ]}
                    labelFormatter={(label) => `Date: ${label}`}
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E4DDCF', borderRadius: 6, fontSize: 13 }}
                  />
                  <ReferenceLine
                    y={compData.series[0]?.safety_buffer}
                    stroke="#D9922E"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance_a"
                    name={compData.scenario_a_name}
                    stroke="#0F6B73"
                    strokeWidth={2.5}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance_b"
                    name={compData.scenario_b_name}
                    stroke="#4F6FA8"
                    strokeWidth={2.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      <div className="ebb-card" style={{ maxWidth: 640, marginTop: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 16px 0', color: 'var(--text-ink)' }}>
          Create New What If Scenario
        </h2>
        <form onSubmit={handleCreateScenario}>
          <div className="ebb-form-group">
            <label className="ebb-form-label">Scenario Name</label>
            <input
              type="text"
              className="ebb-input"
              placeholder="e.g. Cut Discretionary Outflows 50 Percent"
              value={newScenName}
              onChange={(e) => setNewScenName(e.target.value)}
              required
            />
          </div>

          <div className="ebb-form-group">
            <label className="ebb-form-label">Description (Optional)</label>
            <input
              type="text"
              className="ebb-input"
              placeholder="e.g. Pause streaming services and dining out"
              value={newScenDesc}
              onChange={(e) => setNewScenDesc(e.target.value)}
            />
          </div>

          <div className="ebb-form-group">
            <label className="ebb-form-label">Target Recurring Rule</label>
            <select
              className="ebb-select"
              value={targetRuleId || ''}
              onChange={(e) => setTargetRuleId(Number(e.target.value))}
              required
            >
              {rules.map((r) => (
                <option key={r.rule_id} value={r.rule_id}>
                  Rule {r.rule_id}: {r.label} ({r.amount_formatted})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="ebb-form-group">
              <label className="ebb-form-label">Override Action</label>
              <select
                className="ebb-select"
                value={action}
                onChange={(e) => setAction(e.target.value)}
              >
                <option value="SKIP">SKIP (Omit completely)</option>
                <option value="SHIFT_DAYS">SHIFT_DAYS (Move date)</option>
                <option value="SCALE">SCALE (Multiply amount)</option>
              </select>
            </div>

            {action !== 'SKIP' && (
              <div className="ebb-form-group">
                <label className="ebb-form-label">
                  {action === 'SHIFT_DAYS' ? 'Shift Days (e.g. 5)' : 'Scale Multiplier (e.g. 0.50)'}
                </label>
                <input
                  type="number"
                  step={action === 'SCALE' ? '0.01' : '1'}
                  className="ebb-input"
                  value={actionVal}
                  onChange={(e) => setActionVal(parseFloat(e.target.value))}
                  required
                />
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="ebb-form-group">
              <label className="ebb-form-label">From Date</label>
              <input
                type="date"
                className="ebb-input"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                required
              />
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">To Date</label>
              <input
                type="date"
                className="ebb-input"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="ebb-btn-primary" style={{ marginTop: 8 }}>
            Save Scenario and Override
          </button>
        </form>
      </div>
    </div>
  );
};
