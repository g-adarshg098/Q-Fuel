import React, { useState, useEffect } from 'react';
import { Waves, Wind, Compass, Clock, Zap, CheckCircle2, ArrowRight } from 'lucide-react';

export default function WeatherRouting({ voyages }) {
  const [selectedVoyageId, setSelectedVoyageId] = useState(voyages[0]?.voyage_id || 'VOY-2026-1000');
  const [routingData, setRoutingData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    optimizeRoute();
  }, [selectedVoyageId]);

  const optimizeRoute = async () => {
    if (!selectedVoyageId) return;
    setLoading(true);
    try {
      const res = await fetch('/api/route-optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voyage_id: selectedVoyageId }),
      });
      const data = await res.json();
      setRoutingData(data);
    } catch (err) {
      console.error('Weather route optimization failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const opt = routingData?.optimization;
  const legs = opt?.legs || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div className="glass-card highlight-cyan" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Waves size={22} color="var(--cyan-primary)" />
            Continuous Weather Routing & Speed Optimization
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Simulated Annealing continuous profile solver: slows down through storm wave states (Kwon resistance &prop; Hs&sup2;) and speeds up in calm waters to honor arrival ETA
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            className="form-select"
            value={selectedVoyageId}
            onChange={e => setSelectedVoyageId(e.target.value)}
            style={{ width: 'auto' }}
          >
            {voyages.slice(0, 12).map(v => (
              <option key={v.voyage_id} value={v.voyage_id}>
                {v.voyage_id} ({v.origin_port} &rarr; {v.destination_port})
              </option>
            ))}
          </select>

          <button
            onClick={optimizeRoute}
            disabled={loading}
            className="btn-primary-cyan"
          >
            {loading ? 'Optimizing Profile...' : 'Optimize Waypoints'}
          </button>
        </div>
      </div>

      {/* Hero Savings Callout */}
      {opt && (
        <div className="grid-4">
          <div className="stat-box" style={{ borderLeft: '3px solid var(--emerald-green)' }}>
            <div className="stat-label">Weather Route Fuel Saved</div>
            <div className="stat-val emerald">
              {opt.fuel_saved_mt} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>MT</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--emerald-green)', fontWeight: 700, marginTop: '0.2rem' }}>
              &darr; {opt.fuel_saved_pct}% bunker fuel reduction
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid var(--cyan-primary)' }}>
            <div className="stat-label">Bunker Cost Savings</div>
            <div className="stat-val cyan">
              ₹{(opt.cost_saved_inr ?? opt.cost_saved_usd)?.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              On this single passage
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid var(--purple-quantum)' }}>
            <div className="stat-label">CO2e Abated</div>
            <div className="stat-val purple">
              {opt.co2_saved_mt} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>MT</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Reduced operational footprint
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid #38bdf8' }}>
            <div className="stat-label">Strict ETA Compliance</div>
            <div className="stat-val" style={{ color: opt.eta_honored ? '#10b981' : 'var(--coral-primary)' }}>
              {opt.optimized_voyage_hours} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>hrs</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Max Allowed ETA: {opt.max_allowed_eta_hours} hrs
            </div>
          </div>
        </div>
      )}

      {/* Leg-by-Leg Waypoint Table & Strategy */}
      {legs.length > 0 && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
              Waypoint Telemetry & Dynamic Speed Strategy
            </h3>
            <span className="badge badge-cyan">{legs.length} Waypoint Segments</span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Leg #</th>
                <th>Distance</th>
                <th>Forecasted Waves (Hs)</th>
                <th>Wind Speed</th>
                <th>Flat Cruising Speed</th>
                <th>Optimized Speed</th>
                <th>Speed Delta</th>
                <th>Hydrodynamic Strategy</th>
              </tr>
            </thead>
            <tbody>
              {legs.map(l => {
                const isSlow = l.speed_delta_knots < 0;
                return (
                  <tr key={l.leg_index}>
                    <td>
                      <strong style={{ color: '#fff' }}>Segment {l.leg_index}</strong>
                    </td>
                    <td>{l.distance_nm} NM</td>
                    <td>
                      <span style={{ color: l.wave_height_m > 2.2 ? 'var(--coral-deep)' : '#fff', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Waves size={14} /> {l.wave_height_m} m
                      </span>
                    </td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Wind size={14} color="var(--cyan-deep)" /> {l.wind_speed_knots} kts
                      </span>
                    </td>
                    <td>{l.flat_speed_knots} kts</td>
                    <td>
                      <strong style={{ color: 'var(--cyan-primary)' }}>{l.optimized_speed_knots} kts</strong>
                    </td>
                    <td>
                      <span style={{ color: isSlow ? 'var(--coral-deep)' : 'var(--emerald-green)', fontWeight: 700 }}>
                        {l.speed_delta_knots > 0 ? `+${l.speed_delta_knots}` : l.speed_delta_knots} kts
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${isSlow ? 'badge-coral' : 'badge-emerald'}`}>
                        {l.weather_strategy}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
