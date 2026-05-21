import random
import math
from process import Process

class ProcessGenerator:
    def __init__(self, process_count, mean_arrival_interval=4, mean_burst_time=8, mean_io_burst_time=3):
        self.process_count = process_count
        self.mean_arrival_interval = mean_arrival_interval
        self.mean_burst_time = mean_burst_time
        self.mean_io_burst_time = mean_io_burst_time

    def generate_processes(self, processes, current_time=0):
        timeline_pointer = current_time
        pid = processes[-1].pid + 1 if processes else 0

        for i in range(self.process_count):
            timeline_pointer += self._generate_arrival_time()
            
            process = Process(
                pid=pid,
                arrival_time = timeline_pointer,
                burst_time=max(1, self._generate_burst_time()),
                io_burst_time=max(0, self._generate_io_burst_time())
            )
            processes.append(process)
            pid += 1
            
        # Sort them by arrival time just to keep scheduler queue orderly
        processes.sort(key=lambda p: p.arrival_time)
        return processes

    def _generate_arrival_time(self):
        return math.ceil(random.expovariate(1.0 / self.mean_arrival_interval))

    def _generate_burst_time(self):
        return math.ceil(random.expovariate(1.0 / self.mean_burst_time))
    
    def _generate_io_burst_time(self):
        return math.ceil(random.expovariate(1.0 / self.mean_io_burst_time))