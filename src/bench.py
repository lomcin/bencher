from bencher import Bencher, BencherConfig
import os


def callback(b: Bencher):
    # print(f"b.cpu_pct: {b.cpu_pct[-1]} % | b.mem_info: {b.mem_info[-1]} | b.read_bytes:{b.read_bytes[-1]}")
    pass


def main():

    # Creating BencherConfig structure
    cfg = BencherConfig()

    # Setting up BencherConfig attributes
    # cfg.name = "Firefox"
    # cfg.executable = "firefox"
    cfg.name = "gnome-text-editor"
    cfg.executable = "gnome-text-editor"
    cfg.args = [""]
    cfg.callback = callback
    cfg.sample_time = 0.1
    cfg.sample_total = 50

    # Attach to an already-running process (via pidof) instead of launching it.
    cfg.attach = False
    # True: results/<name>/<pid>/...  False: results/<name>/... (many pids under the name)
    cfg.save_per_pid = False
    # Wait for the process to appear when attaching.
    cfg.wait_timeout = 30.0
    cfg.wait_timestep = 0.5

    # Repeat the evaluation for n times (ignored when attach=True; all matching PIDs are sampled once)
    repeat_n_times = 3

    # Creating Bencher
    b = Bencher()

    # Setting up Bencher
    b.set(cfg)

    # Running Bencher
    if cfg.attach:
        b.run()
    else:
        for _ in range(repeat_n_times):
            b.run()

    # Save CSV data
    if b.save_per_pid:
        by_pid = {}
        for data in b.data_history:
            by_pid.setdefault(data.pid, []).append(data)

        for pid, entries in by_pid.items():
            results_dir = b.results_dir_for(entries[0])
            os.makedirs(results_dir, exist_ok=True)
            for i, data in enumerate(entries):
                df = data.to_data_frame()
                df.to_csv(f'{results_dir}{i}.csv')
    else:
        results_dir = f'results/{b.name}/'
        os.makedirs(results_dir, exist_ok=True)
        for i, data in enumerate(b.data_history):
            df = data.to_data_frame()
            # When multiple PIDs share a name, keep files distinguishable.
            if data.pid is not None and cfg.attach:
                df.to_csv(f'{results_dir}{data.pid}.csv')
            else:
                df.to_csv(f'{results_dir}{i}.csv')

    # Save plots as PNG and LaTeX (pgfplots)
    b.save_png(show=True)
    b.save_latex()


if __name__ == "__main__":
    main()
