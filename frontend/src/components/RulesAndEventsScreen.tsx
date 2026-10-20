import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Account, Category, RecurringRule, OneOffEvent } from '../types';

interface Props {
  accounts: Account[];
  selectedAccountId: number;
  onSelectAccount: (id: number) => void;
}

export const RulesAndEventsScreen: React.FC<Props> = ({
  accounts,
  selectedAccountId,
  onSelectAccount
}) => {
  const [activeTab, setActiveTab] = useState<'rules' | 'events' | 'addRule' | 'addEvent' | 'import'>('rules');
  const [rules, setRules] = useState<RecurringRule[]>([]);
  const [events, setEvents] = useState<OneOffEvent[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [ruleLabel, setRuleLabel] = useState('');
  const [ruleCat, setRuleCat] = useState<number>(1);
  const [ruleAmt, setRuleAmt] = useState<number>(-1500);
  const [ruleUnit, setRuleUnit] = useState<'MONTH' | 'WEEK'>('MONTH');
  const [ruleEvery, setRuleEvery] = useState<number>(1);
  const [ruleStart, setRuleStart] = useState<string>(new Date().toISOString().split('T')[0]);
  const [hasEnd, setHasEnd] = useState(false);
  const [ruleEnd, setRuleEnd] = useState<string>('');

  const [eventLabel, setEventLabel] = useState('');
  const [eventCat, setEventCat] = useState<number>(1);
  const [eventAmt, setEventAmt] = useState<number>(-5000);
  const [eventDate, setEventDate] = useState<string>(new Date().toISOString().split('T')[0]);

  const [csvFile, setCsvFile] = useState<File | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rData, eData, cData] = await Promise.all([
        api.getRules(selectedAccountId),
        api.getEvents(selectedAccountId),
        api.getCategories()
      ]);
      setRules(rData);
      setEvents(eData);
      setCategories(cData);
      if (cData.length > 0) {
        setRuleCat(cData[0].category_id);
        setEventCat(cData[0].category_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load rules and events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedAccountId]);

  const handleToggleRule = async (ruleId: number) => {
    try {
      await api.toggleRule(ruleId);
      loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle rule');
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await api.createRule({
        account_id: selectedAccountId,
        category_id: ruleCat,
        label: ruleLabel,
        amount: ruleAmt,
        unit: ruleUnit,
        every_n: ruleEvery,
        start_date: ruleStart,
        end_date: hasEnd && ruleEnd ? ruleEnd : null
      });
      setMessage('Recurring rule created successfully.');
      setRuleLabel('');
      setActiveTab('rules');
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await api.createEvent({
        account_id: selectedAccountId,
        category_id: eventCat,
        label: eventLabel,
        amount: eventAmt,
        event_date: eventDate
      });
      setMessage('One off event created successfully.');
      setEventLabel('');
      setActiveTab('events');
      loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleImportCsv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setError(null);
    setMessage(null);
    try {
      const res = await api.importCsv(csvFile, selectedAccountId);
      setMessage(`Import succeeded: ${res.inserted} rows inserted, ${res.duplicates} duplicates skipped.`);
      setCsvFile(null);
      loadData();
    } catch (err: any) {
      setError(`Import failed: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="ebb-page-header">
        <h1 className="ebb-page-title">Rules and Events</h1>
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-slate)' }}>Active Account:</label>
          <select
            className="ebb-select"
            style={{ width: 340 }}
            value={selectedAccountId}
            onChange={(e) => onSelectAccount(Number(e.target.value))}
          >
            {accounts.map((a) => (
              <option key={a.account_id} value={a.account_id}>
                {a.name} ({a.buffer_min_formatted} buffer)
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="ebb-error-banner">{error}</div>}
      {message && <div className="ebb-success-banner">{message}</div>}

      <div className="ebb-tabs">
        <button
          className={`ebb-tab ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          Recurring Rules ({rules.length})
        </button>
        <button
          className={`ebb-tab ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          One Off Events ({events.length})
        </button>
        <button
          className={`ebb-tab ${activeTab === 'addRule' ? 'active' : ''}`}
          onClick={() => setActiveTab('addRule')}
        >
          Add Recurring Rule
        </button>
        <button
          className={`ebb-tab ${activeTab === 'addEvent' ? 'active' : ''}`}
          onClick={() => setActiveTab('addEvent')}
        >
          Add One Off Event
        </button>
        <button
          className={`ebb-tab ${activeTab === 'import' ? 'active' : ''}`}
          onClick={() => setActiveTab('import')}
        >
          Import CSV
        </button>
      </div>

      {activeTab === 'rules' && (
        <div className="ebb-card">
          <table className="ebb-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Label</th>
                <th>Category</th>
                <th>Nature</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th>Cadence</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.rule_id}>
                  <td>{r.rule_id}</td>
                  <td style={{ fontWeight: 600 }}>{r.label}</td>
                  <td>{r.category_name}</td>
                  <td>{r.is_essential ? 'Essential' : 'Discretionary'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: r.amount < 0 ? 'var(--breach-red)' : 'var(--safe-green)' }}>
                    {r.amount_formatted}
                  </td>
                  <td>{r.cadence_formatted}</td>
                  <td>{r.start_date_formatted}</td>
                  <td>{r.end_date_formatted}</td>
                  <td>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600,
                      backgroundColor: r.is_active ? '#E8F5E9' : '#ECEFF1',
                      color: r.is_active ? 'var(--safe-green)' : 'var(--text-slate)'
                    }}>
                      {r.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="ebb-btn-secondary"
                      style={{ padding: '4px 10px', fontSize: 12 }}
                      onClick={() => handleToggleRule(r.rule_id)}
                    >
                      {r.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
              {rules.length === 0 && !loading && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: 24, color: 'var(--text-slate)' }}>
                    No recurring rules registered for this account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'events' && (
        <div className="ebb-card">
          <table className="ebb-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Label</th>
                <th>Category</th>
                <th>Nature</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.event_id}>
                  <td>{ev.event_id}</td>
                  <td>{ev.event_date_formatted}</td>
                  <td style={{ fontWeight: 600 }}>{ev.label}</td>
                  <td>{ev.category_name}</td>
                  <td>{ev.is_essential ? 'Essential' : 'Discretionary'}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600, color: ev.amount < 0 ? 'var(--breach-red)' : 'var(--safe-green)' }}>
                    {ev.amount_formatted}
                  </td>
                </tr>
              ))}
              {events.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--text-slate)' }}>
                    No one off events registered for this account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'addRule' && (
        <div className="ebb-card" style={{ maxWidth: 600 }}>
          <form onSubmit={handleCreateRule}>
            <div className="ebb-form-group">
              <label className="ebb-form-label">Rule Label</label>
              <input
                type="text"
                className="ebb-input"
                placeholder="e.g. Monthly Broadband Internet"
                value={ruleLabel}
                onChange={(e) => setRuleLabel(e.target.value)}
                required
              />
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Category</label>
              <select
                className="ebb-select"
                value={ruleCat}
                onChange={(e) => setRuleCat(Number(e.target.value))}
              >
                {categories.map((c) => (
                  <option key={c.category_id} value={c.category_id}>
                    {c.name} ({c.is_essential ? 'Essential' : 'Discretionary'})
                  </option>
                ))}
              </select>
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Amount (Negative for expense, positive for income)</label>
              <input
                type="number"
                step="0.01"
                className="ebb-input"
                value={ruleAmt}
                onChange={(e) => setRuleAmt(parseFloat(e.target.value))}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className="ebb-form-group">
                <label className="ebb-form-label">Frequency Unit</label>
                <select
                  className="ebb-select"
                  value={ruleUnit}
                  onChange={(e) => setRuleUnit(e.target.value as 'MONTH' | 'WEEK')}
                >
                  <option value="MONTH">Month</option>
                  <option value="WEEK">Week</option>
                </select>
              </div>

              <div className="ebb-form-group">
                <label className="ebb-form-label">Every N Units</label>
                <input
                  type="number"
                  min="1"
                  max="52"
                  className="ebb-input"
                  value={ruleEvery}
                  onChange={(e) => setRuleEvery(parseInt(e.target.value))}
                  required
                />
              </div>
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Start Date</label>
              <input
                type="date"
                className="ebb-input"
                value={ruleStart}
                onChange={(e) => setRuleStart(e.target.value)}
                required
              />
            </div>

            <div className="ebb-form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
                <input
                  type="checkbox"
                  checked={hasEnd}
                  onChange={(e) => setHasEnd(e.target.checked)}
                />
                Has End Date
              </label>
              {hasEnd && (
                <input
                  type="date"
                  className="ebb-input"
                  style={{ marginTop: 8 }}
                  value={ruleEnd}
                  onChange={(e) => setRuleEnd(e.target.value)}
                />
              )}
            </div>

            <button type="submit" className="ebb-btn-primary" style={{ marginTop: 8 }}>
              Save Recurring Rule
            </button>
          </form>
        </div>
      )}

      {activeTab === 'addEvent' && (
        <div className="ebb-card" style={{ maxWidth: 600 }}>
          <form onSubmit={handleCreateEvent}>
            <div className="ebb-form-group">
              <label className="ebb-form-label">Event Label</label>
              <input
                type="text"
                className="ebb-input"
                placeholder="e.g. Annual Vehicle Service"
                value={eventLabel}
                onChange={(e) => setEventLabel(e.target.value)}
                required
              />
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Category</label>
              <select
                className="ebb-select"
                value={eventCat}
                onChange={(e) => setEventCat(Number(e.target.value))}
              >
                {categories.map((c) => (
                  <option key={c.category_id} value={c.category_id}>
                    {c.name} ({c.is_essential ? 'Essential' : 'Discretionary'})
                  </option>
                ))}
              </select>
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Amount (Negative for expense, positive for income)</label>
              <input
                type="number"
                step="0.01"
                className="ebb-input"
                value={eventAmt}
                onChange={(e) => setEventAmt(parseFloat(e.target.value))}
                required
              />
            </div>

            <div className="ebb-form-group">
              <label className="ebb-form-label">Event Date</label>
              <input
                type="date"
                className="ebb-input"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="ebb-btn-primary" style={{ marginTop: 8 }}>
              Save One Off Event
            </button>
          </form>
        </div>
      )}

      {activeTab === 'import' && (
        <div className="ebb-card" style={{ maxWidth: 600 }}>
          <p style={{ fontSize: 14, color: 'var(--text-slate)', lineHeight: 1.5, marginBottom: 16 }}>
            Upload a CSV file containing posted actual transactions. Columns supported: txn_date, amount, label.
            Duplicate rows are rejected atomically using SHA-256 fingerprint protection.
          </p>
          <form onSubmit={handleImportCsv}>
            <div className="ebb-form-group">
              <input
                type="file"
                accept=".csv"
                className="ebb-input"
                onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
                required
              />
            </div>
            <button type="submit" className="ebb-btn-primary" disabled={!csvFile}>
              Execute Atomic Import
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
