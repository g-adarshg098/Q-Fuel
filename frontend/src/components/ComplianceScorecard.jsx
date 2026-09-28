import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, FileText, DollarSign, Award, Leaf, Zap, BarChart2 } from 'lucide-react';

export default function ComplianceScorecard() {
  const [complianceData, setComplianceData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCompliance();
  }, []);

  const fetchCompliance = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/compliance');
      const data = await res.json();
      setComplianceData(data);
    } catch (err) {
      console.error('Failed to load compliance scorecard:', err);
    } finally {
      setLoading(false);
    }
  };

  const summary = complianceData?.fleet_summary;
  const scorecards = complianceData?.vessel_scorecards || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div className="glass-card highlight-cyan" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Award size={22} color="#b8860b" />
            IMO CII & EEXI Compliance Scorecard & EU ETS Exposure
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#475569' }}>
            MEPC.337(76) Operational Carbon Intensity Indicator rating audit, MARPOL Annex VI EEXI limiters, and EU ETS carbon liabilities
          </p>
        </div>

        <button
          onClick={fetchCompliance}
          disabled={loading}
          className="btn-secondary"
        >
          {loading ? 'Auditing Fleet...' : 'Re-calculate Audit'}
        </button>
      </div>

      {/* Fleet KPI Summary Cards */}
      {summary && (
        <div className="grid-4">
          <div className="stat-box" style={{ borderLeft: '3px solid var(--emerald-green)' }}>
            <div className="stat-label">CII Compliant Fleet (A-C)</div>
            <div className="stat-val emerald">
              {summary.compliant_vessels_count} / {summary.total_vessels}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--emerald-green)', fontWeight: 700, marginTop: '0.2rem' }}>
              {Math.round((summary.compliant_vessels_count / summary.total_vessels) * 100)}% of fleet compliant
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid var(--coral-primary)' }}>
            <div className="stat-label">At-Risk Vessels (D & E)</div>
            <div className="stat-val coral">
              {summary.at_risk_vessels_count} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Vessels</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--coral-deep)', fontWeight: 700, marginTop: '0.2rem' }}>
              Action plan required
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid var(--cyan-primary)' }}>
            <div className="stat-label">EEXI Technical Compliance</div>
            <div className="stat-val cyan">
              {summary.eexi_compliance_rate_pct}%
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Engine power limiter verified
            </div>
          </div>

          <div className="stat-box" style={{ borderLeft: '3px solid var(--amber-gold)' }}>
            <div className="stat-label">Estimated EU ETS Exposure</div>
            <div className="stat-val" style={{ color: 'var(--amber-gold)' }}>
              ₹{(summary.total_eu_ets_cost_inr ?? summary.total_eu_ets_cost_usd)?.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Total CO2: {summary.total_co2_emissions_mt?.toLocaleString()} MT
            </div>
          </div>
        </div>
      )}

      {/* Fleet CII Rating Distribution Bar */}
      {summary && (
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a' }}>
              Fleet Operational CII Rating Distribution (MEPC.337(76))
            </h4>
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.78rem' }}>
              <span style={{ color: '#10b981', fontWeight: 700 }}>A (Superior): {summary.rating_distribution?.A}</span>
              <span style={{ color: '#3b82f6', fontWeight: 700 }}>B (Minor Sup): {summary.rating_distribution?.B}</span>
              <span style={{ color: '#f59e0b', fontWeight: 700 }}>C (Moderate): {summary.rating_distribution?.C}</span>
              <span style={{ color: '#ff5722', fontWeight: 700 }}>D (Inferior): {summary.rating_distribution?.D}</span>
              <span style={{ color: '#ef4444', fontWeight: 700 }}>E (Critical): {summary.rating_distribution?.E}</span>
            </div>
          </div>

          {/* Segmented Distribution Bar */}
          <div style={{ height: '14px', borderRadius: '7px', display: 'flex', overflow: 'hidden', background: 'rgba(255,255,255,0.06)' }}>
            <div style={{ width: `${(summary.rating_distribution?.A / summary.total_vessels) * 100}%`, background: '#10b981' }} title="A" />
            <div style={{ width: `${(summary.rating_distribution?.B / summary.total_vessels) * 100}%`, background: '#3b82f6' }} title="B" />
            <div style={{ width: `${(summary.rating_distribution?.C / summary.total_vessels) * 100}%`, background: '#f59e0b' }} title="C" />
            <div style={{ width: `${(summary.rating_distribution?.D / summary.total_vessels) * 100}%`, background: '#ff5722' }} title="D" />
            <div style={{ width: `${(summary.rating_distribution?.E / summary.total_vessels) * 100}%`, background: '#ef4444' }} title="E" />
          </div>
        </div>
      )}

      {/* Vessel Audit Scorecard Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #e2e8f0' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
            Vessel-by-Vessel Statutory Compliance Audit
          </h3>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Vessel Name & Class</th>
              <th>Fuel Grade</th>
              <th>Distance (NM)</th>
              <th>Attained CII</th>
              <th>Benchmark</th>
              <th>CII Rating Band</th>
              <th>EEXI Status</th>
              <th>EU ETS Liability</th>
              <th>Prescriptive Action</th>
            </tr>
          </thead>
          <tbody>
            {scorecards.map((sc, idx) => (
              <tr key={sc.vessel_id || idx}>
                <td>
                  <div style={{ fontWeight: 700, color: '#0f172a' }}>{sc.vessel_name}</div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    {sc.vessel_type} &bull; {sc.dwt?.toLocaleString()} DWT
                  </div>
                </td>
                <td>
                  <span className="badge badge-cyan">{sc.fuel_type}</span>
                </td>
                <td>{sc.total_distance_nm?.toLocaleString()}</td>
                <td>
                  <strong style={{ color: sc.status_color }}>{sc.annual_attained_cii}</strong>
                </td>
                <td>{sc.annual_required_cii}</td>
                <td>
                  <span
                    className="badge"
                    style={{
                      background: `${sc.status_color}22`,
                      color: sc.status_color,
                      border: `1px solid ${sc.status_color}66`,
                    }}
                  >
                    Band {sc.annual_rating}
                  </span>
                </td>
                <td>
                  {sc.eexi_compliant ? (
                    <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.78rem', fontWeight: 600 }}>
                      <ShieldCheck size={14} /> Passed
                    </span>
                  ) : (
                    <span style={{ color: 'var(--coral-primary)', display: 'flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.78rem', fontWeight: 600 }}>
                      <AlertTriangle size={14} /> Limiter Req.
                    </span>
                  )}
                </td>
                <td>
                  <strong style={{ color: (sc.total_eu_ets_cost_inr ?? sc.total_eu_ets_cost_usd) > 0 ? 'var(--amber-gold)' : 'var(--text-muted)' }}>
                    ₹{(sc.total_eu_ets_cost_inr ?? sc.total_eu_ets_cost_usd)?.toLocaleString()}
                  </strong>
                </td>
                <td>
                  {sc.corrective_action ? (
                    <span style={{ fontSize: '0.75rem', color: 'var(--coral-deep)', fontWeight: 600 }}>
                      {sc.corrective_action}
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: '#10b981' }}>Compliant - No action needed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
