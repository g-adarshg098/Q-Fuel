import React, { useState, useEffect } from 'react';
import { BarChart3, Clock, DollarSign, Leaf, Zap, ShieldCheck, HelpCircle, Layers } from 'lucide-react';

export default function SolverBenchmark() {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchBenchmark();
  }, []);

  const fetchBenchmark = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/benchmark?voyage_count=6');
      const data = await res.json();
      setBenchmarkData(data);
    } catch (err) {
      console.error('Benchmark fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const solvers = benchmarkData?.benchmark_comparison || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div className="glass-card highlight-purple" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Layers size={22} color="var(--purple-quantum)" />
            Quantum vs Classical Solver Benchmark Suite
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Direct comparison of Quantum-Inspired Annealing, QAOA circuit ansatz, Classical HiGHS Branch-and-Cut, and Naive Baseline
          </p>
        </div>

        <button
          onClick={fetchBenchmark}
          disabled={loading}
          className="btn-secondary"
        >
          {loading ? 'Benchmarking Backends...' : 'Refresh Benchmark'}
        </button>
      </div>

      {/* Comparative Benchmark Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Solver Algorithm</th>
              <th>Paradigm</th>
              <th>Execution Time</th>
              <th>Total Fuel (MT)</th>
              <th>CO2e (MT)</th>
              <th>Total Cost (₹)</th>
              <th>Savings vs Greedy</th>
              <th>Feasibility</th>
            </tr>
          </thead>
          <tbody>
            {solvers.map((s, idx) => {
              const isGreedy = s.solver_name.includes('Greedy');
              const isQuantum = s.solver_name.includes('Quantum') || s.solver_name.includes('QAOA');
              const costInr = s.total_operational_cost_inr ?? s.total_operational_cost_usd;
              const savingsInr = s.savings_vs_greedy_inr ?? s.savings_vs_greedy_usd;
              return (
                <tr key={idx} style={{ background: isQuantum ? 'rgba(0, 242, 254, 0.03)' : 'transparent' }}>
                  <td>
                    <div style={{ fontWeight: 700, color: isQuantum ? 'var(--cyan-primary)' : '#fff' }}>
                      {s.solver_name}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${
                      s.solver_name.includes('QAOA') ? 'badge-purple' :
                      s.solver_name.includes('Annealer') ? 'badge-cyan' :
                      s.solver_name.includes('ILP') ? 'badge-emerald' : 'badge-coral'
                    }`}>
                      {s.solver_name.includes('QAOA') ? 'Quantum Native' :
                       s.solver_name.includes('Annealer') ? 'Quantum-Inspired' :
                       s.solver_name.includes('ILP') ? 'Exact Classical' : 'Heuristic'}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: '#fff' }}>{s.execution_time_ms} ms</span>
                  </td>
                  <td>
                    <strong style={{ color: '#fff' }}>{s.total_fuel_mt?.toLocaleString()} MT</strong>
                  </td>
                  <td>
                    <span style={{ color: 'var(--coral-deep)' }}>{s.total_co2_mt?.toLocaleString()} MT</span>
                  </td>
                  <td>
                    <strong style={{ color: isGreedy ? 'var(--coral-deep)' : 'var(--cyan-primary)' }}>
                      ₹{costInr?.toLocaleString()}
                    </strong>
                  </td>
                  <td>
                    {savingsInr > 0 ? (
                      <span style={{ color: 'var(--emerald-green)', fontWeight: 700 }}>
                        +₹{savingsInr?.toLocaleString()} ({s.savings_pct}%)
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>Baseline Ref</span>
                    )}
                  </td>
                  <td>
                    {s.is_valid ? (
                      <span style={{ color: 'var(--emerald-green)', display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: 600 }}>
                        <ShieldCheck size={14} /> Valid
                      </span>
                    ) : (
                      <span style={{ color: 'var(--coral-primary)', fontWeight: 600 }}>Infeasible</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Comparative Insights Grid */}
      <div className="grid-3">
        <div className="glass-card highlight-cyan">
          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--cyan-primary)', marginBottom: '0.65rem' }}>
            Quantum-Inspired Annealing
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Simulates quantum thermal fluctuations and transverse-field tunneling via D-Wave Ocean's Ising sampler. Effectively tunnels through tall, narrow potential energy barriers to find global low-cost fleet configurations without getting trapped in local minima.
          </p>
          <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Key strength: Scales favorably as fleet size N and concurrent voyages grow exponentially.
          </div>
        </div>

        <div className="glass-card highlight-purple">
          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--purple-quantum)', marginBottom: '0.65rem' }}>
            QAOA Circuit Emulator
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Implements the Quantum Approximate Optimization Algorithm ansatz |&psi;(&gamma;, &beta;)&rang; parameterized with alternating problem cost and mixer unitaries. Demonstrates the quantum-native path for upcoming QPUs (IBM Quantum, Rigetti).
          </p>
          <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Key strength: Native quantum execution on noisy intermediate-scale quantum (NISQ) hardware.
          </div>
        </div>

        <div className="glass-card highlight-emerald">
          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--emerald-green)', marginBottom: '0.65rem' }}>
            Classical HiGHS ILP
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            State-of-the-art branch-and-cut linear programming solver. Provides the mathematically guaranteed optimal integer solution, serving as the ground-truth benchmark to verify quantum solver quality and convergence.
          </p>
          <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Key strength: Exact optimum guarantee for small and medium fleet sizes.
          </div>
        </div>
      </div>
    </div>
  );
}
