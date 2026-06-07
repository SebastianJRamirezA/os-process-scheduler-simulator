import tkinter as tk
from gui import SchedulerGUI

# ==========================================
# 5. ENTRY POINT EXECUTION
# ==========================================
if __name__ == "__main__":
    app_root = tk.Tk()
    engine_app = SchedulerGUI(app_root)
    app_root.mainloop()