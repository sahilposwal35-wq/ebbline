export interface Account {
  account_id: number;
  name: string;
  account_type: string;
  buffer_min: number;
  buffer_min_formatted: string;
}

export interface Category {
  category_id: number;
  name: string;
  is_essential: boolean;
}

export interface Scenario {
  scenario_id: number;
  name: string;
  description?: string;
}

export interface RecurringRule {
  rule_id: number;
  label: string;
  category_name: string;
  is_essential: boolean;
  amount: number;
  amount_formatted: string;
  unit: string;
  every_n: number;
  cadence_formatted: string;
  start_date: string;
  start_date_formatted: string;
  end_date: string | null;
  end_date_formatted: string;
  is_active: boolean;
}

export interface OneOffEvent {
  event_id: number;
  event_date: string;
  event_date_formatted: string;
  label: string;
  category_name: string;
  is_essential: boolean;
  amount: number;
  amount_formatted: string;
}

export interface ProjectionDay {
  day: string;
  day_formatted: string;
  net: number;
  net_formatted: string;
  balance: number;
  balance_formatted: string;
  is_breach: boolean;
}

export interface ProjectionData {
  run_id: number;
  account_id: number;
  scenario_id: number;
  anchor_date: string;
  anchor_date_formatted: string;
  anchor_balance: number;
  anchor_balance_formatted: string;
  horizon_start: string;
  horizon_start_formatted: string;
  horizon_end: string;
  horizon_end_formatted: string;
  safety_buffer: number;
  safety_buffer_formatted: string;
  min_balance: number;
  min_balance_formatted: string;
  min_balance_date: string | null;
  min_balance_date_formatted: string;
  first_breach_date: string | null;
  first_breach_date_formatted: string;
  days_below_buffer: number;
  ledger: ProjectionDay[];
}

export interface ComparisonSeriesPoint {
  day: string;
  day_formatted: string;
  balance_a: number;
  balance_b: number | null;
  safety_buffer: number;
}

export interface ComparisonData {
  account_id: number;
  account_name: string;
  scenario_a_id: number;
  scenario_a_name: string;
  run_a_id: number;
  min_balance_a: number;
  min_balance_a_formatted: string;
  first_breach_a: string | null;
  first_breach_a_formatted: string;
  days_below_a: number;
  scenario_b_id: number;
  scenario_b_name: string;
  run_b_id: number;
  min_balance_b: number;
  min_balance_b_formatted: string;
  first_breach_b: string | null;
  first_breach_b_formatted: string;
  days_below_b: number;
  min_balance_delta: number;
  min_balance_delta_formatted: string;
  breach_shift_days: number | null;
  days_below_delta: number;
  series: ComparisonSeriesPoint[];
}

export interface ExplainEvent {
  event_id: number;
  due_date: string;
  due_date_formatted: string;
  label: string;
  category_name: string;
  is_essential: boolean;
  amount: number;
  amount_formatted: string;
  running_balance: number;
  running_balance_formatted: string;
}

export interface ExplainCategory {
  category_name: string;
  is_essential: boolean;
  event_count: number;
  total_amount: number;
  total_amount_formatted: string;
}

export interface ExplainData {
  run_id: number;
  query_day: string;
  query_day_formatted: string;
  anchor_date: string;
  anchor_date_formatted: string;
  anchor_balance: number;
  anchor_balance_formatted: string;
  stored_day_balance: number;
  stored_day_balance_formatted: string;
  cumulative_net: number;
  cumulative_net_formatted: string;
  events: ExplainEvent[];
  categories: ExplainCategory[];
}

export interface FixItem {
  source_type: string;
  source_id: number;
  due_date: string;
  due_date_formatted: string;
  label: string;
  category_name: string;
  saving: number;
  saving_formatted: string;
  cum_saving: number;
  cum_saving_formatted: string;
}

export interface SuggestFixesData {
  has_breach: boolean;
  message?: string;
  shortfall_target?: number;
  shortfall_target_formatted?: string;
  scope_note?: string;
  fixes?: FixItem[];
}

export interface ReserveRow {
  label: string;
  total_obligation: number;
  total_obligation_formatted: string;
  cycle_formatted: string;
  monthly_set_aside: number;
  monthly_set_aside_formatted: string;
}

export interface ReserveScheduleData {
  total_monthly_reserve: number;
  total_monthly_reserve_formatted: string;
  rows: ReserveRow[];
}

export interface PlanVsActualRow {
  month: string;
  rule_label: string;
  planned: number;
  planned_formatted: string;
  actual: number;
  actual_formatted: string;
  variance: number;
  variance_formatted: string;
  variance_pct: number;
  avg_3m: number;
  avg_3m_formatted: string;
}

export interface BacktestComparison {
  checkpoint_date: string;
  checkpoint_date_formatted: string;
  actual_balance: number;
  actual_balance_formatted: string;
  projected_balance: number;
  projected_balance_formatted: string;
  abs_error: number;
  abs_error_formatted: string;
  pct_error: number;
}

export interface BacktestData {
  disclaimer?: string;
  error?: string;
  overall_mae?: number;
  overall_mae_formatted?: string;
  overall_rmse?: number;
  overall_rmse_formatted?: string;
  comparisons: BacktestComparison[];
}
