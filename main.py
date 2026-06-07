import math
import random
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from process import Process, State
from process_generator import ProcessGenerator
from process_scheduler import ProcessScheduler 

# ==========================================
# 2. GLOBAL SIMULATION STATE
# ==========================================

pending_processes = []  # Processes waiting for their arrival time
scheduler = None        # Will hold our ProcessScheduler instance

tick_counter = 0
simulation_running = False

# Plot tracking history
history_ticks = []
history_running_active = []   # Tracks if a process is on the CPU (0 or 1)
history_ready_counts = []     # Tracks ready queue length
history_blocked_counts = []   # Tracks blocked queue length

# ==========================================
# 3. LIVE GENERATION & EXECUTION LOOP
# ==========================================

def start_generation():
    global pending_processes, scheduler, tick_counter, simulation_running
    global history_ticks, history_running_active, history_ready_counts, history_blocked_counts

    try:
        count = int(count_entry.get())
        m_arr = float(arrival_entry.get())
        m_brst = float(burst_entry.get())
        m_io = float(io_entry.get())
        chosen_policy = policy_combobox.get()
        chosen_quantum = int(quantum_entry.get())
    except ValueError:
        return  # Safeguard for invalid inputs or blank numerical fields

    # Generate the pool of upcoming processes using generate_workload
    generator = ProcessGenerator(count, m_arr, m_brst, m_io)
    pending_processes = generator.generate_workload()
    
    # Sort pending processes by arrival time so we can check them sequentially
    pending_processes.sort(key=lambda x: x.arrival_time)
    
    # Initialize the Scheduler instance with user choices
    scheduler = ProcessScheduler(policy=chosen_policy, quantum=chosen_quantum)
    
    # Reset tracking histories
    tick_counter = 0
    history_ticks.clear()
    history_running_active.clear()
    history_ready_counts.clear()
    history_blocked_counts.clear()

    simulation_running = True
    start_button.config(state="disabled")
    run_generation_tick()


def run_generation_tick():
    global tick_counter, simulation_running, scheduler, pending_processes

    if not simulation_running:
        return

    # 1. Handle Arrivals: Check if any pending processes arrive at this exact tick
    # Copying list slicing avoids evaluation skipping while modifying in-loop
    newly_arrived = [p for p in pending_processes if p.arrival_time == tick_counter]
    for p in newly_arrived:
        scheduler.add_to_ready(p)
        pending_processes.remove(p)

    # 2. Advance the scheduler by one clock cycle
    scheduler.tick(tick_counter)

    # 3. Collect state metrics for UI updates
    running_count = 1 if scheduler.running_process else 0
    ready_count = len(scheduler.ready_queue)
    blocked_count = len(scheduler.blocked_set)

    # Update UI Text Dashboards
    tick_label.config(text=f"Current Tick: {tick_counter}")
    arrived_lbl.config(text=f"Running: {running_count} | Ready: {ready_count}")
    pending_lbl.config(text=f"Blocked (I/O): {blocked_count} | Pending: {len(pending_processes)}")

    # 4. Track historical data for the visual plot
    history_ticks.append(tick_counter)
    history_running_active.append(running_count)
    history_ready_counts.append(ready_count)
    history_blocked_counts.append(blocked_count)

    # Maintain rolling window of the last 40 ticks
    if len(history_ticks) > 40:
        history_ticks.pop(0)
        history_running_active.pop(0)
        history_ready_counts.pop(0)
        history_blocked_counts.pop(0)

    # Refresh the Matplotlib visualization
    update_plot()

    # 5. Terminal Condition: Stop when no processes remain anywhere
    if not pending_processes and not scheduler.running_process and not scheduler.ready_queue and not scheduler.blocked_set:
        simulation_running = False
        start_button.config(state="normal")
        tick_label.config(text=f"Current Tick: {tick_counter} (Finished!)")
        return

    # Schedule next execution loop step
    tick_counter += 1
    try:
        speed_ms = int(speed_scale.get())
    except ValueError:
        speed_ms = 250
        
    ventana.after(speed_ms, run_generation_tick)


