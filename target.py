"""Naive N-body simulation. The target the agent optimizes."""

import os
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'

import numpy as np

N_BODIES = 200
N_STEPS = 400
DT = 0.01
G = 1.0
SEED = 42


def init_bodies(n):
    rng = np.random.default_rng(SEED)
    pos = rng.uniform(-1, 1, (n, 3))
    px, py, pz = pos[:, 0].copy(), pos[:, 1].copy(), pos[:, 2].copy()
    vx = np.zeros(n)
    vy = np.zeros(n)
    vz = np.zeros(n)
    mass = rng.uniform(0.1, 1.0, n)
    return px, py, pz, vx, vy, vz, mass


def step(px, py, pz, vx, vy, vz, mass, dt, ii, jj, mm_ij, inv_mass, starts_ii, ax, ay, az):
    n = len(mass)
    dx = px[jj] - px[ii]
    dy = py[jj] - py[ii]
    dz = pz[jj] - pz[ii]
    r2 = dx*dx + dy*dy + dz*dz + 1e-6
    r = np.sqrt(r2)
    f = mm_ij / (r2 * r)
    fx = f * dx
    fy = f * dy
    fz = f * dz
    # ii is sorted: use reduceat for contiguous segment sums (15x faster than bincount)
    # jj is unsorted: use add.at scatter
    ax[:n-1] = np.add.reduceat(fx, starts_ii)
    ax[n-1] = 0.0
    np.add.at(ax, jj, -fx)
    ax *= inv_mass
    ay[:n-1] = np.add.reduceat(fy, starts_ii)
    ay[n-1] = 0.0
    np.add.at(ay, jj, -fy)
    ay *= inv_mass
    az[:n-1] = np.add.reduceat(fz, starts_ii)
    az[n-1] = 0.0
    np.add.at(az, jj, -fz)
    az *= inv_mass
    vx += ax * dt
    vy += ay * dt
    vz += az * dt
    px += vx * dt
    py += vy * dt
    pz += vz * dt


def total_energy(px, py, pz, vx, vy, vz, mass):
    ke = 0.5 * np.sum(mass * (vx**2 + vy**2 + vz**2))
    pos = np.stack([px, py, pz], axis=1)
    diff = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]
    r2 = np.sum(diff ** 2, axis=2) + 1e-6
    r = np.sqrt(r2)
    i, j = np.triu_indices(len(mass), k=1)
    pe = -G * np.sum(mass[i] * mass[j] / r[i, j])
    return ke + pe


def main():
    px, py, pz, vx, vy, vz, mass = init_bodies(N_BODIES)
    n = N_BODIES
    ii, jj = np.triu_indices(n, k=1)
    mm_ij = G * mass[ii] * mass[jj]
    inv_mass = 1.0 / mass
    # precompute reduceat segment starts for sorted ii
    # body k appears (n-1-k) times; cumsum gives segment boundaries
    starts_ii = np.concatenate([[0], np.cumsum(np.arange(n-1, 1, -1))])
    ax = np.empty(n)
    ay = np.empty(n)
    az = np.empty(n)
    e0 = total_energy(px, py, pz, vx, vy, vz, mass)
    for _ in range(N_STEPS):
        step(px, py, pz, vx, vy, vz, mass, DT, ii, jj, mm_ij, inv_mass, starts_ii, ax, ay, az)
    e1 = total_energy(px, py, pz, vx, vy, vz, mass)
    drift = abs(e1 - e0) / abs(e0)
    print(f"energy_drift: {drift:.6e}")


if __name__ == "__main__":
    main()
