import {
  Account,
  Category,
  Scenario,
  RecurringRule,
  OneOffEvent,
  ProjectionData,
  ComparisonData,
  ExplainData,
  SuggestFixesData,
  ReserveScheduleData,
  PlanVsActualRow,
  BacktestData
} from './types';

const API_BASE = '/api';

export const api = {
  async getAccounts(): Promise<Account[]> {
    const res = await fetch(`${API_BASE}/accounts`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getCategories(): Promise<Category[]> {
    const res = await fetch(`${API_BASE}/categories`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getScenarios(): Promise<Scenario[]> {
    const res = await fetch(`${API_BASE}/scenarios`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getRules(accountId: number): Promise<RecurringRule[]> {
    const res = await fetch(`${API_BASE}/rules?account_id=${accountId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createRule(payload: {
    account_id: number;
    category_id: number;
    label: string;
    amount: number;
    unit: string;
    every_n: number;
    start_date: string;
    end_date?: string | null;
  }) {
    const res = await fetch(`${API_BASE}/rules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create rule');
    }
    return res.json();
  },

  async toggleRule(ruleId: number) {
    const res = await fetch(`${API_BASE}/rules/${ruleId}/toggle`, {
      method: 'PATCH'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getEvents(accountId: number): Promise<OneOffEvent[]> {
    const res = await fetch(`${API_BASE}/events?account_id=${accountId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createEvent(payload: {
    account_id: number;
    category_id: number;
    label: string;
    amount: number;
    event_date: string;
  }) {
    const res = await fetch(`${API_BASE}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create event');
    }
    return res.json();
  },

  async buildProjection(accountId: number, scenarioId: number, horizonDays: number): Promise<ProjectionData> {
    const res = await fetch(`${API_BASE}/projections/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account_id: accountId,
        scenario_id: scenarioId,
        horizon_days: horizonDays
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Projection build failed');
    }
    return res.json();
  },

  async compareScenarios(accountId: number, scenarioA: number, scenarioB: number): Promise<ComparisonData> {
    const res = await fetch(
      `${API_BASE}/scenarios/compare?account_id=${accountId}&scenario_a=${scenarioA}&scenario_b=${scenarioB}`
    );
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Scenario comparison failed');
    }
    return res.json();
  },

  async createScenario(payload: {
    name: string;
    description?: string;
    target_type: string;
    target_id: number;
    action: string;
    value?: number | null;
    from_date: string;
    to_date: string;
  }) {
    const res = await fetch(`${API_BASE}/scenarios`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create scenario');
    }
    return res.json();
  },

  async explainDay(runId: number, date: string): Promise<ExplainData> {
    const res = await fetch(`${API_BASE}/analytics/explain?run_id=${runId}&date=${date}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Explain day failed');
    }
    return res.json();
  },

  async suggestFixes(runId: number): Promise<SuggestFixesData> {
    const res = await fetch(`${API_BASE}/analytics/suggest-fixes?run_id=${runId}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Suggest fixes failed');
    }
    return res.json();
  },

  async saveFixes(runId: number) {
    const res = await fetch(`${API_BASE}/analytics/save-fixes?run_id=${runId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save fixes');
    }
    return res.json();
  },

  async getReserveSchedule(accountId: number): Promise<ReserveScheduleData> {
    const res = await fetch(`${API_BASE}/analytics/reserve?account_id=${accountId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getPlanVsActual(accountId: number): Promise<PlanVsActualRow[]> {
    const res = await fetch(`${API_BASE}/analytics/plan-vs-actual?account_id=${accountId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getBacktest(accountId: number): Promise<BacktestData> {
    const res = await fetch(`${API_BASE}/analytics/backtest?account_id=${accountId}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Backtest failed');
    }
    return res.json();
  },

  async importCsv(file: File, accountId: number) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/import-csv?account_id=${accountId}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'CSV import failed');
    }
    return res.json();
  }
};
