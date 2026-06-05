from enum import Enum

class State(Enum):
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    TERMINATED = 4

class Process:
    def __init__(self, pid, burst_time, io_burst_time, priority=0, arrival_time=0):
        self.pid = pid
        self.arrival_time = arrival_time
        
        # CPU Burst tracking
        self.total_burst = burst_time
        self.remaining_time = burst_time
        
        # I/O Burst tracking
        self.total_io_burst = io_burst_time
        self.remaining_io_time = io_burst_time
        self.has_yielded_io = False  # Track if process has initiated its I/O burst
        
        # General configurations
        self.priority = priority  # Lower integers = Higher priority
        self.state = State.READY
        
        # Analytical tracking metrics
        self.wait_time = 0
        self.blocked_time = 0
        self.completion_time = 0
        self.turnaround_time = 0

    def tick(self, current_time):
        """Advances process state by one clock cycle."""
        if self.state == State.RUNNING:
            self.remaining_time -= 1
            if self.remaining_time <= 0:
                self.state = State.TERMINATED
                self.completion_time = current_time + 1
                self.turnaround_time = self.completion_time - self.arrival_time
                return "TERMINATED"
                
        elif self.state == State.BLOCKED:
            if self.remaining_io_time > 0:
                self.remaining_io_time -= 1
                self.blocked_time += 1
                if self.remaining_io_time <= 0:
                    self.state = State.READY
                    return "READY_FROM_IO"
            else:
                # Fallback if somehow blocked with no I/O remaining
                self.state = State.READY
                return "READY_FROM_IO"
                
        elif self.state == State.READY:
            self.wait_time += 1
            
        return "NO_CHANGE"

    def copy(self):
        """Returns a fresh, unexecuted copy of the process for benchmarking."""
        return Process(
            pid=self.pid,
            arrival_time=self.arrival_time,
            burst_time=self.total_burst,
            io_burst_time=self.total_io_burst,
            priority=self.priority
        )