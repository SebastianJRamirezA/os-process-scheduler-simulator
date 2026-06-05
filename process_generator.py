import math
import random
from process import Process

class ProcessGenerator:
    def __init__(self, process_count, mean_arrival, mean_burst, mean_io):
        self.process_count = process_count
        self.mean_arrival = mean_arrival
        self.mean_burst = mean_burst
        self.mean_io = mean_io

    def generate_workload(self):
        """Generates a static production batch using an exponential distribution."""
        processes = []
        timeline_pointer = 0
        
        for i in range(self.process_count):
            # Advance timeline by a stochastic arrival interval
            timeline_pointer += math.ceil(random.expovariate(1.0 / self.mean_arrival))
            
            # Ensure burst values are valid minimums
            burst = max(1, math.ceil(random.expovariate(1.0 / self.mean_burst)))
            
            # 10% chance a process does not require I/O operations
            if random.random() < 0.10:
                io_burst = 0
            else:
                io_burst = max(1, math.ceil(random.expovariate(1.0 / self.mean_io)))
                
            priority = random.randint(1, 5)
            pid = f"P{i+1}"
            
            p = Process(
                pid=pid,
                arrival_time=timeline_pointer,
                burst_time=burst,
                io_burst_time=io_burst,
                priority=priority
            )
            processes.append(p)
            
        return processes