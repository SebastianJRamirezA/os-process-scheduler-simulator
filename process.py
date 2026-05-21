from enum import Enum

class State(Enum):
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    FINISHED = 4

class Process:
    def __init__(self, pid, burst_time, io_burst_time, priority=0, arrival_time=0):
        self.pid = pid
        self.arrival_time = arrival_time

        self.priority = priority
        self.burst_time = burst_time
        self.remaining_burst_time = burst_time
        self.io_burst_time = io_burst_time
        self.remaining_io_time = io_burst_time
        
        self.state = State.READY
        
        # Simulation Metrics (Crucial for final reports)
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0

    def run(self, current_time):
        """Called when the scheduler picks this process to run."""
        self.state = State.RUNNING
        if self.start_time is None:
            self.start_time = current_time

    def block(self):
        """Called if the process yields for I/O operations."""
        self.state = State.BLOCKED

    def ready(self):
        """Called when a blocked process finishes I/O, or a running one is preempted."""
        self.state = State.READY

    def tick(self, current_time):
        """
        Simulates one unit of system time passing. 
        Handles both CPU execution and I/O countdowns.
        """
        if self.state == State.RUNNING:
            self.remaining_burst_time -= 1
            if self.remaining_burst_time <= 0:
                self.state = State.TERMINATED
                self.completion_time = current_time + 1
                return "TERMINATED"
                
        elif self.state == State.BLOCKED:
            if self.remaining_io_time > 0:
                self.remaining_io_time -= 1
                if self.remaining_io_time == 0:
                    self.state = State.READY
                    return "READY_FROM_IO"
                    
        return "NO_CHANGE"

    def __repr__(self):
        return f"[PID {self.pid} | {self.state.name} | Rem: {self.remaining_time}]"