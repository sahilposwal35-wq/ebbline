import React, { useState, useEffect } from 'react';
import { api } from './api';
import { Account, Scenario } from './types';
import { RulesAndEventsScreen } from './components/RulesAndEventsScreen';
import { ProjectionScreen } from './components/ProjectionScreen';
import { ScenarioCompareScreen } from './components/ScenarioCompareScreen';
import { ExplainAndFixScreen } from './components/ExplainAndFixScreen';
import { ReserveAndAccuracyScreen } from './components/ReserveAndAccuracyScreen';

type ScreenType = 'rules' | 'projection' | 'compare' | 'explain' | 'reserve';

export const App: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<ScreenType>('projection');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchGlobalData = async () => {
    try {
      const [accs, scens] = await Promise.all([
        api.getAccounts(),
        api.getScenarios()
      ]);
      setAccounts(accs);
      setScenarios(scens);
      if (accs.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accs[0].account_id);
      }
    } catch (err) {
      console.error('Failed to load accounts and scenarios', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'var(--text-slate)' }}>
        Loading Ebbline Engine...
      </div>
    );
  }

  return (
    <div className="ebb-app-layout">
      <aside className="ebb-sidebar">
        <div className="ebb-sidebar-brand">Ebbline</div>
        <div className="ebb-sidebar-tagline">Know the day your balance dips, before it does.</div>

        <nav className="ebb-nav-list">
          <button
            className={`ebb-nav-button ${currentScreen === 'rules' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('rules')}
          >
            Rules and Events
          </button>
          <button
            className={`ebb-nav-button ${currentScreen === 'projection' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('projection')}
          >
            Projection
          </button>
          <button
            className={`ebb-nav-button ${currentScreen === 'compare' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('compare')}
          >
            Scenario Compare
          </button>
          <button
            className={`ebb-nav-button ${currentScreen === 'explain' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('explain')}
          >
            Explain and Fix
          </button>
          <button
            className={`ebb-nav-button ${currentScreen === 'reserve' ? 'active' : ''}`}
            onClick={() => setCurrentScreen('reserve')}
          >
            Reserve and Accuracy
          </button>
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: 32, fontSize: 11, color: 'var(--text-slate)' }}>
          <div>Engine: MySQL 8.4 LTS</div>
          <div style={{ marginTop: 4 }}>FastAPI + React TypeScript</div>
        </div>
      </aside>

      <main className="ebb-main-content">
        {currentScreen === 'rules' && (
          <RulesAndEventsScreen
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
          />
        )}

        {currentScreen === 'projection' && (
          <ProjectionScreen
            accounts={accounts}
            scenarios={scenarios}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
          />
        )}

        {currentScreen === 'compare' && (
          <ScenarioCompareScreen
            accounts={accounts}
            scenarios={scenarios}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
            onRefreshScenarios={fetchGlobalData}
          />
        )}

        {currentScreen === 'explain' && (
          <ExplainAndFixScreen
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
            onRefreshScenarios={fetchGlobalData}
          />
        )}

        {currentScreen === 'reserve' && (
          <ReserveAndAccuracyScreen
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onSelectAccount={setSelectedAccountId}
          />
        )}
      </main>
    </div>
  );
};
export default App;
