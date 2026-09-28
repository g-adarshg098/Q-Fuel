import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, ArrowRight, TrendingDown, TrendingUp, AlertTriangle, ShieldCheck, Flame, DollarSign } from 'lucide-react';

export default function ScenarioRunner({ fleet, voyages }) {
  const [selectedVoyageId, setSelectedVoyageId] = useState(voyages[0]?.voyage_id || 'VOY-2026-1000');
  const [targetVesselId, setTargetVesselId] = useState(voyages[0]?.vessel_id || fleet[0]?.id);
  const [speedDelta, setSpeedDelta] = useState(0.0);
  const [alternativeFuel, setAlternativeFuel] = useState('VLSFO');

  const [scenarioResult, setScenarioResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedVoyageId) {
      const v = voyages.find(voy => voy.voyage_id === selectedVoyageId);
      if (v) {
        setTargetVesselId(v.vessel_id);
        setAlternativeFuel(v.fuel_type || 'VLSFO');
        setSpeedDelta(0.0);
      }
    }
  }, [selectedVoyageId]);

  useEffect(() => {
    runSimulation();
  }, [selectedVoyageId, targetVesselId, speedDelta, alternativeFuel]);

  const runSimulation = async () => {
    if (!selectedVoyageId) return;
    setLoading(true);
    try {
      const res = await fetch('/api/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voyage_id: selectedVoyageId,
          vessel_id: targetVesselId,
          speed_knots_delta: Number(speedDelta),
          alternative_fuel: alternativeFuel,
        }),
      });
      const data = await res.json();
      setScenarioResult(data);
    } catch (err) {
      console.error('Scenario simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const delta = scenarioResult?.comparison_delta;
  const base = scenarioResult?.baseline;
  const scen = scenarioResult?.scenario;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div className="glass-card highlight-cyan" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Sliders size={22} color="var(--cyan-primary)" />
            "What-If" Green Fleet Scenario Simulator
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Simulate operational levers: swap assigned vessels, test slow-steaming vs fast transit, and model alternate low-carbon fuels
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading}
          className="btn-secondary"
        >
          <RefreshCw size={15} />
          {loading ? 'Re-calculating...' : 'Refresh Simulation'}
        </button>
      </div>

      {/* Control Panel Grid */}
      <div className="glass-card">
        <div className="grid-4">
          <div className="form-group">
            <label className="form-label">Target Voyage</label>
            <select
              className="form-select"
              value={selectedVoyageId}
              onChange={e => setSelectedVoyageId(e.target.value)}
            >
              {voyages.slice(0, 15).map(v => (
                <option key={v.voyage_id} value={v.voyage_id}>
                  {v.voyage_id} &bull; {v.origin_port} &rarr; {v.destination_port} ({v.distance_nm.toLocaleString()} nm)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Substitute Vessel</label>
            <select
              className="form-select"
              value={targetVesselId}
              onChange={e => setTargetVesselId(e.target.value)}
            >
              {fleet.map(v => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.type}) [{v.fuel_type}]
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">
              Speed Adjustment: <strong style={{ color: speedDelta > 0 ? 'var(--coral-deep)' : speedDelta < 0 ? 'var(--cyan-primary)' : '#fff' }}>
                {speedDelta > 0 ? `+${speedDelta}` : speedDelta} knots
              </strong>
            </label>
            <input
              type="range"
              min="-3.0"
              max="3.0"
              step="0.5"
              value={speedDelta}
              onChange={e => setSpeedDelta(e.target.value)}
              style={{ width: '100%', accentColor: 'var(--cyan-primary)', cursor: 'pointer', marginTop: '0.4rem' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>Slow-steaming (-3kt)</span>
              <span>Baseline</span>
              <span>Sprint (+3kt)</span>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Bunker Fuel Grade</label>
            <select
              className="form-select"
              value={alternativeFuel}
              onChange={e => setAlternativeFuel(e.target.value)}
            >
              <option value="VLSFO">VLSFO (₹52,080/MT, Cf 3.151)</option>
              <option value="HFO">HFO (₹42,840/MT, Cf 3.114)</option>
              <option value="MGO">MGO (₹69,720/MT, Cf 3.206)</option>
              <option value="LNG">LNG (₹57,960/MT, Cf 2.750)</option>
              <option value="Methanol">Bio-Methanol (₹65,520/MT, Cf 1.375)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Before vs After Impact Comparison */}
      {base && scen && delta && (
        <div className="grid-2">
          {/* Baseline Plan Box */}
          <div className="glass-card highlight-coral">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff' }}>Current Baseline Configuration</h3>
              <span className="badge badge-coral">Band {base.cii_rating}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div className="stat-box">
                <div className="stat-label">Assigned Vessel</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>{base.vessel_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Cruising Speed: {base.speed_knots} knots &bull; Fuel: {base.fuel_type}</div>
              </div>

              <div className="grid-2" style={{ gap: '0.75rem' }}>
                <div className="stat-box">
                  <div className="stat-label">Fuel Consumption</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>{base.fuel_consumed_mt} MT</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>₹{(base.fuel_cost_inr ?? base.fuel_cost_usd)?.toLocaleString()}</div>
                </div>

                <div className="stat-box">
                  <div className="stat-label">CO2e Emissions</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--coral-deep)' }}>{base.co2_emissions_mt} MT</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>EU ETS: ₹{(base.eu_ets_cost_inr ?? base.eu_ets_cost_usd)?.toLocaleString()}</div>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Transit Duration: <strong style={{ color: '#fff' }}>{base.duration_hours} hrs</strong> ({(base.duration_hours / 24).toFixed(1)} days)
              </div>
            </div>
          </div>

          {/* Simulated Scenario Plan Box */}
          <div className="glass-card highlight-cyan">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff' }}>Simulated Scenario Impact</h3>
              <span className={`badge ${scen.cii_rating <= 'B' ? 'badge-emerald' : scen.cii_rating === 'C' ? 'badge-amber' : 'badge-coral'}`}>
                Band {scen.cii_rating} ({scen.rating_description})
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div className="stat-box">
                <div className="stat-label">Simulated Vessel</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--cyan-primary)' }}>{scen.vessel_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sim Speed: {scen.speed_knots} knots &bull; Fuel: {scen.fuel_type}</div>
              </div>

              <div className="grid-2" style={{ gap: '0.75rem' }}>
                <div className="stat-box">
                  <div className="stat-label">Fuel Consumption</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--cyan-primary)' }}>{scen.fuel_consumed_mt} MT</div>
                  <div style={{ fontSize: '0.75rem', color: delta.fuel_delta_mt < 0 ? 'var(--emerald-green)' : 'var(--coral-deep)', fontWeight: 600 }}>
                    {delta.fuel_delta_mt > 0 ? `+${delta.fuel_delta_mt}` : delta.fuel_delta_mt} MT ({delta.fuel_delta_pct}%)
                  </div>
                </div>

                <div className="stat-box">
                  <div className="stat-label">CO2e Emissions</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>{scen.co2_emissions_mt} MT</div>
                  <div style={{ fontSize: '0.75rem', color: delta.co2_delta_mt < 0 ? 'var(--emerald-green)' : 'var(--coral-deep)', fontWeight: 600 }}>
                    {delta.co2_delta_mt > 0 ? `+${delta.co2_delta_mt}` : delta.co2_delta_mt} MT ({delta.co2_delta_pct}%)
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>Transit Duration: <strong style={{ color: '#fff' }}>{scen.duration_hours} hrs</strong> ({delta.hours_delta > 0 ? `+${delta.hours_delta}h` : `${delta.hours_delta}h`})</span>
                <span>CII Rating Shift: <strong style={{ color: delta.is_net_positive_reduction ? 'var(--emerald-green)' : 'var(--coral-deep)' }}>{delta.cii_rating_change}</strong></span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
