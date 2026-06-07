import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from process_generator import ProcessGenerator
from process import Process, State
from process_scheduler import ProcessScheduler

class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Production-Grade Multi-Policy CPU Scheduler Simulator")
        self.root.geometry("1200x750")
        self.root.minsize(1050, 650)
        
        # Runtime Data Allocations
        self.backup_processes = []
        self.pending_processes = []
        self.scheduler = ProcessScheduler()
        self.tick_counter = 0
        self.cpu_active_ticks = 0
        self.simulation_running = False
        
        # Telemetry History Arrays for Plotting
        self.history_ticks = []
        self.history_ready = []
        self.history_running = []
        self.history_blocked = []
        
        self.build_ui_layout()
        
    def build_ui_layout(self):
        # -------------------------------------------
        # TOP FRAME: SIMULATION SYSTEM CONFIGURATION
        # -------------------------------------------
        config_frame = ttk.LabelFrame(self.root, text=" System Infrastructure Configurations ", padding=10)
        config_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Configure columns for clean alignment
        for c in range(8):
            config_frame.columnconfigure(c, weight=1)
            
        # Column 1: Scheduling Policy Selection & Simulation Latency Configuration
        ttk.Label(config_frame, text="Algorithm:").grid(row=0, column=0, sticky="e", padx=2)
        self.policy_selector = ttk.Combobox(config_frame, state="readonly", values=[
            "FCFS", 
            "SJF (Shortest Job First)", 
            "SRTF (Shortest Remaining Time First)", 
            "Non-Preemptive Priority", 
            "Preemptive Priority", 
            "Round Robin", 
            "Random Selection"
        ], width=35)
        self.policy_selector.set("FCFS")
        self.policy_selector.grid(row=0, column=1, sticky="w", padx=2)
        
        # Column 2: Quantum Configuration and Workload Generation Parameters
        ttk.Label(config_frame, text="Quantum (Ticks):").grid(row=0, column=2, sticky="e", padx=2)
        self.quantum_entry = ttk.Entry(config_frame, width=5)
        self.quantum_entry.insert(0, "3")
        self.quantum_entry.grid(row=0, column=3, sticky="w", padx=2)
        
        ttk.Label(config_frame, text="Workloads:").grid(row=1, column=2, sticky="e", padx=2)
        self.count_entry = ttk.Entry(config_frame, width=5)
        self.count_entry.insert(0, "10")
        self.count_entry.grid(row=1, column=3, sticky="w", padx=2)
        
        # Column 3: Process Generation Parameters (Arrival, CPU Burst, I/O Burst)
        ttk.Label(config_frame, text="Mean Arrival:").grid(row=2, column=4, sticky="e", padx=2)
        self.arrival_entry = ttk.Entry(config_frame, width=5)
        self.arrival_entry.insert(0, "4")
        self.arrival_entry.grid(row=2, column=5, sticky="w", padx=2)
        
        ttk.Label(config_frame, text="Mean CPU Burst:").grid(row=1, column=4, sticky="e", padx=2, pady=5)
        self.burst_entry = ttk.Entry(config_frame, width=5)
        self.burst_entry.insert(0, "6")
        self.burst_entry.grid(row=1, column=5, sticky="w", padx=2, pady=5)
        
        ttk.Label(config_frame, text="Mean I/O Burst:").grid(row=0, column=4, sticky="e", padx=2, pady=5)
        self.io_entry = ttk.Entry(config_frame, width=5)
        self.io_entry.insert(0, "3")
        self.io_entry.grid(row=0, column=5, sticky="w", padx=2, pady=5)
        
        ttk.Label(config_frame, text="Latency (ms):").grid(row=1, column=0, sticky="e", padx=2, pady=5)
        self.speed_scale = ttk.Scale(config_frame, from_=25, to=1000, value=250)
        self.speed_scale.grid(row=1, column=1, columnspan=1, sticky="ew", padx=5, pady=5)
        
        # Interactive Operation Buttons
        btn_container = ttk.Frame(config_frame)
        btn_container.grid(row=3, column=0, columnspan=8, pady=5)
        
        self.btn_generate = ttk.Button(btn_container, text="Generate Workload", command=self.action_generate_workload)
        self.btn_generate.pack(side=tk.LEFT, padx=10)
        
        self.btn_start = ttk.Button(btn_container, text="Start Simulation", command=self.action_start_simulation, state="disabled")
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = ttk.Button(btn_container, text="Stop / Reset", command=self.action_stop_simulation, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        # -------------------------------------------
        # MIDDLE FRAME: SPLIT VIEW (PLOT & QUEUES)
        # -------------------------------------------
        split_view = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        split_view.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left Side View: Matplotlib Live Trend Graph
        self.graph_container = ttk.LabelFrame(split_view, text=" Live Process Allocation Metric Matrix ")
        split_view.add(self.graph_container, weight=3)
        
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Live Process Allocation Matrix")
        self.ax.set_xlabel("Ticks")
        self.ax.set_ylabel("Process Volume")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right Side View: Side-by-Side Real-Time Discrete Queue Lists
        queue_container = ttk.LabelFrame(split_view, text=" System Discrete Micro Queues ", padding=5)
        split_view.add(queue_container, weight=2)
        
        queue_grid = ttk.Frame(queue_container)
        queue_grid.pack(fill=tk.BOTH, expand=True)
        for c in range(4):
            queue_grid.columnconfigure(c, weight=1)
        queue_grid.rowconfigure(1, weight=1)
        
        # Change the original local variables to class instance variables (self.)
        self.lbl_ready_hdr = ttk.Label(queue_grid, text="READY QUEUE (0)", font=("Arial", 9, "bold"))
        self.lbl_ready_hdr.grid(row=0, column=0, pady=2)
        self.listbox_ready = tk.Listbox(queue_grid, bg="#fffde7", font=("Courier", 9))
        self.listbox_ready.grid(row=1, column=0, sticky="nsew", padx=2)
        
        self.lbl_cpu_hdr = ttk.Label(queue_grid, text="RUNNING CPU (0)", font=("Arial", 9, "bold"), foreground="green")
        self.lbl_cpu_hdr.grid(row=0, column=1, pady=2)
        self.listbox_cpu = tk.Listbox(queue_grid, bg="#e8f5e9", font=("Courier", 10, "bold"))
        self.listbox_cpu.grid(row=1, column=1, sticky="nsew", padx=2)
        
        self.lbl_blocked_hdr = ttk.Label(queue_grid, text="BLOCKED (I/O) (0)", font=("Arial", 9, "bold"), foreground="red")
        self.lbl_blocked_hdr.grid(row=0, column=2, pady=2)
        self.listbox_blocked = tk.Listbox(queue_grid, bg="#ffebee", font=("Courier", 9))
        self.listbox_blocked.grid(row=1, column=2, sticky="nsew", padx=2)
        
        self.lbl_terminated_hdr = ttk.Label(queue_grid, text="TERMINATED (0)", font=("Arial", 9, "bold"), foreground="gray")
        self.lbl_terminated_hdr.grid(row=0, column=3, pady=2)
        self.listbox_terminated = tk.Listbox(queue_grid, bg="#eceff1", font=("Courier", 9))
        self.listbox_terminated.grid(row=1, column=3, sticky="nsew", padx=2)

        # -------------------------------------------
        # BOTTOM FRAME: DIAGNOSTICS & METRICS readouts
        # -------------------------------------------
        bottom_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        bottom_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Diagnostic Table Treeview Display Grid
        table_frame = ttk.LabelFrame(bottom_panel, text=" Global Workload Ledger ")
        bottom_panel.add(table_frame, weight=3)
        
        cols = ("PID", "Arrival", "CPU Burst", "I/O Burst", "Priority", "State", "Wait Time", "Blk Time")
        self.tree_ledger = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree_ledger.heading(col, text=col)
            self.tree_ledger.column(col, width=75, anchor="center")
            
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_ledger.yview)
        self.tree_ledger.configure(yscrollcommand=scrollbar.set)
        
        self.tree_ledger.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Live Performance Telemetry Summary Cards
        self.metrics_frame = ttk.LabelFrame(bottom_panel, text=" Live Performance Telemetry Summary ", padding=10)
        bottom_panel.add(self.metrics_frame, weight=1)
        
        self.lbl_curr_tick = ttk.Label(self.metrics_frame, text="Current Tick: 0", font=("Arial", 10, "bold"))
        self.lbl_curr_tick.pack(anchor="w", pady=1)
        self.lbl_cpu_util = ttk.Label(self.metrics_frame, text="CPU Utilization: 0.0%", font=("Arial", 10))
        self.lbl_cpu_util.pack(anchor="w", pady=1)
        self.lbl_avg_wait = ttk.Label(self.metrics_frame, text="Avg Waiting Time: 0.0 ticks", font=("Arial", 10))
        self.lbl_avg_wait.pack(anchor="w", pady=1)
        self.lbl_avg_blk  = ttk.Label(self.metrics_frame, text="Avg Blocked Time: 0.0 ticks", font=("Arial", 10))
        self.lbl_avg_blk.pack(anchor="w", pady=1)
        self.lbl_avg_turn = ttk.Label(self.metrics_frame, text="Avg Turnaround Time: 0.0 ticks", font=("Arial", 10))
        self.lbl_avg_turn.pack(anchor="w", pady=1)

    # -------------------------------------------
    # RUNTIME USER EVENT ACTION HANDLERS
    # -------------------------------------------
    def action_generate_workload(self):
        try:
            count = int(self.count_entry.get())
            m_arr = float(self.arrival_entry.get())
            m_brst = float(self.burst_entry.get())
            m_io = float(self.io_entry.get())
        except ValueError:
            messagebox.showerror("Configuration Error", "Please input valid numerical simulation values.")
            return

        generator = ProcessGenerator(count, m_arr, m_brst, m_io)
        self.backup_processes = generator.generate_workload()
        
        # Display the freshly generated workload in the ledger grid
        self.refresh_ledger_ui(self.backup_processes)
        self.btn_start.config(state="normal")

    def action_start_simulation(self):
        if not self.backup_processes:
            return
            
        try:
            chosen_policy = self.policy_selector.get()
            chosen_quantum = int(self.quantum_entry.get())
        except ValueError:
            messagebox.showerror("Configuration Error", "Invalid quantum entry configuration detected.")
            return

        # Restore structural conditions from identical benchmark backup configuration
        self.pending_processes = [p.copy() for p in self.backup_processes]
        self.scheduler = ProcessScheduler(policy=chosen_policy, quantum=chosen_quantum)
        
        # Reset infrastructure variables
        self.tick_counter = 0
        self.cpu_active_ticks = 0
        self.history_ticks.clear()
        self.history_ready.clear()
        self.history_running.clear()
        self.history_blocked.clear()
        
        # Toggle state switches
        self.simulation_running = True
        self.btn_generate.config(state="disabled")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.policy_selector.config(state="disabled")
        
        # Enter the event execution loop
        self.execute_simulation_clock_cycle()

    def action_stop_simulation(self):
        self.simulation_running = False
        self.btn_generate.config(state="normal")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.policy_selector.config(state="readonly")
        self.refresh_ledger_ui(self.backup_processes)
        
        # Reset column headers to default state
        self.lbl_ready_hdr.config(text="READY QUEUE (0)")
        self.lbl_cpu_hdr.config(text="RUNNING CPU (0)")
        self.lbl_blocked_hdr.config(text="BLOCKED (I/O) (0)")
        self.lbl_terminated_hdr.config(text="TERMINATED (0)")

    # -------------------------------------------
    # MAIN SIMULATION ENGINE CLOCK LOOP
    # -------------------------------------------
    def execute_simulation_clock_cycle(self):
        if not self.simulation_running:
            return

        # 1. Pipeline newly arriving processes based on the clock timeline index
        arriving = [p for p in self.pending_processes if p.arrival_time == self.tick_counter]
        for p in arriving:
            self.scheduler.add_to_ready(p)
            self.pending_processes.remove(p)

        # 2. Advance Scheduler Clock Step Logic
        if self.scheduler.running_process:
            self.cpu_active_ticks += 1
            
        self.scheduler.tick(self.tick_counter)

        # 3. Cache Telemetry History Metrics
        self.history_ticks.append(self.tick_counter)
        self.history_ready.append(len(self.scheduler.ready_queue))
        self.history_running.append(1 if self.scheduler.running_process else 0)
        self.history_blocked.append(len(self.scheduler.blocked_set))

        # Constrain sliding timeline grid context to maximum 40 historical tracking slots
        if len(self.history_ticks) > 40:
            self.history_ticks.pop(0)
            self.history_ready.pop(0)
            self.history_running.pop(0)
            self.history_blocked.pop(0)

        # 4. Synchronize Graphical UI Components
        self.update_live_plot_canvas()
        self.update_discrete_queue_lists()
        
        # Gather all current process records to refresh runtime dashboards
        all_runtime_instances = []
        if self.scheduler.running_process:
            all_runtime_instances.append(self.scheduler.running_process)
        all_runtime_instances.extend(self.pending_processes)
        all_runtime_instances.extend(self.scheduler.ready_queue)
        all_runtime_instances.extend(self.scheduler.blocked_set)
        all_runtime_instances.extend(list(self.scheduler.blocked_set)) 
        
        # Remove duplicates when assembling the full list
        unique_instances = {p.pid: p for p in all_runtime_instances}
        all_current_processes = list(unique_instances.values()) + list(self.scheduler.blocked_set)
        
        # Filter duplicates again to be completely safe
        ledger_map = {}
        for p in all_current_processes:
            ledger_map[p.pid] = p
            
        final_ledger_list = list(ledger_map.values())
        final_ledger_list.sort(key=lambda x: int(x.pid.replace("P", "")))
        
        self.refresh_ledger_ui(final_ledger_list)
        self.calculate_and_render_telemetry(final_ledger_list)

        # 5. Continuous System Termination State Validation
        if (not self.pending_processes and 
                not self.scheduler.ready_queue and 
                not self.scheduler.blocked_set and 
                not self.scheduler.running_process):
            self.simulation_running = False
            self.btn_generate.config(state="normal")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.policy_selector.config(state="readonly")
            return

        # 6. Dispatch next clock step interval delay invocation
        self.tick_counter += 1
        try:
            delay = int(self.speed_scale.get())
        except ValueError:
            delay = 250
            
        self.root.after(delay, self.execute_simulation_clock_cycle)

    # -------------------------------------------
    # REFRESH AND RENDER UI WRITING HANDLERS
    # -------------------------------------------
    def update_live_plot_canvas(self):
        self.ax.clear()
        self.ax.step(self.history_ticks, self.history_ready, label="Ready Queue", where="post", color="#ffc107", alpha=0.85)
        self.ax.step(self.history_ticks, self.history_running, label="Running (CPU)", where="post", color="#28a745", linewidth=2)
        self.ax.step(self.history_ticks, self.history_blocked, label="Blocked (I/O)", where="post", color="#dc3545", alpha=0.85)

        self.ax.set_title("Live Process Allocation Matrix", fontsize=10, fontweight="bold")
        self.ax.set_xlabel("Ticks", fontsize=8)
        self.ax.set_ylabel("Process Volume", fontsize=8)
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.legend(loc="upper left", prop={'size': 7})
        
        if self.history_ticks:
            self.ax.set_xlim(min(self.history_ticks), max(self.history_ticks) + 1)
            max_y = max(self.history_ready + self.history_running + self.history_blocked, default=4)
            self.ax.set_ylim(-0.2, max_y + 1.2)

        self.canvas.draw()

    def update_discrete_queue_lists(self):
        self.listbox_ready.delete(0, tk.END)
        self.listbox_cpu.delete(0, tk.END)
        self.listbox_blocked.delete(0, tk.END)
        self.listbox_terminated.delete(0, tk.END)

        # 1. Populate Ready Queue & Track Count
        for p in self.scheduler.ready_queue:
            self.listbox_ready.insert(tk.END, f" {p.pid} [R:{p.remaining_time}]")
        self.lbl_ready_hdr.config(text=f"READY QUEUE ({len(self.scheduler.ready_queue)})")

        # 2. Populate Running CPU & Track Count (0 or 1)
        if self.scheduler.running_process:
            p = self.scheduler.running_process
            rr_info = f" Q:{self.scheduler.quantum_left}" if self.scheduler.policy == "Round Robin" else ""
            self.listbox_cpu.insert(tk.END, f" {p.pid} ({p.remaining_time}t){rr_info}")
            self.lbl_cpu_hdr.config(text="RUNNING CPU (1)")
        else:
            self.listbox_cpu.insert(tk.END, " [IDLE CPU]")
            self.lbl_cpu_hdr.config(text="RUNNING CPU (0)")

        # 3. Populate Blocked Set & Track Count
        for p in self.scheduler.blocked_set:
            self.listbox_blocked.insert(tk.END, f" {p.pid} [IO:{p.remaining_io_time}]")
        self.lbl_blocked_hdr.config(text=f"BLOCKED (I/O) ({len(self.scheduler.blocked_set)})")

        # 4. Extract, Populate, and Count Terminated Processes
        terminated_count = 0
        all_known = sorted(self.backup_processes, key=lambda x: int(x.pid.replace("P", "")))
        for bp in all_known:
            is_active = False
            for ap in (self.pending_processes + self.scheduler.ready_queue + list(self.scheduler.blocked_set)):
                if ap.pid == bp.pid:
                    is_active = True
                    break
            if self.scheduler.running_process and self.scheduler.running_process.pid == bp.pid:
                is_active = True
                
            if not is_active and len(self.pending_processes) == 0 and self.tick_counter > bp.arrival_time:
                self.listbox_terminated.insert(tk.END, f" {bp.pid} ✔")
                terminated_count += 1
                
        self.lbl_terminated_hdr.config(text=f"TERMINATED ({terminated_count})")

    def refresh_ledger_ui(self, process_list):
        # Clear out current ledger records cleanly
        for item in self.tree_ledger.get_children():
            self.tree_ledger.delete(item)
            
        for p in process_list:
            state_str = p.state.name if isinstance(p.state, State) else str(p.state)
            
            # Context state overrides for elements currently rendered inside global historical frames
            if not self.simulation_running:
                state_str = "READY"
                rem_cpu, rem_io = p.total_burst, p.total_io_burst
            else:
                rem_cpu, rem_io = p.remaining_time, p.remaining_io_time
                # Detect terminated records that are no longer active in core queues
                is_active = (p in self.pending_processes or 
                             p in self.scheduler.ready_queue or 
                             p in self.scheduler.blocked_set or 
                             p == self.scheduler.running_process)
                if not is_active:
                    state_str = "TERMINATED"
                    rem_cpu, rem_io = 0, 0

            self.tree_ledger.insert("", "end", values=(
                p.pid,
                p.arrival_time,
                f"{rem_cpu}/{p.total_burst}",
                f"{rem_io}/{p.total_io_burst}",
                p.priority,
                state_str,
                p.wait_time,
                p.blocked_time
            ))

    def calculate_and_render_telemetry(self, process_list):
        self.lbl_curr_tick.config(text=f"Current Tick: {self.tick_counter}")
        
        util = (self.cpu_active_ticks / self.tick_counter * 100) if self.tick_counter > 0 else 0.0
        self.lbl_cpu_util.config(text=f"CPU Utilization: {util:.1f}%")
        
        if process_list:
            avg_wait = sum(p.wait_time for p in process_list) / len(process_list)
            avg_blk  = sum(p.blocked_time for p in process_list) / len(process_list)
            
            # Extract items to calculate completed turnaround records safely
            completed = [p for p in process_list if p.turnaround_time > 0]
            avg_turn  = sum(p.turnaround_time for p in completed) / len(completed) if completed else 0.0
            
            self.lbl_avg_wait.config(text=f"Avg Waiting Time: {avg_wait:.1f} ticks")
            self.lbl_avg_blk.config(text=f"Avg Blocked Time: {avg_blk:.1f} ticks")
            self.lbl_avg_turn.config(text=f"Avg Turnaround: {avg_turn:.1f} ticks")
