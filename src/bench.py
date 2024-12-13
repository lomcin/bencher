from bencher import Bencher, BencherConfig
import matplotlib.pyplot as plt
import numpy as np

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
    cfg.args = []
    cfg.callback = callback
    cfg.sample_time = 1
    
    # Creating Bencher
    b = Bencher()
    
    # Setting up Bencher
    b.set(cfg)
    
    # Running Bencher
    b.run()
    
    plt.plot(b.sample_timestamp, b.cpu_pct)
    plt.title(f"{b.name}'s CPU Usage (%)")
    plt.ylabel("CPU Usage (%)")
    plt.xlabel("Sample timestamp (s)")
    plt.show()
    
    plt.plot(b.sample_timestamp, [x.data for x in b.mem_info])
    plt.title(f"{b.name}'s RAM Usage (bytes)")
    plt.ylabel("RAM Usage (bytes)")
    plt.xlabel("Sample timestamp (s)")
    plt.show()
    
if __name__ == "__main__":
    main()