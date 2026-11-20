"""Regenerate every artefact: data -> forecast -> mix -> docs -> figures -> deck -> tests.
Usage:  python run_all.py            (everything)
        python run_all.py --no-deck  (skip the Node deck build)"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def step(name, fn):
    t = time.time()
    fn()
    print(f"  ✓ {name} ({time.time() - t:.1f}s)")


def main():
    from src import clean, geo, regional_cards, docs_build, report_figs
    from src.forecast import run as forecast_run
    from src import mix
    step("data: ingest + clean + NPP consistency check", clean.run)
    step("map geometry", geo.build)
    step("forecast: models, back-test, MC, reconciliation", forecast_run.run)
    step("mix: back-tested share models, regional allocation, validation", mix.run)
    step("parameter register + headline", docs_build.build)
    step("regional cards", regional_cards.build)
    step("deck figures", report_figs.build)
    if "--no-deck" not in sys.argv:
        import shutil
        node = shutil.which("node")
        if node is None:
            print("  ! deck build skipped: Node.js not found (the ready-made deck/*.pptx is unchanged)")
        else:
            r = subprocess.run([node, str(ROOT / "deck" / "build_deck.js")], cwd=ROOT)
            print("  ✓ deck" if r.returncode == 0 else "  ! deck build skipped (needs pptxgenjs: cd deck && npm install)")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
