"""Verify this redesign did not change engine files or non-UI function ASTs."""
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "55e990d962ed22ae1021f0d335db197607bddda1"
PATH = "nuvem/core/wall_modeling.py"
ALLOWED = {
    "_style_primary_button", "_style_secondary_button", "_build_section_label",
    "_ProgressConsole", "_SetupForm", "_PostCreationForm", "_WallReviewForm",
    "_WallSourceModeForm", "_select_existing_walls_for_modulation",
    "run_modulation_on_existing_walls",
}


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=ROOT).decode("utf-8")


def definitions(tree):
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


def main():
    before = definitions(ast.parse(git("show", BASE + ":" + PATH)))
    after = definitions(ast.parse((ROOT / PATH).read_text(encoding="utf-8")))
    changed = sorted(name for name in set(before) | set(after)
                     if name not in before or name not in after or
                     ast.dump(before[name]) != ast.dump(after[name]))
    unexpected = sorted(set(changed) - ALLOWED)
    engine_diff = git("diff", "--name-only", BASE, "--", "nuvem/core/engine", "nuvem/benchmark", "Script.py").splitlines()
    handler_same = ast.dump(before["_PostCreationEventHandler"]) == ast.dump(after["_PostCreationEventHandler"])
    old_console, new_console = definitions(before["_ProgressConsole"]), definitions(after["_ProgressConsole"])
    protected = ("_pump_ui", "_invoke_if_needed", "_on_watchdog_tick", "stop_watchdog", "close")
    threading_same = all(ast.dump(old_console[name]) == ast.dump(new_console[name]) for name in protected)
    result = {"base": BASE, "head": git("rev-parse", "HEAD").strip(),
              "changed_definitions": changed, "unexpected_definitions": unexpected,
              "engine_benchmark_loader_changed": engine_diff,
              "entire_external_event_handler_ast_unchanged": handler_same,
              "threading_dispatch_pump_and_timer_methods_unchanged": threading_same,
              "unchanged_top_level_definitions": len(before) - len(changed),
              "ok": not unexpected and not engine_diff and handler_same and threading_same}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
