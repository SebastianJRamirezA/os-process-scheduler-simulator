import math
import random
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from process import Process, State
from process_generator import ProcessGenerator

# ==========================================
# 2. GLOBAL SIMULATION STATE
# ==========================================

pending_processes = []  # Processes waiting for their arrival time
arrived_processes = []  # Processes that have successfully "spawned"

tick_counter = 0
simulation_running = False

# Plot tracking history
history_ticks = []
history_arrived_counts = []
history_pending_counts = []

# ==========================================
# 3. LIVE GENERATION LOOP
# ==========================================

def start_generation():
    global pending_processes, arrived_processes, tick_counter, simulation_running
    global history_ticks, history_arrived_counts, history_pending_counts

    try:
        count = int(count_entry.get())
        m_arr = float(arrival_entry.get())
        m_brst = float(burst_entry.get())
        m_io = float(io_entry.get())
    except ValueError:
        return  # Safeguard for invalid inputs

    # Generate the pool of upcoming processes
    generator = ProcessGenerator(count, m_arr, m_brst, m_io)
    pending_processes = generator.generate_processes(pending_processes,current_time=0)
    arrived_processes.clear()
    
    # Reset tracking
    tick_counter = 0
    history_ticks.clear()
    history_arrived_counts.clear()
    history_pending_counts.clear()

    simulation_running = True
    start_button.config(state="disabled")
    run_generation_tick()


def run_generation_tick():
    global tick_counter, simulation_running

    if not simulation_running:
        return

    # Check if any processes have arrived at the current tick
    newly_arrived = [p for p in pending_processes if p.arrival_time == tick_counter]
    
    # Move them from pending to arrived
    for p in newly_arrived:
        arrived_processes.append(p)
        pending_processes.remove(p)

    # Update the UI Labels
    tick_label.config(text=f"Current Tick: {tick_counter}")
    arrived_lbl.config(text=f"Arrived: {len(arrived_processes)}")
    pending_lbl.config(text=f"Pending: {len(pending_processes)}")

    # Record data for the real-time plot
    history_ticks.append(tick_counter)
    history_arrived_counts.append(len(arrived_processes))
    history_pending_counts.append(len(pending_processes))

    # Keep a rolling window of the last 40 ticks on the graph
    if len(history_ticks) > 40:
        history_ticks.pop(0)
        history_arrived_counts.pop(0)
        history_pending_counts.pop(0)

    # Refresh the Plot
    update_plot()

    # If all processes have arrived, stop the loop
    if not pending_processes:
        simulation_running = False
        start_button.config(state="normal")
        return

    # Advance time based on the speed slider
    tick_counter += 1
    try:
        speed_ms = int(speed_scale.get())
    except ValueError:
        speed_ms = 200
        
    ventana.after(speed_ms, run_generation_tick)


def update_plot():
    ax.clear()
    
    # Step plots map beautifully to discrete integer event changes over time
    ax.step(history_ticks, history_arrived_counts, label="Arrived (Active)", where="post", color="#28a745", linewidth=2)
    # ax.step(history_ticks, history_pending_counts, label="Pending (In Queue)", where="post", color="#6c757d", linestyle="--")

    ax.set_title("Process Generation Timeline")
    ax.set_xlabel("Timeline Ticks")
    ax.set_ylabel("Process Count")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    
    if history_ticks:
        ax.set_xlim(min(history_ticks), max(history_ticks) + 1)
        max_y = max(history_arrived_counts + history_pending_counts, default=10)
        ax.set_ylim(-0.5, max_y + 2)

    canvas.draw()

# ==========================================
# 4. UI WINDOW SETUP
# ==========================================

ventana = tk.Tk()
ventana.title("Real-Time Process Generator Observer")
ventana.geometry("900x520")

# Top Counter Dashboard
metrics_frame = ttk.Frame(ventana, padding=10)
metrics_frame.pack(side=tk.TOP, fill=tk.X)

tick_label = ttk.Label(metrics_frame, text="Current Tick: 0", font=("Arial", 11))
tick_label.pack(side=tk.LEFT, padx=15)

arrived_lbl = ttk.Label(metrics_frame, text="Arrived: 0", foreground="#1e7e34", font=("Arial", 11, "bold"))
arrived_lbl.pack(side=tk.LEFT, padx=15)

pending_lbl = ttk.Label(metrics_frame, text="Pending: 0", foreground="#6c757d", font=("Arial", 11, "bold"))
pending_lbl.pack(side=tk.LEFT, padx=15)

# Settings Side Panel (Right)
control_frame = ttk.LabelFrame(ventana, text=" Generator Settings ", padding=15)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

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

ttk.Label(control_frame, text="Tick Interval Speed (ms):").pack(anchor="w")
speed_scale = ttk.Scale(control_frame, from_=50, to=1000, value=250)
speed_scale.pack(fill=tk.X, pady=(0, 20))

start_button = ttk.Button(control_frame, text="🚀 Start Stream", command=start_generation)
start_button.pack(fill=tk.X, ipady=5)

# Matplotlib Left Canvas
figura = Figure(figsize=(5, 4), dpi=100)
ax = figura.add_subplot(111)
canvas = FigureCanvasTkAgg(figura, master=ventana)
canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

ventana.mainloop()