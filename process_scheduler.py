import random
from process import State, Process

class ProcessScheduler:
    def __init__(self, policy="FCFS", quantum=2):
        self.policy = policy          
        self.quantum = quantum        
        self.ready_queue = []         
        self.blocked_set = set()      
        self.running_process = None   
        self.quantum_left = quantum   

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
                # Ensure the object reflects termination before dropping its pointer
                self.running_process.state = State.TERMINATED 
                self.running_process = None
                self.quantum_left = self.quantum
            else:
                # Dynamic Intermittent I/O Yielding Strategy
                # If a running process has remaining I/O burst and hasn't done it yet, 
                # there's a 15% mid-execution probability it yields to perform I/O.
                if (not self.running_process.has_yielded_io and 
                        self.running_process.total_io_burst > 0 and 
                        random.random() < 0.15):
                    self.force_io_yield()
                
                # Check Round Robin Quantum Expirations
                elif self.policy == "Round Robin":
                    self.quantum_left -= 1
                    if self.quantum_left <= 0:
                        self.running_process.state = State.READY
                        self.ready_queue.append(self.running_process)
                        self.running_process = None
                        self.quantum_left = self.quantum
                        
                # Preemptive Runtime Algorithm Interruptions
                elif self.policy == "SRTF (Shortest Remaining Time First)" and self.ready_queue:
                    shortest_ready = min(self.ready_queue, key=lambda x: x.remaining_time)
                    if shortest_ready.remaining_time < self.running_process.remaining_time:
                        self.preempt_current_running()
                        
                elif self.policy == "Preemptive Priority" and self.ready_queue:
                    highest_prio_ready = min(self.ready_queue, key=lambda x: x.priority)
                    if highest_prio_ready.priority < self.running_process.priority:
                        self.preempt_current_running()

        # Dispatching & Scheduling Rules
        if self.running_process is None and self.ready_queue:
            if self.policy in ["FCFS", "Round Robin"]:
                self.running_process = self.ready_queue.pop(0)
                
            elif self.policy == "SJF (Shortest Job First)":
                self.ready_queue.sort(key=lambda x: x.remaining_time)
                self.running_process = self.ready_queue.pop(0)
                
            elif self.policy == "SRTF (Shortest Remaining Time First)":
                self.ready_queue.sort(key=lambda x: x.remaining_time)
                self.running_process = self.ready_queue.pop(0)
                
            elif self.policy in ["Non-Preemptive Priority", "Preemptive Priority"]:
                self.ready_queue.sort(key=lambda x: x.priority)
                self.running_process = self.ready_queue.pop(0)
                
            elif self.policy == "Random Selection":
                idx = random.randint(0, len(self.ready_queue) - 1)
                self.running_process = self.ready_queue.pop(idx)

            if self.running_process:
                self.running_process.state = State.RUNNING
                self.quantum_left = self.quantum

    def force_io_yield(self):
        """Forces the current running process to step off CPU into an active I/O state."""
        if self.running_process:
            self.running_process.state = State.BLOCKED
            self.running_process.has_yielded_io = True
            self.blocked_set.add(self.running_process)
            self.running_process = None
            self.quantum_left = self.quantum

    def preempt_current_running(self):
        """Saves current process context back to ready queue for later dispatch."""
        if self.running_process:
            self.running_process.state = State.READY
            self.ready_queue.append(self.running_process)
            self.running_process = None
            self.quantum_left = self.quantum