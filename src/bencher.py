import psutil
import subprocess
import time


class BencherConfig:
    def __init__(self):
        self.name = ""
        self.executable = ""
        self.args = list([])
        self.callback = None
        self.sample_time = 1
        

class Bencher:
    
    def __init__(self):
        
        # Data
        self.cpu_pct = list()
        self.mem_info = list()
        self.num_threads = list()
        self.read_count = list()
        self.read_bytes = list()
        self.write_count = list()
        self.write_bytes = list()
        self.sample_timestamp = list()
        
        # Config
        self.name = "unnamed"
        self.executable = ""
        self.args = list([""])
        self.callback = None
        self.sample_time = 1
        
        # Status
        self.done = False
        self.init_time = 0
    
    def set(self, config: BencherConfig):
        self.name = config.name
        self.executable = config.executable
        self.args = config.args
        self.callback = config.callback
        self.sample_time = config.sample_time
    
    def reset(self):
        
        # Data
        self.cpu_pct.clear()
        self.mem_info.clear()
        self.num_threads.clear()
        self.read_count.clear()
        self.read_bytes.clear()
        self.write_count.clear()
        self.write_bytes.clear()
        self.sample_timestamp.clear()
        
        # Status
        self.done = False
        
    def run(self):
        try:
            if not self.done:
                self.init_time = time.time()
                self.po = subprocess.Popen(self.args, -1, self.executable)
                self.p = psutil.Process(self.po.pid)
                cpu_count = psutil.cpu_count()
                
                while self.p.is_running() and not self.done:
                    self.sample_timestamp.append(time.time() - self.init_time)
                    # CPU metrics
                    self.cpu_pct.append(self.p.cpu_percent()/cpu_count)
                    self.num_threads.append(self.p.num_threads())
                    
                    # Memory Metrics
                    self.mem_info.append(self.p.memory_info())
                    
                    # IO metrics
                    io_counters = self.p.io_counters() # read count | write count | read bytes | write bytes
                    self.read_count.append(io_counters.read_count)
                    self.read_bytes.append(io_counters.read_bytes)
                    self.write_count.append(io_counters.write_count)
                    self.write_bytes.append(io_counters.write_bytes)
                    
                    if self.callback is not None:
                        self.callback(self)
                    time.sleep(self.sample_time)
                
                self.done = True
            else:
                print(f"The bencher for '{self.executable}' with {self.args} is done already. Doing nothing.")
        except KeyboardInterrupt as e:
            self.p.kill()
        except psutil.AccessDenied as e:
            pass