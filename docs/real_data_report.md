# Real-data report — recorded organoid vs. simulated SNN

| metric | fs363-org0 | fs363-org1 | fs363-org2 | fs363-org3 | sim_snn (resting) |
|---|---|---|---|---|---|
| duration (s) | 400 | 599 | 599 | 600 | 1.2e+03 |
| channels | 8 | 8 | 8 | 8 | 8 |
| active channels | 8 | 8 | 8 | 8 | 8 |
| spikes | 4.22e+03 | 9.88e+03 | 4.71e+03 | 4.39e+03 | 6.92e+03 |
| mean rate (Hz) | 1.32 | 2.06 | 0.983 | 0.914 | 0.72 |
| max rate (Hz) | 2.96 | 6.77 | 1.81 | 2.29 | 0.876 |
| Fano factor (burstiness) | 17.3 | 64.8 | 63.8 | 14.9 | 21.7 |
| drift similarity (1=stationary) | 0.993 | 0.985 | 0.764 | 0.991 | 0.937 |
| mean |channel corr| | 0.256 | 0.66 | 0.487 | 0.231 | 0.388 |
| max channel corr | 0.977 | 0.985 | 0.992 | 0.989 | 0.605 |

- **Fano factor** >>1 means bursty/poisson-clustered activity; ~1 means regular. Living MEA data is typically far burstier than a Poisson process.
- **Drift similarity** <0.9 over a session means the 'computer' measurably changed while you watched it.
- **Channel corr** on real MEAs shows structured co-activation; an uncorrelated sim understates coupling.
