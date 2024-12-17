import psutil
import subprocess
import time
import pandas


class BencherConfig:
    def __init__(self):
        self.name = ""
        self.executable = ""
        self.args = list([])
        self.callback = None
        self.sample_time = 1
        self.sample_total = 100

class BencherData:
    def __init__(self):
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
        self.sample_current = 0
        
    def run(self):
        
        # Data
        self.data = BencherData()
        
        # Config
        self.sample_current = 0
        
        # Status
        self.done = False
        
        # Run Loop
        try:
            if not self.done:
                self.init_time = time.time()
                self.po = subprocess.Popen(self.args, -1, self.executable)
                self.p = psutil.Process(self.po.pid)
                cpu_count = psutil.cpu_count()
                
                while self.p.is_running() and not self.done:
                    self.data.sample_timestamp.append(time.time() - self.init_time)
                    
                    # CPU metrics
                    self.data.cpu_pct.append(self.p.cpu_percent()/cpu_count)
                    self.data.num_threads.append(self.p.num_threads())
                    
                    # Memory Metrics
                    self.data.mem_info.append(self.p.memory_info().data)
                    
                    # IO metrics
                    try:
                        io_counters = self.p.io_counters() # read count | write count | read bytes | write bytes
                        print(f'io_counters:{io_counters}')
                    except psutil.AccessDenied as e:
                        self.process_died = True
                        print("Access Denied")
                        self.data.read_count.append(0)
                        self.data.read_bytes.append(0)
                        self.data.write_count.append(0)
                        self.data.write_bytes.append(0)
                    finally:
                        self.data.read_count.append(io_counters.read_count)
                        self.data.read_bytes.append(io_counters.read_bytes)
                        self.data.write_count.append(io_counters.write_count)
                        self.data.write_bytes.append(io_counters.write_bytes)
                    
                    if self.callback is not None:
                        self.callback(self)
                    
                    self.sample_current = self.sample_current + 1
                    
                    if self.sample_current == self.sample_total:
                        self.p.kill()
                        break
                    
                    time.sleep(self.sample_time)
                
            else:
                print(f"The bencher for '{self.executable}' with {self.args} is done already. Doing nothing.")
        except KeyboardInterrupt as e:
            self.p.kill()
            raise KeyboardInterrupt()
        except psutil.AccessDenied as e:
            self.process_died = True
            print("Access Denied")
        finally:
            self.data.process_died = self.process_died
            self.data_history.append(self.data)
            self.done = True