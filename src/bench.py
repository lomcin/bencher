from bencher import Bencher, BencherConfig
import matplotlib.pyplot as plt
import numpy as np
import os, sys

def callback(b: Bencher):
    # print(f"b.cpu_pct: {b.cpu_pct[-1]} % | b.mem_info: {b.mem_info[-1]} | b.read_bytes:{b.read_bytes[-1]}")
    pass
    

def main():
    
    # Creating BencherConfig structure
    cfg = BencherConfig()
    
    # Setting up BencherConfig attributes
    # cfg.name = "Firefox"
    # cfg.executable = "firefox"
    cfg.name = "gedit"
    cfg.executable = "gedit"
    cfg.args = [""]
    cfg.callback = callback
    cfg.sample_time = 1
    cfg.sample_total = 3
    
    # Repeat the evaluaton for n times
    repeat_n_times = 3
    
    # Creating Bencher
    b = Bencher()
    
    # Setting up Bencher
    b.set(cfg)
    
    # Running Bencher
    for i in range(repeat_n_times):
        b.run()
    
    # Save data
    os.makedirs(f'results/{b.name}/', exist_ok=True)
    for i in range(repeat_n_times):
        df = b.data_history[i].to_data_frame()
        df.to_csv(f'results/{b.name}/{i}.csv')
    
    for i in range(repeat_n_times):
        plt.plot(b.data_history[i].sample_timestamp, b.data_history[i].cpu_pct)
    plt.title(f"{b.name}'s CPU Usage (%)")
    plt.ylabel("CPU Usage (%)")
    plt.xlabel("Sample timestamp (s)")
    plt.show()
    
    for i in range(repeat_n_times):
        plt.plot(b.data_history[i].sample_timestamp, [x for x in b.data_history[i].mem_info])
    plt.title(f"{b.name}'s RAM Usage (bytes)")
    plt.ylabel("RAM Usage (bytes)")
    plt.xlabel("Sample timestamp (s)")
    plt.show()
    
if __name__ == "__main__":
    main()