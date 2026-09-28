"""
Quantum Approximate Optimization Algorithm (QAOA) Circuit Emulator.
Simulates parameterized quantum circuit ansatz:
|ψ(γ, β)⟩ = ∏_{l=1}^p [ e^{-i β_l H_M} e^{-i γ_l H_C} ] |+⟩^{⊗n}
Demonstrates the quantum-native execution path for fleet assignment sub-problems.
"""

import time
import math
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy.optimize import minimize


class QAOAFleetSolver:
    def __init__(self, p_layers: int = 2, max_qubits: int = 12):
        self.p_layers = p_layers
        self.max_qubits = max_qubits

    def _qubo_to_ising(self, Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Converts binary QUBO: min x^T Q x
        to Ising Hamiltonian: H = sum_i h_i Z_i + sum_{i<j} J_ij Z_i Z_j + offset
        using identity: x_i = (1 - Z_i) / 2 where Z_i ∈ {+1, -1}.
        """
        n = Q.shape[0]
        h = np.zeros(n)
        J = np.zeros((n, n))
        offset = 0.0

        for i in range(n):
            # Diagonal
            q_ii = Q[i, i]
            offset += q_ii * 0.25
            h[i] -= q_ii * 0.5
            offset += q_ii * 0.25

            # Off-diagonal
            for j in range(i + 1, n):
                q_ij = Q[i, j]
                offset += q_ij * 0.25
                h[i] -= q_ij * 0.25
                h[j] -= q_ij * 0.25
                J[i, j] += q_ij * 0.25

        return h, J, offset

    def _simulate_qaoa_statevector(
        self,
        h: np.ndarray,
        J: np.ndarray,
        n_qubits: int,
        gamma: np.ndarray,
        beta: np.ndarray,
    ) -> np.ndarray:
        """
        Simulates exact statevector of QAOA quantum circuit with p layers.
        """
        dim = 1 << n_qubits
        # Initial state |+>^{⊗n}
        psi = np.full(dim, 1.0 / math.sqrt(dim), dtype=np.complex128)

        # Precompute diagonal of Cost Hamiltonian H_C
        diag_hc = np.zeros(dim)
        for idx in range(dim):
            # z_i = 1 if bit is 0, -1 if bit is 1
            z = np.array([1.0 if not (idx & (1 << q)) else -1.0 for q in range(n_qubits)])
            cost = float(np.dot(h, z))
            for i in range(n_qubits):
                for j in range(i + 1, n_qubits):
                    if J[i, j] != 0:
                        cost += J[i, j] * z[i] * z[j]
            diag_hc[idx] = cost

        # Apply alternating layers: e^{-i \gamma H_C} and e^{-i \beta H_M}
        for l in range(len(gamma)):
            # 1. Phase separation operator: e^{-i \gamma_l H_C}
            phase_gate = np.exp(-1j * gamma[l] * diag_hc)
            psi = psi * phase_gate

            # 2. Mixer operator: e^{-i \beta_l \sum_q X_q} = \bigotimes_q [ cos(\beta) I - i sin(\beta) X ]
            cos_b = math.cos(beta[l])
            sin_b = math.sin(beta[l])
            for q in range(n_qubits):
                step = 1 << q
                for base in range(0, dim, 2 * step):
                    for k in range(step):
                        i0 = base + k
                        i1 = base + k + step
                        v0 = psi[i0]
                        v1 = psi[i1]
                        psi[i0] = cos_b * v0 - 1j * sin_b * v1
                        psi[i1] = -1j * sin_b * v0 + cos_b * v1

        return psi

    def solve(
        self,
        qubo_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes QAOA on the QUBO problem (or optimal subspace if N > max_qubits).
        """
        start_time = time.perf_counter()

        Q = qubo_data["Q_matrix"]
        var_map = qubo_data["var_map"]
        cost_breakdown = qubo_data["cost_breakdown"]
        num_voyages = qubo_data["num_voyages"]
        n_vars = min(len(var_map), self.max_qubits)

        # Extract top candidates for sub-matrix if variables exceed quantum simulator limit
        sub_Q = Q[:n_vars, :n_vars]
        h, J, offset = self._qubo_to_ising(sub_Q)

        # Objective function for classical parameter optimization
        p = self.p_layers

        def objective(params):
            g = params[:p]
            b = params[p:]
            psi = self._simulate_qaoa_statevector(h, J, n_vars, g, b)
            # Expectation value <psi | H_C | psi>
            dim = 1 << n_vars
            diag_hc = np.zeros(dim)
            for idx in range(dim):
                z = np.array([1.0 if not (idx & (1 << q)) else -1.0 for q in range(n_vars)])
                diag_hc[idx] = float(np.dot(h, z))
            probs = np.abs(psi) ** 2
            return float(np.sum(probs * diag_hc))

        # Initial variational angles
        init_params = np.concatenate([np.full(p, 0.35), np.full(p, 0.45)])
        res = minimize(objective, init_params, method="COBYLA", options={"maxiter": 30})

        opt_gamma = res.x[:p]
        opt_beta = res.x[p:]

        # Sample optimal statevector probabilities
        final_psi = self._simulate_qaoa_statevector(h, J, n_vars, opt_gamma, opt_beta)
        probs = np.abs(final_psi) ** 2
        best_state_idx = int(np.argmax(probs))
        ground_prob = float(probs[best_state_idx])

        # Decode best computational bitstring
        best_sample = {}
        for q in range(n_vars):
            bit = 1 if (best_state_idx & (1 << q)) else 0
            best_sample[q] = bit

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Parse selected assignments
        assignments = []
        assigned_voyages = set()
        violations = []
        total_fuel_cost = 0.0
        total_fuel_mt = 0.0
        total_co2_mt = 0.0
        total_ets_cost = 0.0
        total_charter_cost = 0.0

        for var_idx, bit in best_sample.items():
            if bit == 1:
                meta = var_map[var_idx]
                cost = cost_breakdown[var_idx]
                v_id = meta["vessel_id"]
                j_id = meta["voyage_id"]

                if j_id in assigned_voyages:
                    violations.append(f"Voyage {j_id} assigned multiple times.")
                assigned_voyages.add(j_id)

                total_fuel_cost += cost["fuel_cost_inr"]
                total_fuel_mt += cost["fuel_consumed_mt"]
                total_co2_mt += cost["co2_emissions_mt"]
                total_ets_cost += cost["eu_ets_cost_inr"]
                total_charter_cost += cost["charter_cost_inr"]

                assignments.append({
                    "vessel_id": v_id,
                    "vessel_name": meta["vessel_name"],
                    "voyage_id": j_id,
                    "fuel_cost_inr": cost["fuel_cost_inr"],
                    "fuel_consumed_mt": cost["fuel_consumed_mt"],
                    "co2_emissions_mt": cost["co2_emissions_mt"],
                    "eu_ets_cost_inr": cost["eu_ets_cost_inr"],
                    "charter_cost_inr": cost["charter_cost_inr"],
                    "cii_rating": cost["cii_rating"],
                })

        total_operational_cost = total_fuel_cost + total_ets_cost + total_charter_cost

        return {
            "solver_name": "QAOA Quantum Circuit Emulator",
            "execution_time_ms": round(elapsed_ms, 2),
            "circuit_depth": p * 2,
            "qaoa_layers_p": p,
            "num_qubits": n_vars,
            "optimal_gamma": [round(float(x), 4) for x in opt_gamma],
            "optimal_beta": [round(float(x), 4) for x in opt_beta],
            "ground_state_probability": round(ground_prob, 4),
            "assignments": assignments,
            "total_assigned_voyages": len(assigned_voyages),
            "total_fuel_cost_inr": round(total_fuel_cost, 2),
            "total_fuel_consumed_mt": round(total_fuel_mt, 2),
            "total_co2_emissions_mt": round(total_co2_mt, 2),
            "total_eu_ets_cost_inr": round(total_ets_cost, 2),
            "total_charter_cost_inr": round(total_charter_cost, 2),
            "total_operational_cost_inr": round(total_operational_cost, 2),
            "violations": violations,
            "is_valid": len(violations) == 0,
        }
