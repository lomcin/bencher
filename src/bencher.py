import os
import psutil
import subprocess
import time
import pandas
import matplotlib.pyplot as plt


class BencherConfig:
    def __init__(self):
        self.name = ""
        self.executable = ""
        self.args = list([])
        self.callback = None
        self.sample_time = 1
        self.sample_total = 100
        # Attach to an already-running process via `pidof` instead of launching it.
        self.attach = False
        # Process names for pidof when attach=True. Multiple names are sampled concurrently.
        # If empty, falls back to [executable or name].
        self.attach_names = list([])
        # True: store under results/<name>/<pid>/; False: store under results/<name>/ (many pids share the name).
        self.save_per_pid = False
        # How long to wait (seconds) for the process to appear when attaching.
        self.wait_timeout = 30.0
        # How often (seconds) to poll `pidof` while waiting for the process to start.
        self.wait_timestep = 0.5


class BencherData:
    def __init__(self):
        self.pid = None
        self.process_name = None
        self.cpu_pct = list()
        self.mem_info = list()
        self.num_threads = list()
        self.read_count = list()
        self.read_bytes = list()
        self.write_count = list()
        self.write_bytes = list()
        self.sample_timestamp = list()
        self.process_died = None

    def clear(self):
        self.pid = None
        self.process_name = None
        self.cpu_pct.clear()
        self.mem_info.clear()
        self.num_threads.clear()
        self.read_count.clear()
        self.read_bytes.clear()
        self.write_count.clear()
        self.write_bytes.clear()
        self.sample_timestamp.clear()
        self.process_died = None

    def to_dict(self) -> dict:
        d = dict()
        d['cpu_pct'] = self.cpu_pct
        d['mem_info'] = self.mem_info
        d['num_threads'] = self.num_threads
        d['read_count'] = self.read_count
        d['read_bytes'] = self.read_bytes
        d['write_count'] = self.write_count
        d['write_bytes'] = self.write_bytes
        d['sample_timestamp'] = self.sample_timestamp

        for k in d.keys():
            print(f'{k}:{len(d[k])}')
        print("-----------------------------")

        return d

    def to_data_frame(self) -> pandas.DataFrame:
        df = pandas.DataFrame()
        df = df.from_dict(self.to_dict())
        return df


