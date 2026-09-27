# Checks the numpy QAOA simulator against Qiskit's Statevector for a random 5-variable QUBO.
import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qsel.solvers import qaoa_state
from qsel.qubo import all_energies
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate
from qiskit.quantum_info import Statevector


def test_qaoa_matches_qiskit():
    rng = np.random.default_rng(1); n = 5
    Q = np.triu(rng.normal(size=(n, n))); E = all_energies(Q)
    cost = (E - E.min()) / (E.max() - E.min())
    g, b = [0.7, 1.3], [0.4, 0.9]
    psi = qaoa_state(cost, n, g, b)
    qc = QuantumCircuit(n); qc.h(range(n))
    for gg, bb in zip(g, b):
        qc.append(DiagonalGate(list(np.exp(-1j * gg * cost))), range(n))
        for q in range(n): qc.rx(2 * bb, q)
    sv = Statevector(qc).data
    fid = abs(np.vdot(sv, psi)) ** 2
    assert fid > 1 - 1e-9, fid
    # energies: brute-force check of all_energies
    for v in [0, 7, 19, 31]:
        x = np.array([(v >> i) & 1 for i in range(n)], float)
        assert abs(x @ Q @ x - E[v]) < 1e-4
    print('numpy QAOA matches Qiskit Statevector: fidelity =', fid)


if __name__ == '__main__':
    test_qaoa_matches_qiskit()
