import React, { useState } from 'react';
import { Anchor, Navigation, Wind, Waves, AlertTriangle, ShieldCheck, Ship, MapPin } from 'lucide-react';

/**
 * Converts latitude and longitude into SVG canvas coordinates (Mercator-like projection)
 * Canvas dimension: width=1000, height=520
 */
function projectCoords(lat, lon) {
  // lon: -180 to 180 -> 0 to 1000
  const x = ((lon + 180) / 360) * 1000;
  // lat: 85 to -85 -> 0 to 520
  const clampedLat = Math.max(-75, Math.min(75, lat));
  const y = (1 - (clampedLat + 75) / 150) * 520;
  return { x: Math.round(x), y: Math.round(y) };
}

export default function FleetMap({ fleet, ports, voyages, onSelectVessel }) {
  const [selectedVessel, setSelectedVessel] = useState(fleet[0] || null);
  const [filterType, setFilterType] = useState('ALL');

  const filteredFleet = filterType === 'ALL'
    ? fleet
    : fleet.filter(v => v.type.toUpperCase() === filterType);

  return (
    <div className="glass-card highlight-cyan" style={{ padding: '1.25rem' }}>
      {/* Map Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Navigation size={22} color="var(--cyan-primary)" />
            Global Maritime Fleet & Telemetry Map
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Real-time tracking of {fleet.length} active vessels, global hub ports, and trade lane waypoints
          </p>
        </div>

        {/* Filter Chips */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {['ALL', 'BULK CARRIER', 'CONTAINER', 'TANKER', 'LNG CARRIER'].map(t => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className="badge"
              style={{
                cursor: 'pointer',
                border: filterType === t ? '1px solid var(--cyan-primary)' : '1px solid var(--border-subtle)',
                background: filterType === t ? 'rgba(0, 242, 254, 0.18)' : 'rgba(15, 23, 42, 0.6)',
                color: filterType === t ? 'var(--cyan-primary)' : 'var(--text-muted)',
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Interactive Ocean Map */}
      <div style={{ position: 'relative', width: '100%', borderRadius: '10px', overflow: 'hidden', background: '#080d19', border: '1px solid rgba(255,255,255,0.06)' }}>
        <svg
          viewBox="0 0 1000 520"
          style={{ width: '100%', height: 'auto', display: 'block', minHeight: '380px' }}
        >
          {/* Subtle Grid Lines */}
          <defs>
            <pattern id="grid" width="100" height="65" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 65" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
            </pattern>
            <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--cyan-primary)" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--coral-primary)" stopOpacity="0.8" />
            </linearGradient>
          </defs>
          <rect width="1000" height="520" fill="url(#grid)" />

          {/* Continents simplified silhouettes (Polygons for world continents) */}
          <g fill="rgba(30, 41, 59, 0.45)" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="0.75">
            {/* North America */}
            <path d="M 150 90 L 260 70 L 300 120 L 280 200 L 220 220 L 200 270 L 170 240 L 130 180 Z" />
            {/* South America */}
            <path d="M 270 290 L 330 310 L 370 380 L 330 470 L 280 430 L 250 340 Z" />
            {/* Europe */}
            <path d="M 470 90 L 580 80 L 560 160 L 510 180 L 460 140 Z" />
            {/* Africa */}
            <path d="M 480 190 L 570 190 L 600 280 L 560 410 L 500 400 L 460 270 Z" />
            {/* Asia */}
            <path d="M 590 70 L 850 80 L 880 180 L 780 250 L 690 240 L 640 180 Z" />
            {/* Australia */}
            <path d="M 780 340 L 880 340 L 870 430 L 790 420 Z" />
          </g>

          {/* Major Shipping Lanes */}
          {voyages.slice(0, 10).map((voy, i) => {
            const p1 = projectCoords(voy.origin_lat, voy.origin_lon);
            const p2 = projectCoords(voy.dest_lat, voy.dest_lon);
            // Midpoint curve for great circle simulation
            const midX = (p1.x + p2.x) / 2;
            const midY = Math.min(p1.y, p2.y) - 30;
            return (
              <path
                key={voy.voyage_id || i}
                d={`M ${p1.x} ${p1.y} Q ${midX} ${midY} ${p2.x} ${p2.y}`}
                fill="none"
                stroke="url(#routeGradient)"
                strokeWidth="1.6"
                strokeDasharray="4 4"
                opacity="0.65"
              />
            );
          })}

          {/* Port Hubs */}
          {Object.entries(ports).map(([name, meta]) => {
            const pt = projectCoords(meta.lat, meta.lon);
            return (
              <g key={name} transform={`translate(${pt.x}, ${pt.y})`}>
                <circle r="3.5" fill="#f8fafc" opacity="0.6" />
                <circle r="7" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="0.75" />
                <text
                  x="8"
                  y="3"
                  fill="#94a3b8"
                  fontSize="7.5"
                  fontWeight="600"
                  fontFamily="sans-serif"
                >
                  {name.split(' ')[0]}
                </text>
              </g>
            );
          })}

          {/* Vessel Markers */}
          {filteredFleet.map(v => {
            const pos = v.current_location || { lat: 20, lon: 40 };
            const pt = projectCoords(pos.lat, pos.lon);
            const isSelected = selectedVessel?.id === v.id;
            const markerColor = v.fuel_type === 'Methanol'
              ? 'var(--emerald-green)'
              : v.fuel_type === 'LNG'
              ? 'var(--cyan-primary)'
              : v.fuel_type === 'HFO'
              ? 'var(--coral-primary)'
              : '#38bdf8';

            return (
              <g
                key={v.id}
                transform={`translate(${pt.x}, ${pt.y})`}
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSelectedVessel(v);
                  if (onSelectVessel) onSelectVessel(v);
                }}
              >
                {/* Glow ring on selection */}
                {isSelected && (
                  <circle
                    r="14"
                    fill="none"
                    stroke={markerColor}
                    strokeWidth="2"
                    strokeDasharray="3 3"
                    className="pulse-ring"
                    opacity="0.9"
                  />
                )}
                {/* Vessel Pin Outer */}
                <circle r="7" fill="#070b14" stroke={markerColor} strokeWidth="2" />
                {/* Center dot */}
                <circle r="3.2" fill={markerColor} />

                {/* Vessel Label */}
                <text
                  x="0"
                  y="-11"
                  textAnchor="middle"
                  fill={isSelected ? '#ffffff' : '#cbd5e1'}
                  fontSize="8"
                  fontWeight="700"
                  style={{ textShadow: '0 1px 3px rgba(0,0,0,0.9)' }}
                >
                  {v.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Map Legend */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          background: 'rgba(10, 16, 30, 0.85)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '0.6rem 0.9rem',
          fontSize: '0.72rem',
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          color: 'var(--text-secondary)',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--cyan-primary)' }} />
            LNG Fueled
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--emerald-green)' }} />
            Methanol / Green
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8' }} />
            VLSFO
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--coral-primary)' }} />
            HFO (Scrubber)
          </span>
        </div>
      </div>

      {/* Selected Vessel Quick Telemetry Drawer */}
      {selectedVessel && (
        <div style={{
          marginTop: '1rem',
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(0, 242, 254, 0.1)',
              border: '1px solid var(--border-cyan)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Ship size={24} color="var(--cyan-primary)" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>{selectedVessel.name}</h3>
                <span className="badge badge-cyan">{selectedVessel.type}</span>
                <span className="badge badge-purple">{selectedVessel.subtype}</span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                ID: {selectedVessel.id} &bull; Near {selectedVessel.current_location?.nearest_port} &bull; Status: <span style={{ color: '#10b981', fontWeight: 600 }}>{selectedVessel.status}</span>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>DWT / Capacity</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>{selectedVessel.dwt.toLocaleString()} MT</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hull Age / Fouling</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: selectedVessel.hull_age_years > 6 ? 'var(--coral-deep)' : '#fff' }}>
                {selectedVessel.hull_age_years} yrs (Cf: {selectedVessel.fouling_coeff})
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Bunker Fuel</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--cyan-primary)' }}>{selectedVessel.fuel_type}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Daily Charter</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>₹{(selectedVessel.daily_charter_rate_inr ?? (selectedVessel.daily_charter_rate_usd * 84))?.toLocaleString()}/day</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>EEXI Status</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>
                {selectedVessel.eexi_compliant ? (
                  <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    <ShieldCheck size={14} /> Compliant
                  </span>
                ) : (
                  <span style={{ color: 'var(--coral-primary)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    <AlertTriangle size={14} /> EPL Required
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