class Bencher:

    def __init__(self):

        # Data
        self.data = None
        self.data_history = list([])

        # Config
        self.name = "unnamed"
        self.executable = ""
        self.args = list([""])
        self.callback = None
        self.sample_time = 1
        self.sample_total = 100
        self.sample_current = 0
        self.attach = False
        self.attach_names = list([])
        self.save_per_pid = False
        self.wait_timeout = 30.0
        self.wait_timestep = 0.5

        # Status
        self.done = False
        self.init_time = 0
        self.process_died = False

    def set(self, config: BencherConfig):
        self.name = config.name
        self.executable = config.executable
        self.args = config.args
        self.callback = config.callback
        self.sample_time = config.sample_time
        self.sample_total = config.sample_total
        self.attach = config.attach
        self.attach_names = list(config.attach_names) if config.attach_names else []
        self.save_per_pid = config.save_per_pid
        self.wait_timeout = config.wait_timeout
        self.wait_timestep = config.wait_timestep
        self.sample_current = 0

    def _results_base(self, data: BencherData) -> str:
        """Directory label under results/ for a sample set."""
        if data.process_name:
            return data.process_name.replace(' ', '-')
        return self.name

    def results_dir_for(self, data: BencherData) -> str:
        """Return the results directory path for a given sample set."""
        base = self._results_base(data)
        if self.save_per_pid and data.pid is not None:
            return f'results/{base}/{data.pid}/'
        return f'results/{base}/'

    def _result_groups(self):
        """Yield (results_dir, label, entries) groups for saving plots/data."""
        if not self.data_history:
            return

        if self.save_per_pid:
            by_key = {}
            for data in self.data_history:
                key = (self._results_base(data), data.pid)
                by_key.setdefault(key, []).append(data)
            for (base, pid), entries in by_key.items():
                yield (
                    f'results/{base}/{pid}/',
                    f"{base} (pid {pid})",
                    entries,
                )
            return

        by_base = {}
        for data in self.data_history:
            base = self._results_base(data)
            by_base.setdefault(base, []).append(data)
        for base, entries in by_base.items():
            yield f'results/{base}/', base, entries

    def _plot_metric(self, entries, label: str, attr: str, ylabel: str, title: str):
        fig, ax = plt.subplots()
        show_legend = False
        for data in entries:
            legend = f"pid {data.pid}" if data.pid is not None else None
            if legend is not None:
                show_legend = True
            ax.plot(data.sample_timestamp, getattr(data, attr), label=legend)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Sample timestamp (s)")
        if show_legend:
            ax.legend()
        fig.tight_layout()
        return fig

    def save_csv(self):
        """Persist each BencherData sample set as CSV under the configured results layout."""
        saved = []
        for results_dir, _label, entries in self._result_groups():
            os.makedirs(results_dir, exist_ok=True)
            for i, data in enumerate(entries):
                if (
                    not self.save_per_pid
                    and data.pid is not None
                    and self.attach
                    and len(entries) > 1
                ):
                    path = os.path.join(results_dir, f'{data.pid}.csv')
                else:
                    path = os.path.join(results_dir, f'{i}.csv')
                data.to_data_frame().to_csv(path)
                saved.append(path)
        return saved

    def save_png(self, show: bool = False):
        """Save CPU and RAM plots as PNG images under the results directories."""
        saved = []
        for results_dir, label, entries in self._result_groups():
            os.makedirs(results_dir, exist_ok=True)

            cpu_path = os.path.join(results_dir, 'cpu_usage.png')
            ram_path = os.path.join(results_dir, 'ram_usage.png')

            fig = self._plot_metric(
                entries, label, 'cpu_pct', 'CPU Usage (%)',
                f"{label}'s CPU Usage (%)",
            )
            fig.savefig(cpu_path)
            if show:
                plt.show()
            else:
                plt.close(fig)

            fig = self._plot_metric(
                entries, label, 'mem_info', 'RAM Usage (bytes)',
                f"{label}'s RAM Usage (bytes)",
            )
            fig.savefig(ram_path)
            if show:
                plt.show()
            else:
                plt.close(fig)

            saved.extend([cpu_path, ram_path])
        return saved

    def _latex_escape(self, text: str) -> str:
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        return ''.join(replacements.get(ch, ch) for ch in text)

    def _tikz_plot(self, entries, attr: str, ylabel: str, title: str) -> str:
        lines = [
            r'\begin{tikzpicture}',
            r'\begin{axis}[',
            f'  title={{{self._latex_escape(title)}}},',
            r'  xlabel={Sample timestamp (s)},',
            f'  ylabel={{{self._latex_escape(ylabel)}}},',
            r'  legend pos=north east,',
            r'  grid=major,',
            r'  width=\linewidth,',
            r']',
        ]
        for data in entries:
            coords = ' '.join(
                f'({t:.6g},{v:.6g})'
                for t, v in zip(data.sample_timestamp, getattr(data, attr))
            )
            lines.append(r'\addplot coordinates {')
            lines.append(f'  {coords}')
            lines.append(r'};')
            if data.pid is not None:
                lines.append(f'\\addlegendentry{{pid {data.pid}}}')
        lines.append(r'\end{axis}')
        lines.append(r'\end{tikzpicture}')
        return '\n'.join(lines)

    def save_latex(self):
        """Save CPU and RAM plots as standalone LaTeX (pgfplots) files."""
        saved = []
        for results_dir, label, entries in self._result_groups():
            os.makedirs(results_dir, exist_ok=True)

            header = '\n'.join([
                r'\documentclass{standalone}',
                r'\usepackage{pgfplots}',
                r'\pgfplotsset{compat=1.18}',
                r'\begin{document}',
            ])
            footer = r'\end{document}'

            cpu_path = os.path.join(results_dir, 'cpu_usage.tex')
            with open(cpu_path, 'w', encoding='utf-8') as f:
                f.write(header + '\n')
                f.write(self._tikz_plot(
                    entries, 'cpu_pct', 'CPU Usage (%)',
                    f"{label}'s CPU Usage (%)",
                ))
                f.write('\n' + footer + '\n')

            ram_path = os.path.join(results_dir, 'ram_usage.tex')
            with open(ram_path, 'w', encoding='utf-8') as f:
                f.write(header + '\n')
                f.write(self._tikz_plot(
                    entries, 'mem_info', 'RAM Usage (bytes)',
                    f"{label}'s RAM Usage (bytes)",
                ))
                f.write('\n' + footer + '\n')

            saved.extend([cpu_path, ram_path])
        return saved

    def _pidof(self, process_name: str) -> list:
        """Return PIDs for process_name using the pidof command."""
        try:
            result = subprocess.run(
                ['pidof', process_name],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            print("pidof command not found")
            return []

        if result.returncode != 0 or not result.stdout.strip():
            return []

        return [int(pid) for pid in result.stdout.strip().split()]

    def _attach_process_names(self) -> list:
        """Process names to look up with pidof when attaching."""
        if self.attach_names:
            return list(self.attach_names)
        return [self.executable or self.name]

    def _wait_for_pids(self) -> dict:
        """Poll pidof until every attach name has a PID, or wait_timeout elapses.

        Returns a mapping of pid -> process_name for all discovered processes.
        Names that never appear are omitted (a warning is printed).
        """
        names = self._attach_process_names()
        deadline = time.time() + self.wait_timeout
        found = {name: self._pidof(name) for name in names}

        while (not all(found[name] for name in names)) and time.time() < deadline:
            missing = [name for name in names if not found[name]]
            remaining = max(0.0, deadline - time.time())
            print(
                f"Waiting for process(es) {missing} "
                f"(timeout in {remaining:.1f}s)..."
            )
            time.sleep(min(self.wait_timestep, remaining) if remaining > 0 else 0)
            found = {name: self._pidof(name) for name in names}

        pid_to_name = {}
        for name in names:
            pids = found.get(name) or []
            if not pids:
                print(
                    f"No process named '{name}' found "
                    f"within {self.wait_timeout}s"
                )
                continue
            print(f"Found PID(s) for '{name}': {pids}")
            for pid in pids:
                pid_to_name[pid] = name

        return pid_to_name

    def _sample_once(self, process: psutil.Process, data: BencherData, cpu_count: int):
        data.sample_timestamp.append(time.time() - self.init_time)

        # CPU metrics
        data.cpu_pct.append(process.cpu_percent() / cpu_count)
        data.num_threads.append(process.num_threads())

        # Memory Metrics
        data.mem_info.append(process.memory_info().data)

        # IO metrics
        try:
            io_counters = process.io_counters()
            data.read_count.append(io_counters.read_count)
            data.read_bytes.append(io_counters.read_bytes)
            data.write_count.append(io_counters.write_count)
            data.write_bytes.append(io_counters.write_bytes)
            print(f'io_counters:{io_counters}')
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            self.process_died = True
            print("Access Denied")
            data.read_count.append(0)
            data.read_bytes.append(0)
            data.write_count.append(0)
            data.write_bytes.append(0)

        if self.callback is not None:
            self.data = data
            self.callback(self)

    def _sample_processes(self, processes: dict, pid_names: dict = None, kill_on_done: bool = False):
        """Sample one or more processes until sample_total is reached.

        processes: mapping of pid -> psutil.Process
        pid_names: optional mapping of pid -> process_name (for multi-name attach)
        All processes are sampled in the same timestep loop (concurrent/alternating).
        """
        if pid_names is None:
            pid_names = {}

        cpu_count = psutil.cpu_count()
        datas = {}
        for pid in processes:
            data = BencherData()
            data.pid = pid
            data.process_name = pid_names.get(pid)
            datas[pid] = data

        self.sample_current = 0
        self.init_time = time.time()
        alive = dict(processes)

        while alive and self.sample_current < self.sample_total:
            dead_pids = []
            for pid, process in alive.items():
                try:
                    if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                        dead_pids.append(pid)
                        continue
                    self._sample_once(process, datas[pid], cpu_count)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.process_died = True
                    dead_pids.append(pid)

            for pid in dead_pids:
                alive.pop(pid, None)

            self.sample_current += 1

            if self.sample_current >= self.sample_total:
                if kill_on_done:
                    for process in alive.values():
                        try:
                            process.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                break

            if alive:
                time.sleep(self.sample_time)

        for data in datas.values():
            data.process_died = self.process_died
            self.data_history.append(data)

        # Keep self.data pointing at the last sampled set for callbacks/compat.
        if datas:
            self.data = list(datas.values())[-1]

    def run(self):
        self.sample_current = 0
        self.done = False
        self.process_died = False

        try:
            if self.attach:
                pid_to_name = self._wait_for_pids()
                if not pid_to_name:
                    return

                processes = {}
                for pid in pid_to_name:
                    try:
                        processes[pid] = psutil.Process(pid)
                    except psutil.NoSuchProcess:
                        print(f"PID {pid} disappeared before sampling started")

                if not processes:
                    return

                # Never kill an already-running process we attached to.
                self._sample_processes(
                    processes,
                    pid_names=pid_to_name,
                    kill_on_done=False,
                )
            else:
                self.po = subprocess.Popen(self.args, -1, self.executable)
                process = psutil.Process(self.po.pid)
                self._sample_processes({self.po.pid: process}, kill_on_done=True)
        except KeyboardInterrupt:
            if not self.attach and hasattr(self, 'po'):
                try:
                    self.po.kill()
                except Exception:
                    pass
            raise
        except psutil.AccessDenied:
            self.process_died = True
            print("Access Denied")
        finally:
            self.done = True
