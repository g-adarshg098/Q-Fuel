import React, { useState } from 'react';
import {
  Ship,
  LayoutDashboard,
  Users,
  Navigation,
  Atom,
  BarChart3,
  Settings,
  Fuel,
  Leaf,
  Award,
  CheckCircle2,
  Calendar,
  User,
  MapPin,
  Clock,
  Gauge,
  ChevronRight,
  TrendingDown,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Sliders,
  Layers,
  Save,
  RotateCcw,
} from 'lucide-react';

import QuantumOptimizer from './QuantumOptimizer';
import ComplianceScorecard from './ComplianceScorecard';
import WeatherRouting from './WeatherRouting';
import FleetMap from './FleetMap';

export default function QFuelDashboard({ fleet = [], voyages = [] }) {
  const [activeNav, setActiveNav] = useState('dashboard');
  const [selectedRoute, setSelectedRoute] = useState('Route A');
  const [dateRange, setDateRange] = useState('Apr 12, 2026 - Apr 20, 2026');

  // Config Settings state
  const [settings, setSettings] = useState({
    vlsfoPrice: 52080,
    hfoPrice: 42840,
    mgoPrice: 69720,
    lngPrice: 57960,
    etsPrice: 7560,
    numReads: 100,
    numSweeps: 1200,
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Simulated 7-day trend data for Fleet Fuel & CO2
  const trendDays = [
    { day: 'Day 1', fuel: 350, co2: 240 },
    { day: 'Day 2', fuel: 310, co2: 200 },
    { day: 'Day 3', fuel: 245, co2: 155 },
    { day: 'Day 4', fuel: 240, co2: 138 },
    { day: 'Day 5', fuel: 202, co2: 122 },
    { day: 'Day 6', fuel: 165, co2: 104 },
    { day: 'Day 7', fuel: 140, co2: 95 },
  ];

  // Route comparison table data
  const routesData = [
    { name: 'Route A', distance: 2850, fuel: 620, co2: 1980, eta: 5, isRecommended: true },
    { name: 'Route B', distance: 3120, fuel: 690, co2: 2220, eta: 6, isRecommended: false },
    { name: 'Route C', distance: 2760, fuel: 610, co2: 1850, eta: 5, isRecommended: false },
  ];

  const handleSaveSettings = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="qfuel-app-wrapper">
      {/* LEFT SIDEBAR NAVIGATION */}
      <aside className="qfuel-sidebar">
        {/* Brand Logo */}
        <div className="qfuel-brand">
          <div className="qfuel-logo-icon">
            <Ship size={22} color="#111625" strokeWidth={2.5} />
          </div>
          <div className="qfuel-brand-text">
            <h2>Q-FUEL</h2>
            <span>QUANTUM FLEET</span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="qfuel-menu">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { id: 'fleet', label: 'Fleet', icon: Ship },
            { id: 'routes', label: 'Routes', icon: Navigation },
            { id: 'optimization', label: 'Optimization', icon: Atom },
            { id: 'reports', label: 'Reports', icon: BarChart3 },
            { id: 'settings', label: 'Settings', icon: Settings },
          ].map(item => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`qfuel-menu-item ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Footer Quantum Badge */}
        <div className="qfuel-sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#d4af37', fontSize: '0.75rem', fontWeight: 700 }}>
            <Sparkles size={14} /> D-Wave QUBO Engine
          </div>
          <p style={{ fontSize: '0.68rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.2rem' }}>
            Hybrid Quantum Physics Solvers
          </p>
        </div>
      </aside>

      {/* MAIN DASHBOARD CONTENT CANVAS */}
      <main className="qfuel-main-content">
        {/* TOP HEADER BAR */}
        <header className="qfuel-topbar">
          <div className="qfuel-page-title">
            <h1>
              {activeNav === 'dashboard' && 'Fleet Overview'}
              {activeNav === 'fleet' && 'Fleet Telemetry & Asset Management'}
              {activeNav === 'routes' && 'Route Optimization & Weather Speed Profile'}
              {activeNav === 'optimization' && 'Quantum-Inspired QUBO Optimization Console'}
              {activeNav === 'reports' && 'IMO CII & EU ETS Statutory Audit Reports'}
              {activeNav === 'settings' && 'System Parameters & Fuel Price Benchmarks'}
            </h1>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Real-time quantum fuel prediction & green fleet route optimization
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Date Range Selector */}
            <div className="qfuel-date-badge">
              <Calendar size={14} color="#b8860b" />
              <span>{dateRange}</span>
            </div>

            {/* User Profile Avatar */}
            <div className="qfuel-user-avatar">
              <User size={18} color="#d4af37" />
            </div>
          </div>
        </header>

        {/* VIEW 1: DASHBOARD (MOCKUP GOLD & WHITE) */}
        {activeNav === 'dashboard' && (
          <>
            {/* TOP ROW: 4 SUMMARY KPI CARDS */}
            <div className="qfuel-kpi-grid">
              <div className="qfuel-kpi-card">
                <div className="qfuel-kpi-icon icon-blue">
                  <Ship size={22} color="#0284c7" />
                </div>
                <div>
                  <div className="qfuel-kpi-label">Total Vessels</div>
                  <div className="qfuel-kpi-value">{fleet.length || 5}</div>
                </div>
              </div>

              <div className="qfuel-kpi-card">
                <div className="qfuel-kpi-icon icon-amber">
                  <Fuel size={22} color="#d97706" />
                </div>
                <div>
                  <div className="qfuel-kpi-label">Total Fuel (est.)</div>
                  <div className="qfuel-kpi-value">248.5 <span className="unit">t</span></div>
                </div>
              </div>

              <div className="qfuel-kpi-card">
                <div className="qfuel-kpi-icon icon-green">
                  <Leaf size={22} color="#059669" />
                </div>
                <div>
                  <div className="qfuel-kpi-label">Total CO2 (est.)</div>
                  <div className="qfuel-kpi-value">792.3 <span className="unit">t</span></div>
                </div>
              </div>

              <div className="qfuel-kpi-card">
                <div className="qfuel-kpi-icon icon-gold">
                  <Award size={22} color="#b8860b" />
                </div>
                <div>
                  <div className="qfuel-kpi-label">Avg. CII</div>
                  <div className="qfuel-kpi-value cii-rating">B</div>
                </div>
              </div>
            </div>

            {/* MIDDLE SECTION: ROUTE MAP + FUEL TREND CHART + OPTIMIZATION RESULTS */}
            <div className="qfuel-middle-grid">
              <div className="qfuel-card">
                <div className="qfuel-card-header">
                  <h3>Recommended Route</h3>
                  <div className="qfuel-legend">
                    <span className="legend-recommended">● Recommended</span>
                    <span className="legend-alt">--- Alternative</span>
                  </div>
                </div>

                <div className="qfuel-map-canvas">
                  <svg viewBox="0 0 500 240" className="qfuel-svg-map">
                    <path
                      d="M 20 60 Q 60 40 100 70 T 180 50 T 260 80 T 340 60 T 420 90 T 480 70 L 480 220 L 20 220 Z"
                      fill="#f1f5f9"
                      opacity="0.7"
                    />
                    <path
                      d="M 50 140 Q 120 120 190 150 T 320 130 T 450 160"
                      fill="none"
                      stroke="#cbd5e1"
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                    />
                    <path
                      d="M 80 130 Q 200 80 380 150"
                      fill="none"
                      stroke="#94a3b8"
                      strokeWidth="2.5"
                      strokeDasharray="6 4"
                    />
                    <path
                      d="M 80 130 Q 220 170 380 150"
                      fill="none"
                      stroke="#059669"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                    />

                    <g transform="translate(80, 130)">
                      <circle r="12" fill="rgba(5, 150, 105, 0.15)" />
                      <circle r="6" fill="#059669" />
                      <text x="-15" y="-14" fill="#0f172a" fontSize="11" fontWeight="700">Port A</text>
                    </g>

                    <g transform="translate(380, 150)">
                      <circle r="12" fill="rgba(5, 150, 105, 0.15)" />
                      <circle r="6" fill="#059669" />
                      <text x="-15" y="22" fill="#0f172a" fontSize="11" fontWeight="700">Port B</text>
                    </g>

                    <g transform="translate(230, 165)">
                      <rect x="-14" y="-10" width="28" height="20" rx="4" fill="#0f172a" />
                      <path d="M -8 0 L 8 0 L 0 -6 Z" fill="#d4af37" />
                    </g>
                  </svg>
                </div>
              </div>

              <div className="qfuel-card">
                <div className="qfuel-card-header">
                  <h3>Fleet Fuel & CO2 Trend</h3>
                  <div className="qfuel-chart-legend">
                    <span style={{ color: '#0284c7', fontWeight: 700 }}>● Fuel (t)</span>
                    <span style={{ color: '#059669', fontWeight: 700, marginLeft: '0.75rem' }}>● CO2 (t)</span>
                  </div>
                </div>

                <div className="qfuel-chart-box">
                  <svg viewBox="0 0 340 180" style={{ width: '100%', height: '100%' }}>
                    {[0, 40, 80, 120, 160].map((yVal, idx) => (
                      <line key={idx} x1="30" y1={170 - yVal} x2="330" y2={170 - yVal} stroke="#e2e8f0" strokeDasharray="2 2" />
                    ))}
                    <polyline
                      fill="none"
                      stroke="#0284c7"
                      strokeWidth="3"
                      points="40,25 85,45 130,85 175,90 220,110 265,130 310,145"
                    />
                    <polyline
                      fill="none"
                      stroke="#059669"
                      strokeWidth="3"
                      points="40,75 85,100 130,125 175,135 220,145 265,152 310,158"
                    />
                    {[[40, 25], [85, 45], [130, 85], [175, 90], [220, 110], [265, 130], [310, 145]].map(([x, y], i) => (
                      <circle key={i} cx={x} cy={y} r="4" fill="#0284c7" stroke="#ffffff" strokeWidth="2" />
                    ))}
                    {[[40, 75], [85, 100], [130, 125], [175, 135], [220, 145], [265, 152], [310, 158]].map(([x, y], i) => (
                      <circle key={i} cx={x} cy={y} r="4" fill="#059669" stroke="#ffffff" strokeWidth="2" />
                    ))}
                    {['Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7'].map((lbl, idx) => (
                      <text key={idx} x={40 + idx * 45} y="175" fontSize="9" fill="#64748b" textAnchor="middle">{lbl}</text>
                    ))}
                  </svg>
                </div>
              </div>

              <div className="qfuel-card highlight-gold-card">
                <div className="qfuel-opt-header">
                  <div className="qfuel-opt-badge">
                    <CheckCircle2 size={15} color="#059669" />
                    <span>Optimization Results</span>
                  </div>
                </div>

                <h4 className="qfuel-opt-title">Recommended Plan</h4>

                <div className="qfuel-plan-details">
                  <div className="qfuel-plan-item">
                    <Ship size={18} color="#b8860b" />
                    <div>
                      <div className="plan-label">Vessels</div>
                      <div className="plan-val">MV Orion (Main) + 2 more</div>
                    </div>
                  </div>

                  <div className="qfuel-plan-item">
                    <MapPin size={18} color="#b8860b" />
                    <div>
                      <div className="plan-label">Route</div>
                      <div className="plan-val">Route A (shorter, lower CO2)</div>
                    </div>
                  </div>

                  <div className="qfuel-plan-item">
                    <Gauge size={18} color="#b8860b" />
                    <div>
                      <div className="plan-label">Speed</div>
                      <div className="plan-val">14.5 knots (avg)</div>
                    </div>
                  </div>

                  <div className="qfuel-plan-item">
                    <Fuel size={18} color="#b8860b" />
                    <div>
                      <div className="plan-label">Fuel Type</div>
                      <div className="plan-val">LNG + MGO (hybrid)</div>
                    </div>
                  </div>
                </div>

                <div className="qfuel-opt-metrics">
                  <div className="opt-metric-box">
                    <div className="m-label">Fuel Cost</div>
                    <div className="m-val">₹4,058,880</div>
                  </div>

                  <div className="opt-metric-box">
                    <div className="m-label">CO2 Emissions</div>
                    <div className="m-val">612.8 t</div>
                  </div>

                  <div className="opt-metric-box cii-green-bg">
                    <div className="m-label">CII Impact</div>
                    <div className="m-val-cii">A</div>
                  </div>
                </div>
              </div>
            </div>

            {/* BOTTOM SECTION: VESSEL DETAILS + ROUTE COMPARISON + SCENARIO ANALYSIS */}
            <div className="qfuel-bottom-grid">
              <div className="qfuel-card">
                <h3 className="qfuel-section-title">Vessel Details</h3>
                <div className="qfuel-vessel-flex">
                  <div className="qfuel-vessel-img-box">
                    <img
                      src="/vessel_mv_orion.jpg"
                      alt="MV Orion"
                      className="qfuel-vessel-img"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentNode.style.background = 'linear-gradient(135deg, #1e293b, #0f172a)';
                      }}
                    />
                  </div>

                  <div className="qfuel-vessel-info">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>MV Orion</h4>
                      <span className="qfuel-status-pill">● Available</span>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: '0.75rem' }}>IMO 9876543</div>

                    <div className="qfuel-info-grid">
                      <div>
                        <span className="lbl">Type</span>
                        <span className="val">Container</span>
                      </div>
                      <div>
                        <span className="lbl">Capacity</span>
                        <span className="val">5,200 TEU</span>
                      </div>
                      <div>
                        <span className="lbl">Fuel Type</span>
                        <span className="val">LNG / MGO</span>
                      </div>
                      <div>
                        <span className="lbl">Avg. Consumption</span>
                        <span className="val">28 t/day</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="qfuel-card">
                <h3 className="qfuel-section-title">Route Comparison</h3>
                <div className="qfuel-table-wrapper">
                  <table className="qfuel-table">
                    <thead>
                      <tr>
                        <th>Route</th>
                        <th>Distance (nm)</th>
                        <th>Fuel (t)</th>
                        <th>CO2 (t)</th>
                        <th>ETA (days)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {routesData.map(r => (
                        <tr
                          key={r.name}
                          onClick={() => setSelectedRoute(r.name)}
                          className={r.isRecommended ? 'recommended-row' : ''}
                          style={{ cursor: 'pointer' }}
                        >
                          <td>
                            <span className={`route-badge ${r.isRecommended ? 'rec' : ''}`}>
                              {r.name}
                            </span>
                          </td>
                          <td>{r.distance.toLocaleString()}</td>
                          <td>{r.fuel}</td>
                          <td>{r.co2.toLocaleString()}</td>
                          <td>{r.eta}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="qfuel-card">
                <div className="qfuel-card-header">
                  <h3>Scenario Analysis</h3>
                  <div className="qfuel-chart-legend">
                    <span style={{ color: '#0284c7', fontWeight: 700 }}>● Fuel Cost</span>
                    <span style={{ color: '#059669', fontWeight: 700, marginLeft: '0.6rem' }}>● CO2 Emissions</span>
                  </div>
                </div>

                <div className="qfuel-barchart-box">
                  <svg viewBox="0 0 320 170" style={{ width: '100%', height: '100%' }}>
                    {[0, 500, 1000, 1500].map((val, idx) => (
                      <g key={idx}>
                        <line x1="30" y1={140 - idx * 40} x2="310" y2={140 - idx * 40} stroke="#e2e8f0" strokeDasharray="2 2" />
                        <text x="25" y={144 - idx * 40} fontSize="8" fill="#94a3b8" textAnchor="end">{val}</text>
                      </g>
                    ))}

                    <rect x="55" y="40" width="18" height="100" fill="#0284c7" rx="3" />
                    <rect x="76" y="60" width="18" height="80" fill="#059669" rx="3" />

                    <rect x="140" y="58" width="18" height="82" fill="#0284c7" rx="3" />
                    <rect x="161" y="78" width="18" height="62" fill="#059669" rx="3" />

                    <rect x="225" y="68" width="18" height="72" fill="#0284c7" rx="3" />
                    <rect x="246" y="90" width="18" height="50" fill="#059669" rx="3" />

                    <text x="74" y="156" fontSize="9" fill="#475569" fontWeight="600" textAnchor="middle">Current</text>
                    <text x="159" y="156" fontSize="9" fill="#475569" fontWeight="600" textAnchor="middle">Optimized</text>
                    <text x="244" y="156" fontSize="9" fill="#475569" fontWeight="600" textAnchor="middle">Low Emission</text>
                  </svg>
                </div>
              </div>
            </div>
          </>
        )}

        {/* VIEW 2: FLEET ASSET MANAGEMENT */}
        {activeNav === 'fleet' && (
          <div className="qfuel-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 className="qfuel-section-title">Active Fleet Asset Directory</h3>
              <span className="badge badge-emerald">{fleet.length || 16} Active Vessels Monitored</span>
            </div>

            <div className="qfuel-table-wrapper">
              <table className="qfuel-table">
                <thead>
                  <tr>
                    <th>Vessel ID & Name</th>
                    <th>Class / Type</th>
                    <th>Deadweight (DWT)</th>
                    <th>Engine MCR</th>
                    <th>Primary Fuel</th>
                    <th>Daily Charter Rate (₹)</th>
                    <th>EEXI Status</th>
                    <th>Biofouling Coeff</th>
                  </tr>
                </thead>
                <tbody>
                  {fleet.map((v) => (
                    <tr key={v.id}>
                      <td>
                        <strong style={{ color: '#0f172a' }}>{v.name}</strong>
                        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{v.id}</div>
                      </td>
                      <td>{v.type} ({v.subtype})</td>
                      <td>{v.dwt?.toLocaleString()} MT</td>
                      <td>{v.engine_mcr_kw?.toLocaleString()} kW</td>
                      <td>
                        <span className="route-badge rec">{v.fuel_type}</span>
                      </td>
                      <td>
                        <strong style={{ color: '#b8860b' }}>
                          ₹{(v.daily_charter_rate_inr ?? (v.daily_charter_rate_usd * 84))?.toLocaleString()}/day
                        </strong>
                      </td>
                      <td>
                        {v.eexi_compliant ? (
                          <span style={{ color: '#059669', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                            <ShieldCheck size={14} /> Passed
                          </span>
                        ) : (
                          <span style={{ color: '#d97706', fontWeight: 700 }}>Limiter Req.</span>
                        )}
                      </td>
                      <td>
                        <span style={{ color: v.fouling_coeff > 1.1 ? '#d97706' : '#059669', fontWeight: 700 }}>
                          {v.fouling_coeff}x
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* VIEW 3: ROUTES & WEATHER ROUTING */}
        {activeNav === 'routes' && (
          <WeatherRouting voyages={voyages} />
        )}

        {/* VIEW 4: QUANTUM OPTIMIZATION */}
        {activeNav === 'optimization' && (
          <QuantumOptimizer />
        )}

        {/* VIEW 5: REPORTS & COMPLIANCE */}
        {activeNav === 'reports' && (
          <ComplianceScorecard />
        )}

        {/* VIEW 6: SETTINGS */}
        {activeNav === 'settings' && (
          <div className="qfuel-card" style={{ maxWidth: '800px' }}>
            <h3 className="qfuel-section-title" style={{ marginBottom: '1.25rem' }}>
              System Configuration & Price Benchmarks
            </h3>

            {savedSuccess && (
              <div style={{ padding: '0.75rem 1rem', background: '#dcfce7', border: '1px solid #86efac', borderRadius: '8px', color: '#15803d', fontWeight: 700, marginBottom: '1.25rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={16} /> Configuration updated successfully!
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem' }}>
                  Bunker Fuel Price Benchmarks (INR / MT)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label className="form-label">VLSFO Price (₹/MT)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.vlsfoPrice}
                      onChange={e => setSettings({ ...settings, vlsfoPrice: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="form-label">HFO Price (₹/MT)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.hfoPrice}
                      onChange={e => setSettings({ ...settings, hfoPrice: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="form-label">MGO Price (₹/MT)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.mgoPrice}
                      onChange={e => setSettings({ ...settings, mgoPrice: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="form-label">LNG Price (₹/MT)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.lngPrice}
                      onChange={e => setSettings({ ...settings, lngPrice: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#0f172a', marginBottom: '0.75rem' }}>
                  Statutory & Solver Parameters
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label className="form-label">EU ETS Carbon Price (₹/Ton CO2)</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.etsPrice}
                      onChange={e => setSettings({ ...settings, etsPrice: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="form-label">D-Wave Annealing Sweeps</label>
                    <input
                      type="number"
                      className="form-input"
                      value={settings.numSweeps}
                      onChange={e => setSettings({ ...settings, numSweeps: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <button className="btn-primary-cyan" onClick={handleSaveSettings}>
                  <Save size={16} /> Save Configuration
                </button>
                <button className="btn-secondary" onClick={() => setSettings({ vlsfoPrice: 52080, hfoPrice: 42840, mgoPrice: 69720, lngPrice: 57960, etsPrice: 7560, numReads: 100, numSweeps: 1200 })}>
                  <RotateCcw size={16} /> Reset Defaults
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