def update_plot():
    ax.clear()
    
    chosen_policy = policy_combobox.get()
    
    # Plotting layout adjusted to showcase execution metrics over time
    ax.step(history_ticks, history_running_active, label="CPU Active (0/1)", where="post", color="#dc3545", linewidth=2)
    ax.step(history_ticks, history_ready_counts, label="Ready Queue Size", where="post", color="#28a745", linewidth=1.5)
    ax.step(history_ticks, history_blocked_counts, label="Blocked in I/O", where="post", color="#ffc107", linewidth=1.5, linestyle="--")

    ax.set_title(f"{chosen_policy} CPU Scheduling Real-Time Timeline")
    ax.set_xlabel("Timeline Ticks (Seconds/Cycles)")
    ax.set_ylabel("Process State Counts")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    
    if history_ticks:
        ax.set_xlim(min(history_ticks), max(history_ticks) + 1)
        max_y = max(max(history_ready_counts, default=2), max(history_blocked_counts, default=2), 1)
        ax.set_ylim(-0.2, max_y + 1.5)

    canvas.draw()

# ==========================================
# 4. UI WINDOW SETUP
# ==========================================

ventana = tk.Tk()
ventana.title("Process Scheduler Observer")
ventana.geometry("1050x600")

# Top Counter Dashboard
metrics_frame = ttk.Frame(ventana, padding=10)
metrics_frame.pack(side=tk.TOP, fill=tk.X)

tick_label = ttk.Label(metrics_frame, text="Current Tick: 0", font=("Arial", 11, "bold"))
tick_label.pack(side=tk.LEFT, padx=15)

arrived_lbl = ttk.Label(metrics_frame, text="Running: 0 | Ready: 0", foreground="#1e7e34", font=("Arial", 11, "bold"))
arrived_lbl.pack(side=tk.LEFT, padx=15)

pending_lbl = ttk.Label(metrics_frame, text="Blocked (I/O): 0 | Pending: 0", foreground="#6c757d", font=("Arial", 11, "bold"))
pending_lbl.pack(side=tk.LEFT, padx=15)

# Settings Side Panel (Right)
control_frame = ttk.LabelFrame(ventana, text=" Simulator Settings ", padding=15)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

# POLICY PICKER
ttk.Label(control_frame, text="Scheduling Algorithm:").pack(anchor="w")
policies = [
    "FCFS", 
    "Round Robin", 
    "SJF (Shortest Job First)", 
    "SRTF (Shortest Remaining Time First)", 
    "Non-Preemptive Priority", 
    "Preemptive Priority", 
    "Random Selection"
]
policy_combobox = ttk.Combobox(control_frame, values=policies, state="readonly")
policy_combobox.set("FCFS")
policy_combobox.pack(fill=tk.X, pady=(0, 10))

# ROUND ROBIN QUANTUM TIME
ttk.Label(control_frame, text="Round Robin Quantum (Ticks):").pack(anchor="w")
quantum_entry = ttk.Entry(control_frame)
quantum_entry.insert(0, "2")
quantum_entry.pack(fill=tk.X, pady=(0, 10))

# WORKLOAD PARAMETERS
ttk.Label(control_frame, text="Total Processes to Make:").pack(anchor="w")
count_entry = ttk.Entry(control_frame)
count_entry.insert(0, "15")
count_entry.pack(fill=tk.X, pady=(0, 10))

ttk.Label(control_frame, text="Mean Arrival Interval (Ticks):").pack(anchor="w")
arrival_entry = ttk.Entry(control_frame)
arrival_entry.insert(0, "4")
arrival_entry.pack(fill=tk.X, pady=(0, 10))

ttk.Label(control_frame, text="Mean CPU Burst (Ticks):").pack(anchor="w")
burst_entry = ttk.Entry(control_frame)
burst_entry.insert(0, "6")
burst_entry.pack(fill=tk.X, pady=(0, 10))

ttk.Label(control_frame, text="Mean I/O Burst (Ticks):").pack(anchor="w")
io_entry = ttk.Entry(control_frame)
io_entry.insert(0, "3")
io_entry.pack(fill=tk.X, pady=(0, 15))

# SPEED CONTROL
ttk.Label(control_frame, text="Tick Interval Speed (ms):").pack(anchor="w")
speed_scale = ttk.Scale(control_frame, from_=50, to=1000, value=250)
speed_scale.pack(fill=tk.X, pady=(0, 20))

start_button = ttk.Button(control_frame, text="🚀 Start Simulation", command=start_generation)
start_button.pack(fill=tk.X, ipady=5)

# Matplotlib Left Canvas
figura = Figure(figsize=(5, 4), dpi=100)
ax = figura.add_subplot(111)
canvas = FigureCanvasTkAgg(figura, master=ventana)
canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

ventana.mainloop()