# Bencher

A benchmarking tool that samples CPU, RAM, and storage (read/write) usage of a process over time.

It can either **launch** an executable or **attach** to an already-running process (via `pidof`), then export results as CSV, PNG plots, and LaTeX (pgfplots).

## Dependencies

* Python 3.x
* Packages listed in `requirements.txt` (`psutil`, `matplotlib`, `pandas`)
* `pidof` (for attach mode)

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
./env.sh
```

## Running examples

Usage examples live in `src/bench.py` and are selected by argument:

```bash
python3 src/bench.py <example>
```

| Example | Description |
|---|---|
| `launch_by_name` | Launch the app and save under `results/<name>/` (**default**) |
| `launch_per_pid` | Launch the app and save under `results/<name>/<pid>/` |
| `attach_by_name` | Attach via `pidof`; save all matching PIDs under `results/<name>/` |
| `attach_per_pid` | Attach via `pidof`; save each PID under `results/<name>/<pid>/` |

```bash
python3 src/bench.py launch_by_name
python3 src/bench.py attach_per_pid
python3 src/bench.py --help
```

The examples target `gnome-text-editor` by default. Change the process in `_base_config()` inside `src/bench.py`, or build your own `BencherConfig`.

## Configuration (`BencherConfig`)

| Attribute | Default | Description |
|---|---|---|
| `name` | `""` | Label used for results directories |
| `executable` | `""` | Binary to launch, or process name for `pidof` |
| `args` | `[]` | Arguments passed when launching |
| `callback` | `None` | Optional callback invoked after each sample |
| `sample_time` | `1` | Seconds between samples |
| `sample_total` | `100` | Number of samples to collect |
| `attach` | `False` | If `True`, find the process with `pidof` instead of launching it |
| `save_per_pid` | `False` | If `True`, store under `results/<name>/<pid>/`; otherwise under `results/<name>/` |
| `wait_timeout` | `30.0` | Max seconds to wait for the process when attaching |
| `wait_timestep` | `0.5` | Poll interval (seconds) while waiting for `pidof` |

## Custom usage

```python
from bencher import Bencher, BencherConfig

cfg = BencherConfig()
cfg.name = "firefox"
cfg.executable = "firefox"
cfg.sample_time = 0.1
cfg.sample_total = 50
cfg.attach = True
cfg.save_per_pid = True
cfg.wait_timeout = 30.0
cfg.wait_timestep = 0.5

b = Bencher()
b.set(cfg)
b.run()

b.save_csv()
b.save_png(show=True)
b.save_latex()
```

## Outputs

After a run, Bencher writes under `results/`:

* **CSV** — `save_csv()`
* **PNG plots** — `save_png()` (`cpu_usage.png`, `ram_usage.png`)
* **LaTeX plots** — `save_latex()` (`cpu_usage.tex`, `ram_usage.tex` using pgfplots)

Layout depends on `save_per_pid`:

* `False` → `results/<name>/...`
* `True` → `results/<name>/<pid>/...`

When attaching without `save_per_pid`, multiple PIDs are stored as separate CSV files named by PID under `results/<name>/`.
