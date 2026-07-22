#!/usr/bin/env python3
"""Example entry points for Bencher.

Usage:
    python3 src/bench.py <example>

Examples:
    launch_by_name      Launch the app and save under results/<name>/
    launch_per_pid      Launch the app and save under results/<name>/<pid>/
    attach_by_name      Attach via pidof; save all matching PIDs under results/<name>/
    attach_per_pid      Attach via pidof; save each PID under results/<name>/<pid>/
"""

from __future__ import annotations

import argparse
import sys

from bencher import Bencher, BencherConfig


def callback(b: Bencher):
    # print(f"b.cpu_pct: {b.cpu_pct[-1]} % | b.mem_info: {b.mem_info[-1]} | b.read_bytes:{b.read_bytes[-1]}")
    pass


def run_bencher(cfg: BencherConfig, repeat_n_times: int = 1, show_plots: bool = True) -> Bencher:
    """Configure, run, and export results for a BencherConfig."""
    b = Bencher()
    b.set(cfg)

    if cfg.attach:
        b.run()
    else:
        for _ in range(repeat_n_times):
            b.run()

    b.save_csv()
    b.save_png(show=show_plots)
    b.save_latex()
    return b


def _base_config(name: str = "gnome-text-editor") -> BencherConfig:
    cfg = BencherConfig()
    cfg.name = name
    cfg.executable = name
    cfg.args = [""]
    cfg.callback = callback
    cfg.sample_time = 0.1
    cfg.sample_total = 50
    cfg.wait_timeout = 30.0
    cfg.wait_timestep = 0.5
    return cfg


def example_launch_by_name():
    """Launch the process repeatedly and store results under results/<name>/."""
    cfg = _base_config()
    cfg.attach = False
    cfg.save_per_pid = False
    return run_bencher(cfg, repeat_n_times=3)


def example_launch_per_pid():
    """Launch the process repeatedly and store results under results/<name>/<pid>/."""
    cfg = _base_config()
    cfg.attach = False
    cfg.save_per_pid = True
    return run_bencher(cfg, repeat_n_times=3)


def example_attach_by_name():
    """Wait for an already-running process (pidof) and save all PIDs under results/<name>/."""
    cfg = _base_config()
    cfg.attach = True
    cfg.save_per_pid = False
    cfg.wait_timeout = 30.0
    cfg.wait_timestep = 0.5
    return run_bencher(cfg)


def example_attach_per_pid():
    """Wait for an already-running process (pidof) and save each PID under results/<name>/<pid>/."""
    cfg = _base_config()
    cfg.attach = True
    cfg.save_per_pid = True
    cfg.wait_timeout = 30.0
    cfg.wait_timestep = 0.5
    return run_bencher(cfg)


EXAMPLES = {
    "launch_by_name": example_launch_by_name,
    "launch_per_pid": example_launch_per_pid,
    "attach_by_name": example_attach_by_name,
    "attach_per_pid": example_attach_per_pid,
}


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Run a Bencher usage example.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "example",
        nargs="?",
        default="launch_by_name",
        choices=sorted(EXAMPLES.keys()),
        help="Which example to run (default: launch_by_name)",
    )
    args = parser.parse_args(argv)

    print(f"Running example: {args.example}")
    EXAMPLES[args.example]()


if __name__ == "__main__":
    main(sys.argv[1:])
