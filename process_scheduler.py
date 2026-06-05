import random
from process import State, Process

class ProcessScheduler:
    def __init__(self):
        self.ready_queue = []         
        self.blocked_set = set()      
        self.running_process = None   

    def add_to_ready(self, process):
        process.state = State.READY
        self.ready_queue.append(process)

    def tick(self, current_time):
        #  Advance Blocked/IO Processes
        ready_from_io = []
        for p in self.blocked_set:
            if p.tick(current_time) == "READY_FROM_IO":
                ready_from_io.append(p)
                
        for p in ready_from_io:
            self.blocked_set.remove(p)
            self.add_to_ready(p)

        # Update Wait Times for Ready Queue
        for p in self.ready_queue:
            p.tick(current_time)

        # Handle Running CPU Process State
        if self.running_process:
            status = self.running_process.tick(current_time)
            
            if status == "TERMINATED":
                self.running_process = None
            else:
                # Dynamic Intermittent I/O Yielding Strategy
                # If a running process has remaining I/O burst and hasn't done it yet, 
                # there's a 15% mid-execution probability it yields to perform I/O.
                if (not self.running_process.has_yielded_io and 
                        self.running_process.total_io_burst > 0 and 
                        random.random() < 0.15):
                    self.force_io_yield()

        # 4. Dispatching & Scheduling Rules (FCFS)
        if self.running_process is None and self.ready_queue:
            # FCFS always pulls the oldest process from the front of the queue
            self.running_process = self.ready_queue.pop(0)
            self.running_process.state = State.RUNNING

    def force_io_yield(self):
        """Forces the current running process to step off CPU into an active I/O state."""
        if self.running_process:
            self.running_process.state = State.BLOCKED
            self.running_process.has_yielded_io = True
            self.blocked_set.add(self.running_process)
            self.running_process = None