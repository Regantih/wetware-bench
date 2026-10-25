# Real-data report — recorded organoid vs. simulated SNN

| metric | fs363-org0 | fs363-org1 | fs363-org2 | fs363-org3 | sim_snn |
|---|---|---|---|---|---|
| transfer entropy mean (bits) | 0.00144 | 0.00579 | 0.00336 | 0.00205 | 0.0077 |
| transfer entropy max (bits) | 0.0129 | 0.0172 | 0.0152 | 0.0101 | 0.0173 |
| avalanches | 1.28e+03 | 1.09e+03 | 1.05e+03 | 1.7e+03 | 507 |
| avalanche size (median) | 1 | 1 | 1 | 1 | 25 |
| avalanche size (max) | 305 | 1.22e+03 | 555 | 529 | 911 |
| branching param σ (~1=critical) | 1.22 | 1.22 | 1.21 | 1.11 | 1.64 |
| avalanche size α (~1.5=critical) | 2.31 | 1.83 | 2.39 | 2.58 | 1.68 |
| duration (s) | 400 | 599 | 599 | 600 | 6e+03 |
| channels | 8 | 8 | 8 | 8 | 8 |
| active channels | 8 | 8 | 8 | 8 | 8 |
| spikes | 4.22e+03 | 9.88e+03 | 4.71e+03 | 4.39e+03 | 4.08e+04 |
| mean rate (Hz) | 1.32 | 2.06 | 0.983 | 0.914 | 0.85 |
| max rate (Hz) | 2.96 | 6.77 | 1.81 | 2.29 | 0.98 |
| Fano factor (burstiness) | 17.3 | 64.8 | 63.8 | 14.9 | 22.4 |
| drift similarity (1=stationary) | 0.993 | 0.985 | 0.764 | 0.991 | 0.979 |
| mean |channel corr| | 0.256 | 0.66 | 0.487 | 0.231 | 0.383 |
| max channel corr | 0.977 | 0.985 | 0.992 | 0.989 | 0.498 |

- **Fano factor** >>1 means bursty/poisson-clustered activity; ~1 means regular. Living MEA data is typically far burstier than a Poisson process.
- **Drift similarity** <0.9 over a session means the 'computer' measurably changed while you watched it.
- **Channel corr** on real MEAs shows structured co-activation; an uncorrelated sim understates coupling.
