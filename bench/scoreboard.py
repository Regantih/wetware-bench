import argparse
import json
from pathlib import Path

from .probes import PROBES
from .substrates import make


def run_suite(substrate_names, probe_names, episodes, outdir, seeds=1):
    from .stats import aggregate, run_probe_seeds
    results = []
    for pname in probe_names:
        probe = PROBES[pname]
        for sname in substrate_names:
            sub = make(sname)  # role check only; stats run makes its own
            if probe.ROLE != "any" and probe.ROLE not in sub.roles:
                results.append(_skipped(probe, sname))
                continue
            kw = {"episodes": episodes} if pname == "learning_speed" else {}
            try:
                if seeds > 1:
                    res = aggregate(run_probe_seeds(sname, probe,
                                                  range(seeds), **kw))
                else:
                    res = probe.run(make(sname), **kw)
                print(f"  {pname:18s} {sname:10s} "
                      + "  ".join(f"{k}={v:.3g}" for k, v in res.metrics.items()))
            except Exception as e:  # keep the suite running, record the failure
                res = _skipped(probe, sname, f"error: {e}")
            res.substrate = sname
            results.append(res)
    _write(results, outdir)
    return results


def _skipped(probe, sname, note="skipped: incompatible role"):
    from .substrate import ProbeResult
    return ProbeResult(probe.NAME, sname, notes=note)


def _write(results, outdir):
    out = Path(outdir)
    out.mkdir(exist_ok=True)
    blob = [{"probe": r.probe, "substrate": r.substrate,
             "metrics": r.metrics, "series": r.series, "notes": r.notes}
            for r in results]
    (out / "results.json").write_text(json.dumps(blob, indent=2),
                                      encoding="utf-8")

    subs = sorted({r.substrate for r in results})
    lines = ["| probe | metric | " + " | ".join(subs) + " |",
             "|---|---|" + "---|" * len(subs)]
    for pname in dict.fromkeys(r.probe for r in results):
        rows = {r.substrate: r for r in results if r.probe == pname}
        headline = PROBES[pname].HEADLINE
        cells = []
        for s in subs:
            r = rows.get(s)
            if r is None or headline not in r.metrics:
                cells.append(r.notes.split(":")[0] if r else "—")
            else:
                st = r.series.get("stats", {}).get(headline)
                if st and st["n"] > 1:
                    cells.append(f"{st['mean']:.3g}±{st['ci95']:.2g}")
                else:
                    cells.append(f"{r.metrics[headline]:.3g}")
        lines.append(f"| {pname} | {headline} | " + " | ".join(cells) + " |")
    (out / "scoreboard.md").write_text("\n".join(lines) + "\n",
                                       encoding="utf-8")
    print("\n" + "\n".join(lines))
    print(f"\nwritten: {out/'results.json'}, {out/'scoreboard.md'}")


def main():
    p = argparse.ArgumentParser(prog="bench.scoreboard")
    p.add_argument("--substrates", nargs="+",
                   default=["snn", "tapdelay", "linear_pg"])
    p.add_argument("--probes", nargs="+", default=list(PROBES))
    p.add_argument("--episodes", type=int, default=40)
    p.add_argument("--seeds", type=int, default=1,
                   help="run each probe on N fresh seeds; report mean±95%%CI")
    p.add_argument("--compare-codec", action="store_true",
                   help="also run each substrate wrapped in the learned codec")
    p.add_argument("--out", default="results")
    a = p.parse_args()
    subs = list(a.substrates)
    if a.compare_codec:
        subs += [f"{s}+enc" for s in a.substrates if not s.endswith("+enc")]
    run_suite(subs, a.probes, a.episodes, a.out, seeds=a.seeds)


if __name__ == "__main__":
    main()
