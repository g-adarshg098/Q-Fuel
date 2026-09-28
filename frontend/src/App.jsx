import React, { useState, useEffect } from 'react';
import {
  Ship,
  Navigation,
  Cpu,
  Atom,
  Sliders,
  Award,
  Layers,
  Waves,
  Sparkles,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

import FleetMap from './components/FleetMap';
import PredictionConsole from './components/PredictionConsole';
import QuantumOptimizer from './components/QuantumOptimizer';
import SolverBenchmark from './components/SolverBenchmark';
import ScenarioRunner from './components/ScenarioRunner';
import ComplianceScorecard from './components/ComplianceScorecard';
import WeatherRouting from './components/WeatherRouting';
import QFuelDashboard from './components/QFuelDashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSimpleMode, setIsSimpleMode] = useState(true);
  const [fleet, setFleet] = useState([]);
  const [voyages, setVoyages] = useState([]);
  const [ports, setPorts] = useState({});
  const [modelMetrics, setModelMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [fleetRes, voyagesRes, portsRes, metricsRes] = await Promise.all([
        fetch('/api/fleet').then(r => r.json()),
        fetch('/api/voyages?limit=50').then(r => r.json()),
        fetch('/api/ports').then(r => r.json()),
        fetch('/api/model/metrics').then(r => r.json()),
      ]);

      setFleet(fleetRes.fleet || []);
      setVoyages(voyagesRes.voyages || []);
      setPorts(portsRes.ports || {});
      setModelMetrics(metricsRes || null);
    } catch (err) {
      console.error('Failed to load initial maritime telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Q-FUEL Dashboard', icon: Ship, highlight: 'gold' },
    { id: 'optimizer', label: 'Quantum Optimizer', icon: Atom, highlight: 'gold' },
    { id: 'prediction', label: 'Fuel ML Predictor', icon: Cpu, highlight: 'gold' },
    { id: 'compliance', label: 'IMO CII & EU ETS', icon: Award, highlight: 'gold' },
  ];

  return (
    <div className="app-container">
      {/* Top Glass Navigation Bar */}
      <header className="top-nav">
        {/* Brand / Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #d4af37, #b8860b)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(212, 175, 55, 0.35)',
          }}>
            <Ship size={24} color="#ffffff" strokeWidth={2.4} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
                Q-FUEL <span style={{ color: '#b8860b' }}>QUANTUM</span>
              </h1>
              <span className="badge" style={{ fontSize: '0.65rem', background: '#faf5e6', color: '#b8860b', border: '1px solid #f3e8c8' }}>
                v1.0 &bull; D-Wave QUBO
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: '#64748b' }}>
              Green Fleet Optimization & Voyage Fuel Burn Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Live System Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: '#dcfce7',
            border: '1px solid #86efac',
            borderRadius: '9999px',
            padding: '0.35rem 0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontSize: '0.75rem',
            color: '#15803d',
            fontWeight: 700,
          }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#15803d' }} />
            API ONLINE
          </div>
        </div>
      </header>

      {/* Main Body Content */}
      <main className="main-content">
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', flexDirection: 'column', gap: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              border: '3px solid rgba(0, 242, 254, 0.2)',
              borderTopColor: 'var(--cyan-primary)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Initializing Quantum Annealing & ML Engine...
            </p>
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <QFuelDashboard fleet={fleet} voyages={voyages} />
            )}

            {activeTab === 'optimizer' && (
              <QuantumOptimizer />
            )}

            {activeTab === 'prediction' && (
              <PredictionConsole fleet={fleet} modelMetrics={modelMetrics} />
            )}

            {activeTab === 'compliance' && (
              <ComplianceScorecard />
            )}
          </>
        )}
      </main>
    </div>
  );
}
