import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import calendar
import random
from tkinter import messagebox

# Create the main application window
root = tk.Tk()
root.title("Scheduling Automation Tool")
root.geometry("1200x700")

# Define a font for readability
default_font = tkFont.Font(size=10)

# Workers List
main_staff = [
    "Alejandrina", "Isabel", "Paulina", "Yuli", "Camila", "Javier",
    "Natalia", "Fiorella", "Martina", "Felipe", "Javiera", "Marianella", "Krishna"
]

# Initialize selected workers list
selected_workers = main_staff[:]

# Initialize years and months
years = list(range(2024, 2035))  # Range from 2024 to 2034
months = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

# Spanish weekday abbreviations
weekday_labels = ["L", "M", "X", "J", "V", "S", "D"]

##### HELPER FUNCTIONS #######

def get_continuous_day_info(day, current_month_days):
    """
    Convert a continuous day number into month and day information.
    Returns: is_preview, actual_day
    """
    if day <= current_month_days:
        return False, day
    else:
        return True, day - current_month_days

def get_total_days():
    """Get total days (current month + 7 preview days)"""
    year = selected_year.get()
    month = months[selected_month.get()]
    current_month_days = calendar.monthrange(year, month)[1]
    return current_month_days + 7

def clear_violations_if_resolved(worker_index, changed_day):
    """Check and clear violation highlights if they're resolved"""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    consecutive_days = 0
    
    # Find the start of the current work streak
    start_day = changed_day
    while start_day > 1:
        prev_shift = cells[(worker_index, start_day - 1)].get()
        if prev_shift in ["L", "SL", "DL"]:
            break
        start_day -= 1
    
    # Check forward from the start of the streak
    for day in range(start_day, min(days_in_month + 1, changed_day + 7)):
        current_shift = cells[(worker_index, day)].get()
        cell = cells[(worker_index, day)]
        
        if current_shift in ["L", "SL", "DL"]:
            consecutive_days = 0
            # If this cell was marked as violation, restore its proper color
            if 'red' in cell.cget('bg'):
                if current_shift in ["L", "SL"]:
                    cell.config(bg="#FFFF99")
                elif current_shift == "DL":
                    cell.config(bg="#90EE90")
        else:
            consecutive_days += 1
            # If consecutive days is now under 7, remove red highlight
            if consecutive_days < 7 and 'red' in cell.cget('bg'):
                if current_shift in ["N", "LN", "10N", "10LN"]:
                    cell.config(bg="#D3D3D3")
                elif current_shift in ["M", "M4"]:
                    cell.config(bg="#ADD8E6")
                elif current_shift in ["T", "2T"]:
                    cell.config(bg="#FFA07A")
                elif current_shift == "I":
                    cell.config(bg="#E6E6FA")
                else:
                    cell.config(bg="white")
                    
def convert_selected_to_special():
    """Convert selected regular shifts to their special versions"""
    if not selected_cells:  # If no cells are selected
        messagebox.showwarning("Warning", "Please select cells to convert first")
        return
        
    for worker_index, day in selected_cells:
        cell = cells[(worker_index, day)]
        current_shift = cell.get()
        
        # Convert each type of shift
        if current_shift == "M":
            assign_shift(day, selected_workers[worker_index], "M4")
        elif current_shift == "T":
            assign_shift(day, selected_workers[worker_index], "2T")
        elif current_shift == "N":
            assign_shift(day, selected_workers[worker_index], "10N")
        elif current_shift == "LN":
            assign_shift(day, selected_workers[worker_index], "10LN")
    
    # Clear selections after converting
    for worker_index, day in selected_cells:
        cells[(worker_index, day)].config(highlightbackground='white', highlightthickness=1)
    selected_cells.clear()
    
    # Update total hours after conversion
    update_total_hours()
    
    # Exit selection mode
    global selection_mode
    selection_mode = False
    shift_buttons["Select"].config(relief='raised')

def update_shift_counters():
    """Update all shift counter labels"""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    total_days = days_in_month + 7  # Including preview
    
    # Clear all counters
    for (shift, day), label in shift_counter_labels.items():
        label.config(text="0")
    
    # Count shifts for each day
    for day in range(1, total_days + 1):
        morning_count = 0
        tarde_count = 0
        night_count = 0
        
        for worker_index, worker in enumerate(selected_workers):
            shift = cells[(worker_index, day)].get()
            if shift in ["M", "M4"]:
                morning_count += 1
            elif shift in ["T", "2T"]:
                tarde_count += 1
            elif shift in ["N", "LN", "10N", "10LN"]:
                night_count += 1
        
        # Update labels
        shift_counter_labels[("M", day)].config(text=str(morning_count))
        shift_counter_labels[("T", day)].config(text=str(tarde_count))
        shift_counter_labels[("N", day)].config(text=str(night_count))

#### HELPER FUNCTIONS END #####

selected_month = tk.StringVar()
selected_month.set("January")
selected_year = tk.IntVar()
selected_year.set(2024)  # Default year

current_shift = None  # Variable to hold the currently selected shift type

# Dictionaries for tracking
cells = {}
consecutive_days = {}  # Track consecutive workdays for each worker and day
total_hours = {}
total_hours_labels = {}  # Labels to display total hours for each worker

# Frame for the top controls
top_frame = tk.Frame(root)
top_frame.pack(side='top', fill='x')

# Dropdown menu for months
month_label = tk.Label(top_frame, text="Select Month:", font=default_font)
month_label.pack(side='left', padx=5, pady=10)

month_menu = ttk.OptionMenu(top_frame, selected_month, selected_month.get(), *months.keys())
month_menu.pack(side='left', padx=5, pady=10)

# Dropdown menu for years
year_label = tk.Label(top_frame, text="Select Year:", font=default_font)
year_label.pack(side='left', padx=5, pady=10)

year_menu = ttk.OptionMenu(top_frame, selected_year, *years)
year_menu.pack(side='left', padx=5, pady=10)

###########BUTTONS START#############

# Button to generate night shifts
nightshift_button = tk.Button(top_frame, text="Assign Night Shifts", command=lambda: assign_night_shifts())
nightshift_button.pack(side='left', padx=10, pady=10)

# Button to assign DL days
dl_button = tk.Button(top_frame, text="Assign DL Sundays", command=lambda: assign_free_sundays())
dl_button.pack(side='left', padx=10, pady=10)

# Add L day button
l_button = tk.Button(top_frame, text="Assign L Days", command=lambda: assign_l_days())
l_button.pack(side='left', padx=10, pady=10)

# Add button for dayshift assignment
dayshift_button = tk.Button(top_frame, text="Assign Dayshifts", command=lambda: assign_dayshifts())
dayshift_button.pack(side='left', padx=10, pady=10)

# Button to run entire schedule
consolidate_button = tk.Button(top_frame, text="Generate Full Schedule", command=lambda: generate_schedule())
consolidate_button.pack(side='left', padx=10, pady=10)

# Button to clear schedule
clear_button = tk.Button(top_frame, text="Clear Schedule", command=lambda: clear_schedule())
clear_button.pack(side='left', padx=10, pady=10)

# Button for next month transfer
next_month_button = tk.Button(top_frame, text="Transfer to Next Month", 
                            command=lambda: transfer_to_next_month())
next_month_button.pack(side='left', padx=10, pady=10)

#Button to fill next month 
complete_button = tk.Button(top_frame, text="Complete & Generate Schedule", 
                          command=lambda: complete_and_generate())
complete_button.pack(side='left', padx=10, pady=10)

########### BUTTONS END #############

# Main frame to hold the table and worker selection panel
main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True)

# Container frame for the table
table_container = tk.Frame(main_frame)
table_container.pack(side='left', fill='both', expand=True)

# Canvas and scrollbar for scrolling the table
canvas = tk.Canvas(table_container)
canvas.pack(side='left', fill='both', expand=True)
scrollbar = tk.Scrollbar(table_container, orient='vertical', command=canvas.yview)
scrollbar.pack(side='right', fill='y')
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

# Frame inside the canvas to hold the table
table_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=table_frame, anchor='nw')

# Container frame for the shift options (L, N, DL, M, T, Delete)
shift_options_frame = tk.Frame(main_frame)
shift_options_frame.pack(side='right', fill='y', padx=10)

# Create labels for shift options
shift_label = tk.Label(shift_options_frame, text="Shift Options", font=default_font)
shift_label.pack(pady=5)

# Add to shift_buttons creation section:
# Create shift buttons
shift_buttons = {}

# Create regular shift buttons for side menu
for shift_type in ["L", "SL", "N", "DL", "M", "T", "I"]:  # Added "SL" to the list
    button = tk.Button(shift_options_frame, text=shift_type, 
                      font=default_font, width=10,
                      command=lambda st=shift_type: select_shift(st))
    button.pack(pady=5)
    shift_buttons[shift_type] = button

# Add a separator
tk.Frame(shift_options_frame, height=2, bd=1, relief='sunken').pack(fill='x', pady=5)

# Create action buttons
button = tk.Button(shift_options_frame, text="Delete", 
                  font=default_font, width=10,
                  command=lambda: select_shift("Delete"))
button.pack(pady=5)
shift_buttons["Delete"] = button

button = tk.Button(shift_options_frame, text="Select", 
                  font=default_font, width=10,
                  command=lambda: select_shift("Select"))
button.pack(pady=5)
shift_buttons["Select"] = button

button = tk.Button(shift_options_frame, text="Convert to Special", 
                  font=default_font, width=10,
                  command=convert_selected_to_special)
button.pack(pady=5)
shift_buttons["Convert to Special"] = button

# Add selection handling:
selection_mode = False
selected_cells = []

def select_shift(shift_type):
    global current_shift, selection_mode
    
    # If we were in selection mode and choosing a shift type
    if selection_mode and shift_type not in ["Select"]:
        # Apply the selected shift type to all selected cells
        for worker_index, day in selected_cells:
            worker = selected_workers[worker_index]
            if shift_type == "Delete":
                clear_shift(day, worker)
            else:
                assign_shift(day, worker, shift_type)
        
        # Clear the selection
        for worker_index, day in selected_cells:
            cells[(worker_index, day)].config(highlightbackground='white', highlightthickness=1)
        selected_cells.clear()
        selection_mode = False
    
    # Handle entering/exiting selection mode
    if shift_type == "Select":
        selection_mode = not selection_mode  # Toggle selection mode
        if not selection_mode:  # If turning off selection mode
            # Clear all selections
            for worker_index, day in selected_cells:
                cells[(worker_index, day)].config(highlightbackground='white', highlightthickness=1)
            selected_cells.clear()
    
    # Update button appearances
    for btn in shift_buttons.values():
        btn.config(relief='raised')
    if selection_mode:
        shift_buttons["Select"].config(relief='sunken')
    elif shift_type != "Delete":
        shift_buttons[shift_type].config(relief='sunken')
    
    current_shift = shift_type

# Modify cell click handler:
def on_cell_click(event, worker_index, day):
    global current_shift, selection_mode
    if selection_mode:
        cell = cells[(worker_index, day)]
        if (worker_index, day) not in selected_cells:
            selected_cells.append((worker_index, day))
            cell.config(highlightbackground='blue', highlightthickness=2)
        else:
            selected_cells.remove((worker_index, day))
            cell.config(highlightbackground='white', highlightthickness=1)
    elif current_shift:
        worker = selected_workers[worker_index]
        if current_shift == "Delete":
            clear_shift(day, worker)
        else:
            assign_shift(day, worker, current_shift)
    
# Function to create the schedule table with day and weekday labels + preview of next month
def create_table():
    for widget in table_frame.winfo_children():
        widget.destroy()  # Clear existing content

    cells.clear()
    total_hours_labels.clear()
    consecutive_days.clear()
    total_hours.clear()

    # Get the year and month as integers
    year = selected_year.get()
    month = months[selected_month.get()]
    
    # Get the next month and year
    next_month_idx = month + 1
    next_year = year
    if next_month_idx > 12:
        next_month_idx = 1
        next_year += 1
    
    # Get month names for display
    current_month_name = selected_month.get()
    next_month_name = list(months.keys())[next_month_idx - 1]
    
    # Get the days in current and next month
    current_first_day, days_in_month = calendar.monthrange(year, month)
    next_first_day, days_in_next = calendar.monthrange(next_year, next_month_idx)
    
    preview_days = 7  # Number of days to show in preview
    total_columns = days_in_month + preview_days + 3  # +2 for separator and total hours

    # Create month headers
    current_month_label = tk.Label(table_frame, 
                                 text=f"Current Month: {current_month_name} {year}", 
                                 font=('Arial', 10, 'bold'))
    current_month_label.grid(row=0, column=0, 
                           columnspan=days_in_month + 1, 
                           sticky='w', padx=5, pady=5)
    
    next_month_label = tk.Label(table_frame, 
                               text=f"Preview: {next_month_name} {next_year}", 
                               font=('Arial', 10, 'bold'))
    next_month_label.grid(row=0, column=days_in_month + 2, 
                         columnspan=preview_days, 
                         sticky='w', padx=5, pady=5)

    # Header row with weekday labels for current month
    for day in range(1, days_in_month + 1):
        weekday = weekday_labels[(current_first_day + day - 1) % 7]
        tk.Label(table_frame, text=f"{day}\n({weekday})", 
                font=default_font).grid(row=1, column=day, padx=2, pady=2)

    # Add visual separator
    separator = tk.Label(table_frame, text="║", font=('Arial', 10, 'bold'))
    separator.grid(row=1, column=days_in_month + 1, rowspan=len(selected_workers) + 1)

    # Header row with weekday labels for preview days
    for day in range(1, preview_days + 1):
        weekday = weekday_labels[(next_first_day + day - 1) % 7]
        tk.Label(table_frame, text=f"{day}\n({weekday})", 
                font=default_font).grid(row=1, column=days_in_month + 1 + day, padx=2, pady=2)

    # Header for total hours
    tk.Label(table_frame, text="Total\nHours", 
            font=default_font).grid(row=1, column=total_columns - 1, padx=2, pady=2)

    # Row label for workers
    tk.Label(table_frame, text="Workers", 
            font=default_font).grid(row=1, column=0, padx=2, pady=2, sticky='w')

    # Rows for each worker
    for i, worker in enumerate(selected_workers):
        row = i + 2  # Start after headers
        bg_color = "#F0F0F0" if i % 2 == 0 else "#FFFFFF"
        
        # Worker name
        tk.Label(table_frame, text=worker, 
                font=default_font, bg=bg_color).grid(row=row, column=0, 
                                                    padx=2, pady=2, sticky='w')
        
        # Current month cells
        for day in range(1, days_in_month + 1):
            cell = tk.Entry(table_frame, font=default_font, 
                          bg=bg_color, width=3, justify='center')
            cell.grid(row=row, column=day, padx=1, pady=1)
            cells[(i, day)] = cell
            cell.bind("<Button-1>", lambda event, idx=i, d=day: on_cell_click(event, idx, d))

        # Preview month cells (with different background to distinguish)
        preview_bg = "#F5F5F5" if i % 2 == 0 else "#FFFFFF"
        for day in range(1, preview_days + 1):
            cell = tk.Entry(table_frame, font=default_font, 
                          bg=preview_bg, width=3, justify='center')
            cell.grid(row=row, column=days_in_month + 1 + day, padx=1, pady=1)
            cells[(i, days_in_month + day)] = cell  # Store preview cells with continued numbering
            cell.bind("<Button-1>", 
                     lambda event, idx=i, d=days_in_month + day: on_cell_click(event, idx, d))

        # Total hours label
        total_hours_label = tk.Label(table_frame, text="0", 
                                   font=default_font, bg=bg_color)
        total_hours_label.grid(row=row, column=total_columns - 1, padx=2, pady=2)
        total_hours_labels[i] = total_hours_label

    # Adjust column widths
    for col in range(1, total_columns):
        table_frame.grid_columnconfigure(col, minsize=25)

    table_frame.grid_columnconfigure(0, minsize=100)
    table_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox('all'))

    # Counter Logic for M/T/N shifts

        # Add separator before counters
    separator_row = tk.Label(table_frame, text="-" * 50, font=default_font)
    separator_row.grid(row=len(selected_workers) + 2, column=0, 
                      columnspan=total_columns, pady=5)

    # Add counter rows for each shift type
    shifts_to_count = ["M", "T", "N"]
    shift_labels = {"M": "Morning:", "T": "Afternoon:", "N": "Night:"}
    
    counter_labels = {}  # Store references to counter labels
    for idx, shift in enumerate(shifts_to_count):
        # Label for the shift type
        tk.Label(table_frame, text=shift_labels[shift], 
                font=default_font, anchor='e').grid(row=len(selected_workers) + 3 + idx, 
                                                  column=0, sticky='e', padx=5)
        
        # Counter for each day
        for day in range(1, days_in_month + preview_days + 1):
            actual_day = day if day <= days_in_month else days_in_month + (day - days_in_month)
            label = tk.Label(table_frame, text="0", font=default_font)
            label.grid(row=len(selected_workers) + 3 + idx, column=actual_day, padx=2)
            counter_labels[(shift, actual_day)] = label

    # Store counter_labels in a global variable so other functions can access it
    global shift_counter_labels
    shift_counter_labels = counter_labels
    
    # Initial count update
    update_shift_counters()

    # Counter Table Logic End

def update_total_hours():
    total_hours.clear()
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    preview_days = 7
    total_days = days_in_month  # We only count hours for current month, not preview
    
    for worker_index, worker in enumerate(selected_workers):
        total = 0
        for day in range(1, total_days + 1):  # Go through entire month
            cell_value = cells[(worker_index, day)].get()
            
            # Handle special shifts (extra hour)
            if cell_value in ["M4", "2T"]:
                total += 8.5  # Regular 7.5 + 1 extra hour
            elif cell_value in ["10N", "10LN"]:
                total += 8.5  # Night shift with extra hour
            # Handle regular shifts
            elif cell_value in ["N", "LN", "M", "T", "I"]:
                total += 7.5
            # Free days count as 0 hours
            elif cell_value in ["SL", "L", "DL"]:
                total += 0
            else:
                # For numeric counters or empty cells, only count if it's a workday
                if cell_value and cell_value.strip():
                    try:
                        int(cell_value)  # If it's a number (consecutive day counter)
                        total += 7.5
                    except ValueError:
                        pass  # Ignore non-integer values
        
        total_hours[worker_index] = total
        total_hours_labels[worker_index].config(text=str(total))

# NIGHT SHIFT ASSIGNMENT LOGIC START
def assign_night_shifts(start_from_day=1):
    if start_from_day == 1:
        clear_schedule()
    
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    preview_days = 7
    day = start_from_day
    worker_pool = selected_workers[:]
    used_workers = []
    last_night_workers = []
    
    # Special handling for start of month after transfer
    if start_from_day == 1:
        # Check first few days to see if anyone is in middle of night cycle
        for worker_index, worker in enumerate(selected_workers):
            night_count = 0
            for check_day in range(1, 4):  # Check first 3 days
                if cells[(worker_index, check_day)].get() in ["N", "LN"]:
                    night_count += 1
            
            # If worker has 1 or 2 nights in first days, they're mid-cycle
            if 0 < night_count < 3:
                last_night_workers = [worker]
                # Remove them from initial pool
                if worker in worker_pool:
                    worker_pool.remove(worker)
                break  # We found our continuing night shift worker(s)
    
    # Regular mid-month analysis
    elif start_from_day > 1:
        # Find last completed night cycle
        for prev_day in range(start_from_day - 1, 0, -1):
            night_workers = set()
            for worker in selected_workers:
                worker_index = selected_workers.index(worker)
                shift = cells[(worker_index, prev_day)].get()
                if shift in ["N", "LN"]:
                    night_workers.add(worker)
                elif shift == "SL" and night_workers:
                    used_workers.extend(night_workers)
                    night_workers = set()
            if night_workers:
                last_night_workers = list(night_workers)
                break
        
        worker_pool = [w for w in worker_pool if w not in used_workers]

    while day <= days_in_month + preview_days:
        # Replenish pool if needed
        if len(worker_pool) < 3:
            worker_pool = selected_workers[:]
            used_workers = []  # Reset used workers when restarting pool
        
        # Select workers for this cycle
        available_pool = [w for w in worker_pool if w not in last_night_workers]
        if len(available_pool) >= 3:
            selected_for_night = random.sample(available_pool, 3)
        else:
            # This should rarely happen as we manage the pool carefully
            selected_for_night = random.sample(worker_pool, 3)
        
        # Verify no collisions with previous cycle ending
        if last_night_workers:
            for prev_worker in last_night_workers:
                end_day = day - 1
                if end_day > 0:
                    worker_index = selected_workers.index(prev_worker)
                    # Check if they properly finished their cycle
                    if cells[(worker_index, end_day)].get() not in ["SL", "L"]:
                        continue  # Skip this day if previous cycle isn't properly finished
        
        # Assign the 4-day cycle (N N N LN)
        cycle_complete = True
        for day_offset in range(4):
            current_day = day + day_offset
            if current_day > days_in_month + preview_days:
                cycle_complete = False
                break
            
            for worker in selected_for_night:
                shift_type = "N" if day_offset < 3 else "LN"
                actual_day = (current_day if current_day <= days_in_month 
                            else days_in_month + (current_day - days_in_month))
                assign_shift(actual_day, worker, shift_type)
        
        # Only assign SL and L if cycle was completed
        if cycle_complete:
            # Assign SL day
            rest_day = day + 4
            if rest_day <= days_in_month + preview_days:
                for worker in selected_for_night:
                    actual_rest_day = (rest_day if rest_day <= days_in_month 
                                     else days_in_month + (rest_day - days_in_month))
                    assign_shift(actual_rest_day, worker, "SL")
                    
                    # Assign L day after SL if no DL is present
                    next_day = rest_day + 1
                    if next_day <= days_in_month + preview_days:
                        worker_index = selected_workers.index(worker)
                        next_actual_day = (next_day if next_day <= days_in_month 
                                         else days_in_month + (next_day - days_in_month))
                        next_day_shift = cells[(worker_index, next_actual_day)].get()
                        if next_day_shift != "DL":
                            assign_shift(next_actual_day, worker, "L")
            
            # Move completed workers to used list
            used_workers.extend(selected_for_night)
            # Remove them from available pool
            worker_pool = [w for w in worker_pool if w not in selected_for_night]
        
        last_night_workers = selected_for_night
        day = day + 4  # Move to next cycle start
# NIGHT SHIFT ASSIGNMENT LOGIC END

# NIGHT SHIFT AFTER TRANSFER LOGIC START #

def assign_night_shifts_after_transfer():
   """Special version of night shift assignment for after month transfer"""
   days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
   preview_days = 7
   
   # Step 1: Identify and complete preview cycles
   preview_night_workers = []
   
   for worker in selected_workers:
       worker_index = selected_workers.index(worker)
       for day in range(1, 8):
           if cells[(worker_index, day)].get() == "N":
               # Count consecutive N/LN
               sequence = []
               for check_day in range(day, 8):
                   check_shift = cells[(worker_index, check_day)].get()
                   if check_shift in ["N", "LN"]:
                       sequence.append(check_shift)
                   else:
                       break
               if sequence:  # Found a sequence
                   if sequence[-1] == "LN":
                       preview_night_workers.append((worker, day, "needs_sl_l"))
                   elif len(sequence) == 3:
                       preview_night_workers.append((worker, day, "needs_ln_sl_l"))
                   elif len(sequence) == 2:
                       preview_night_workers.append((worker, day, "needs_n_ln_sl_l"))
                   elif len(sequence) == 1:
                       preview_night_workers.append((worker, day, "needs_nn_ln_sl_l"))
               break  # Found this worker's cycle, move to next
   
   # Step 2: Complete existing night cycles
   latest_completion = 8
   workers_in_cycles = set()  # Keep track of all workers involved in night cycles
   
   for worker, start_day, completion_type in preview_night_workers:
       workers_in_cycles.add(worker)
       worker_index = selected_workers.index(worker)
       
       if completion_type == "needs_sl_l":
           assign_shift(start_day + 4, worker, "SL")
           assign_shift(start_day + 5, worker, "L")
           latest_completion = max(latest_completion, start_day + 5)
       
       elif completion_type == "needs_ln_sl_l":
           assign_shift(start_day + 3, worker, "LN")
           assign_shift(start_day + 4, worker, "SL")
           assign_shift(start_day + 5, worker, "L")
           latest_completion = max(latest_completion, start_day + 5)
       
       elif completion_type == "needs_n_ln_sl_l":
           assign_shift(start_day + 2, worker, "N")
           assign_shift(start_day + 3, worker, "LN")
           assign_shift(start_day + 4, worker, "SL")
           assign_shift(start_day + 5, worker, "L")
           latest_completion = max(latest_completion, start_day + 5)
       
       elif completion_type == "needs_nn_ln_sl_l":
           assign_shift(start_day + 1, worker, "N")
           assign_shift(start_day + 2, worker, "N")
           assign_shift(start_day + 3, worker, "LN")
           assign_shift(start_day + 4, worker, "SL")
           assign_shift(start_day + 5, worker, "L")
           latest_completion = max(latest_completion, start_day + 5)
   
   # Step 3: Setup initial pool for new assignments
   worker_pool = [w for w in selected_workers if w not in workers_in_cycles]
   used_workers = []
   last_night_workers = []
   
   # Find SL day of last completed cycle to start new cycles
   day = latest_completion
   for check_day in range(latest_completion, 0, -1):
       sl_count = 0
       for worker_index, worker in enumerate(selected_workers):
           if cells[(worker_index, check_day)].get() == "SL":
               sl_count += 1
       if sl_count == 3:  # Found where a group hits SL
           day = check_day
           break
   
   # Step 4: Continue with regular night shift assignment
   while day <= days_in_month + preview_days:
       # Replenish pool if needed
       if len(worker_pool) < 3:
           worker_pool = selected_workers[:]
           # Keep excluding last night workers to prevent back-to-back
           worker_pool = [w for w in worker_pool if w not in last_night_workers]
           used_workers = []
       
       # Select workers for this cycle
       available_pool = [w for w in worker_pool if w not in last_night_workers]
       if len(available_pool) >= 3:
           selected_for_night = random.sample(available_pool, 3)
       else:
           # If we can't avoid using last_night_workers, use full pool
           selected_for_night = random.sample(worker_pool, 3)
       
       # Assign the 4-day cycle (N N N LN)
       cycle_complete = True
       for day_offset in range(4):
           current_day = day + day_offset
           if current_day > days_in_month + preview_days:
               cycle_complete = False
               break
           
           for worker in selected_for_night:
               shift_type = "N" if day_offset < 3 else "LN"
               assign_shift(current_day, worker, shift_type)
       
       # Only assign SL and L if cycle was completed
       if cycle_complete:
           rest_day = day + 4
           if rest_day <= days_in_month + preview_days:
               for worker in selected_for_night:
                   assign_shift(rest_day, worker, "SL")
                   
                   next_day = rest_day + 1
                   if next_day <= days_in_month + preview_days:
                       worker_index = selected_workers.index(worker)
                       if cells[(worker_index, next_day)].get() != "DL":
                           assign_shift(next_day, worker, "L")
           
           used_workers.extend(selected_for_night)
           worker_pool = [w for w in worker_pool if w not in selected_for_night]
       
       last_night_workers = selected_for_night
       day = day + 4  # Move to next cycle start
# NIGHTSHIFT AFTER TRANSFER LOGIC END #

# DL ASSIGNMENT LOGIC START
def assign_free_sundays(start_from_day=1):
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    
    # Get ALL Sundays in the month
    all_sundays = [day for day in range(1, days_in_month + 1) 
                   if calendar.weekday(selected_year.get(), months[selected_month.get()], day) == 6]
    
    if not all_sundays:
        messagebox.showinfo("Info", "No Sundays found in this month.")
        return
    
    # Initialize tracking
    dl_per_sunday = {day: [] for day in all_sundays}
    worker_dls = {worker: [] for worker in selected_workers}
    
    # Count existing DLs (in case we're starting from day 8)
    for worker in selected_workers:
        worker_index = selected_workers.index(worker)
        for sunday in all_sundays:
            if cells[(worker_index, sunday)].get() == "DL":
                dl_per_sunday[sunday].append(worker)
                worker_dls[worker].append(sunday)
    
    # First pass - assign first DLs to alternating Sundays
    for worker in selected_workers:
        if len(worker_dls[worker]) >= 2:  # Skip if already has 2 DLs
            continue
            
        worker_index = selected_workers.index(worker)
        # Try first half of Sundays for first DL
        first_dl_assigned = False
        for i, sunday in enumerate(all_sundays):
            if i % 2 == 0:  # Even indexed Sundays
                if (len(dl_per_sunday[sunday]) < 7 and 
                    cells[(worker_index, sunday)].get() not in ["N", "LN", "SL"]):
                    assign_shift(sunday, worker, "DL")
                    dl_per_sunday[sunday].append(worker)
                    worker_dls[worker].append(sunday)
                    first_dl_assigned = True
                    break
        
        # If couldn't assign on even Sundays, try odd ones
        if not first_dl_assigned:
            for i, sunday in enumerate(all_sundays):
                if i % 2 == 1:  # Odd indexed Sundays
                    if (len(dl_per_sunday[sunday]) < 7 and 
                        cells[(worker_index, sunday)].get() not in ["N", "LN", "SL"]):
                        assign_shift(sunday, worker, "DL")
                        dl_per_sunday[sunday].append(worker)
                        worker_dls[worker].append(sunday)
                        first_dl_assigned = True
                        break
    
    # Second pass - try to maintain alternating pattern first
    for worker in selected_workers:
        if len(worker_dls[worker]) >= 2:  # Skip if already has 2 DLs
            continue
            
        worker_index = selected_workers.index(worker)
        if not worker_dls[worker]:  # Skip if no first DL
            continue
            
        first_dl = worker_dls[worker][0]
        first_dl_index = all_sundays.index(first_dl)
        second_dl_assigned = False
        
        # First try ideal spacing (2 Sundays apart)
        for offset in [2, -2, 3, -3]:  # Try both forward and backward
            target_index = first_dl_index + offset
            if 0 <= target_index < len(all_sundays):
                target_sunday = all_sundays[target_index]
                if (len(dl_per_sunday[target_sunday]) < 7 and 
                    cells[(worker_index, target_sunday)].get() not in ["N", "LN", "SL"]):
                    assign_shift(target_sunday, worker, "DL")
                    dl_per_sunday[target_sunday].append(worker)
                    worker_dls[worker].append(target_sunday)
                    second_dl_assigned = True
                    break
        
        # If alternating pattern failed, find the least populated available Sunday
        if not second_dl_assigned:
            # Create list of available Sundays with their population
            available_sundays = []
            for sunday in all_sundays:
                if (sunday != first_dl and
                    len(dl_per_sunday[sunday]) < 7 and 
                    cells[(worker_index, sunday)].get() not in ["N", "LN", "SL"]):
                    available_sundays.append((sunday, len(dl_per_sunday[sunday])))
            
            # Sort by population (least populated first)
            available_sundays.sort(key=lambda x: x[1])
            
            # Assign to least populated available Sunday
            if available_sundays:
                best_sunday = available_sundays[0][0]
                assign_shift(best_sunday, worker, "DL")
                dl_per_sunday[best_sunday].append(worker)
                worker_dls[worker].append(best_sunday)
    
    # Final verification and summary
    final_summary = []
    any_missing = False
    for worker in selected_workers:
        dls = sorted(worker_dls[worker])
        if len(dls) < 2:
            status = f"WARNING: Only has {len(dls)} DL(s)"
            any_missing = True
        else:
            spacing = dls[1] - dls[0]
            status = f"Complete (2 DLs, {spacing} days apart)"
        final_summary.append(f"{worker}: {status} on days {dls}")
    
    # Summary of DLs per Sunday
    sunday_summary = [f"Sunday {day}: {len(dl_per_sunday[day])} workers" 
                     for day in all_sundays]
    
    complete_summary = "\n".join(final_summary) + "\n\nSundays Distribution:\n" + "\n".join(sunday_summary)
    
    if any_missing:
        messagebox.showwarning("DL Assignment Warning", 
                             "Some workers did not get 2 DLs!\n\n" + complete_summary)
    else:
        messagebox.showinfo("DL Assignment Complete", complete_summary)
# DL ASSIGNMENT LOGIC END

# L DAY ASSIGNMENT LOGIC START
def can_place_l_here(worker_index, day, preview=False):
    """Check if we can place an L on this day for the specified worker."""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    
    # Handle preview days
    if preview:
        if day < 1 or day > 7:  # Preview days range
            return False
        actual_day = days_in_month + day
    else:
        if day < 1 or day > days_in_month:
            return False
        actual_day = day
    
    current_shift = cells[(worker_index, actual_day)].get()
    
    # Cannot place L if there's already a shift or free day assigned
    if current_shift in ["N", "LN", "SL", "DL", "L", "M", "T"]:
        return False
    
    # Check if previous day is not an L day, handling month boundary
    if actual_day > 1:
        prev_shift = cells[(worker_index, actual_day - 1)].get()
        if prev_shift == "L":
            return False
    
    # Check if next day is not an L day, handling month boundary
    if (not preview and day < days_in_month) or (preview and day < 7):
        next_shift = cells[(worker_index, actual_day + 1)].get()
        if next_shift == "L":
            return False
    
    return True

def needs_l_before_sl(worker_index, sl_day, days_in_month):
    """Check if worker needs L before SL day, considering month boundary."""
    start_day = max(1, sl_day - 7)
    
    # If checking near month boundary, include preview days
    if sl_day <= 7:  # SL day is in preview
        # Check last days of previous month
        for day in range(max(1, days_in_month - (7 - sl_day)), days_in_month + 1):
            if cells[(worker_index, day)].get() in ["L", "DL"]:
                return False
        # Check preview days up to SL
        for day in range(1, sl_day):
            if cells[(worker_index, days_in_month + day)].get() in ["L", "DL"]:
                return False
    else:
        # Regular check within month
        for day in range(start_day, sl_day):
            if cells[(worker_index, day)].get() in ["L", "DL"]:
                return False
    return True

def assign_l_days(start_from_day=1):  # Add parameter here
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    preview_days = 7
    
    # First pass: Handle L days before SL for both current month and preview
    for worker_index, worker in enumerate(selected_workers):
        # Check current month
        day = 1
        while day <= days_in_month:
            current_shift = cells[(worker_index, day)].get()
            if current_shift == "SL":
                if needs_l_before_sl(worker_index, day, days_in_month):
                    l_day = day - 7
                    if l_day > 0 and can_place_l_here(worker_index, l_day):
                        assign_shift(l_day, worker, "L")
            day += 1
            
        # Check preview period
        for day in range(1, preview_days + 1):
            current_shift = cells[(worker_index, days_in_month + day)].get()
            if current_shift == "SL":
                if needs_l_before_sl(worker_index, day, days_in_month):
                    l_day = day - 7
                    if l_day > 0:  # L day might be in current month
                        if l_day <= 7:  # L should be in preview
                            if can_place_l_here(worker_index, l_day, preview=True):
                                assign_shift(days_in_month + l_day, worker, "L")
                        else:  # L should be in current month
                            actual_l_day = days_in_month - (7 - l_day)
                            if can_place_l_here(worker_index, actual_l_day):
                                assign_shift(actual_l_day, worker, "L")
    
    # Second pass: Handle consecutive working days
    for worker_index, worker in enumerate(selected_workers):
        consecutive_days = 0
        # Start from day 1 of current month through preview period
        for day in range(1, days_in_month + preview_days + 1):
            actual_day = day if day <= days_in_month else days_in_month + (day - days_in_month)
            current_shift = cells[(worker_index, actual_day)].get()
            
            # Reset counter for free days
            if current_shift in ["L", "SL", "DL"]:
                consecutive_days = 0
            else:
                consecutive_days += 1
                
                # Place L if reaching 6 consecutive days
                if consecutive_days >= 6:
                    next_day = day + 1
                    if next_day <= days_in_month + preview_days:
                        next_actual_day = (next_day if next_day <= days_in_month 
                                         else days_in_month + (next_day - days_in_month))
                        preview_check = next_day > days_in_month
                        
                        if can_place_l_here(worker_index, 
                                          next_day - days_in_month if preview_check else next_day, 
                                          preview=preview_check):
                            assign_shift(next_actual_day, worker, "L")
                            consecutive_days = 0
                        elif consecutive_days >= 7:
                            cells[(worker_index, actual_day)].config(bg='red')


    # Final check for violations including preview period
    check_violations(include_preview=True)

def check_violations(include_preview=False):
    """Check for any remaining violations after L day assignment."""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    total_days = days_in_month + (7 if include_preview else 0)
    
    has_violations = False
    
    for worker_index, worker in enumerate(selected_workers):
        consecutive_days = 0
        for day in range(1, total_days + 1):
            actual_day = day if day <= days_in_month else days_in_month + (day - days_in_month)
            current_shift = cells[(worker_index, actual_day)].get()
            
            if current_shift not in ["L", "SL", "DL"]:
                consecutive_days += 1
                if consecutive_days >= 7:
                    cells[(worker_index, actual_day)].config(bg='red')
                    has_violations = True
            else:
                consecutive_days = 0
    
    if has_violations:
        messagebox.showwarning("Schedule Warning", 
            "There are workers with more than 6 consecutive working days.")
# L DAY ASSIGNMENT LOGIC END

# DAYSHIFT ASSIGNMENT LOGIC START
def assign_dayshifts(start_from_day=1):
   days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
   preview_days = 7
   total_days = days_in_month + preview_days
   worker_shift_type = {}  # Track current shift type for each worker
   
   # First, assign shifts normally for everyone except Marianella
   for worker_index, worker in enumerate(selected_workers):
       if worker == "Marianella":  # Skip Marianella for now
           continue
           
       # Initialize shift type based on previous shifts
       last_shift = None
       last_free_day = False
       
       for day in range(start_from_day - 1, 0, -1):
           shift = cells[(worker_index, day)].get()
           if shift in ['L', 'SL', 'DL']:
               last_free_day = True
           elif shift in ['M', 'T'] and last_shift is None:
               last_shift = shift
               if last_free_day:
                   last_shift = 'T' if shift == 'M' else 'M'
               break
       
       worker_shift_type[worker] = last_shift if last_shift else random.choice(['M', 'T'])
   
   # Assign shifts day by day for everyone except Marianella
   for day in range(start_from_day, total_days + 1):
       actual_day = day if day <= days_in_month else days_in_month + (day - days_in_month)
       morning_count = 0
       tarde_count = 0
       
       # Count existing shifts
       for worker in selected_workers:
           if worker == "Marianella":  # Skip Marianella in counting
               continue
           worker_index = selected_workers.index(worker)
           current_shift = cells[(worker_index, actual_day)].get()
           if current_shift == 'M':
               morning_count += 1
           elif current_shift == 'T':
               tarde_count += 1
       
       # Assign shifts for everyone except Marianella
       for worker_index, worker in enumerate(selected_workers):
           if worker == "Marianella":
               continue
               
           current_cell = cells[(worker_index, actual_day)].get()
           
           # Skip if already has a shift or free day
           if current_cell in ["N", "LN", "SL", "DL", "L", "M", "T"]:
               continue
           
           # First priority: Check previous day
           if actual_day > 1:
               prev_shift = cells[(worker_index, actual_day - 1)].get()
               if prev_shift == "T":
                   worker_shift_type[worker] = "T"  # Must be T after T
               elif prev_shift in ["L", "SL", "DL"]:
                   worker_shift_type[worker] = 'T' if worker_shift_type[worker] == 'M' else 'M'
           
           # Only consider balance if not forced by T->T rule
           if actual_day > 1 and cells[(worker_index, actual_day - 1)].get() != "T":
               if morning_count >= 4:
                   worker_shift_type[worker] = 'T'
               elif tarde_count >= 5:
                   worker_shift_type[worker] = 'M'
           
           # Assign shift
           assign_shift(actual_day, worker, worker_shift_type[worker])
           
           # Update counts
           if worker_shift_type[worker] == 'M':
               morning_count += 1
           else:
               tarde_count += 1
   
   # Now assign Marianella's shifts based on Javiera's schedule
   marianella_index = selected_workers.index("Marianella")
   javiera_index = selected_workers.index("Javiera")
   
   # Track Marianella's last shift type for continuity
   marianella_last_shift = None
   
   for day in range(start_from_day, total_days + 1):
       actual_day = day if day <= days_in_month else days_in_month + (day - days_in_month)
       current_cell = cells[(marianella_index, actual_day)].get()
       
       # Skip if already has a shift or free day
       if current_cell in ["N", "LN", "SL", "DL", "L", "M", "T"]:
           if current_cell in ["M", "T"]:
               marianella_last_shift = current_cell
           continue
       
       # Get Javiera's shift for this day
       javiera_shift = cells[(javiera_index, actual_day)].get()
       
       # First priority for Marianella: T after T rule
       if actual_day > 1:
           prev_shift = cells[(marianella_index, actual_day - 1)].get()
           if prev_shift == "T":
               assign_shift(actual_day, "Marianella", "T")
               marianella_last_shift = "T"
               continue
       
       # Regular Marianella logic if not forced by T->T rule
       if javiera_shift == "M":
           assign_shift(actual_day, "Marianella", "T")
           marianella_last_shift = "T"
       elif javiera_shift == "T":
           assign_shift(actual_day, "Marianella", "M")
           marianella_last_shift = "M"
       elif javiera_shift in ["N", "LN", "L", "SL", "DL"]:
           if actual_day == 1:  # First day of month
               assign_shift(actual_day, "Marianella", "M")
               marianella_last_shift = "M"
           elif actual_day > 1:
               marianella_prev_shift = cells[(marianella_index, actual_day - 1)].get()
               if marianella_prev_shift in ["L", "SL", "DL"]:
                   # After free day: assign Morning
                   assign_shift(actual_day, "Marianella", "M")
                   marianella_last_shift = "M"
               elif marianella_prev_shift in ["M", "T"]:
                   # Continue with previous shift
                   assign_shift(actual_day, "Marianella", marianella_prev_shift)
                   marianella_last_shift = marianella_prev_shift
               else:
                   # Default to Morning if no previous pattern
                   assign_shift(actual_day, "Marianella", "M")
                   marianella_last_shift = "M"
   
   # Final pass to check violations
   check_violations()
# DAYSHIFT ASSIGNMENT LOGIC END

def assign_shift(day, worker, shift_type):
    worker_index = selected_workers.index(worker)
    cell = cells[(worker_index, day)]
    cell.delete(0, tk.END)
    cell.insert(0, shift_type)
    
    # Set cell colors
    if shift_type in ["N", "LN", "10N", "10LN"]:
        cell.config(bg="#D3D3D3", fg="black")  # Grey for all night shifts
    elif shift_type in ["L", "SL"]:
        cell.config(bg="#FFFF99", fg="black")  # Yellow for rest days
    elif shift_type == "DL":
        cell.config(bg="#90EE90", fg="black")  # Light green for DL
    elif shift_type in ["M", "M4"]:
        cell.config(bg="#ADD8E6", fg="black")  # Light blue for all morning shifts
    elif shift_type in ["T", "2T"]:
        cell.config(bg="#FFA07A", fg="black")  # Light salmon for all afternoon shifts
    elif shift_type == "I":
        cell.config(bg="#E6E6FA", fg="black")  # Light purple for I shift
    else:
        cell.config(bg="white", fg="black")
    
    # Always keep text bold
    cell.config(font=('Arial', 10, 'bold'))

    # After assigning a free day, check and clear violations
    if shift_type in ["L", "SL", "DL"]:
        clear_violations_if_resolved(worker_index, day)

    # Recalculate consecutive days from the start
    recalculate_consecutive_days(worker_index, 1)

    # Update total hours
    update_total_hours()
    # Update Shift Counter
    update_shift_counters()

def clear_shift(day, worker):
    worker_index = selected_workers.index(worker)
    cell = cells[(worker_index, day)]
    cell.delete(0, tk.END)
    cell.config(bg="white", fg="black")
    
    # Recalculate consecutive days
    recalculate_consecutive_days(worker_index, 1)  # Start from beginning to ensure accuracy

    # Update total hours
    update_total_hours()
    # Update Shift Counter
    update_shift_counters()

def recalculate_consecutive_days(worker_index, start_day):
    """Recalculate consecutive days for a worker starting from a specific day"""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    preview_days = 7
    total_days = days_in_month + preview_days
    
    # First find last free day before start_day
    last_free = 0  # Start from beginning if no free day found
    for day in range(start_day - 1, 0, -1):
        if cells[(worker_index, day)].get() in ["L", "SL", "DL"]:
            last_free = day
            break
    
    # Start counting from day after last free day
    current_count = 0
    for day in range(last_free + 1, total_days + 1):
        cell_key = (worker_index, day)
        if cell_key not in cells:
            break
            
        current_shift = cells[cell_key].get()
        
        if current_shift in ["L", "SL", "DL"]:
            current_count = 0
            # Clear red background if exists
            if 'red' in cells[cell_key].cget('bg'):
                if current_shift in ["L", "SL"]:
                    cells[cell_key].config(bg="#FFFF99")
                elif current_shift == "DL":
                    cells[cell_key].config(bg="#90EE90")
        else:
            current_count += 1
            # Handle red highlighting based on count
            if current_count >= 7:
                cells[cell_key].config(bg='red')
            elif 'red' in cells[cell_key].cget('bg'):
                # Clear red if no longer a violation
                if current_shift in ["N", "LN"]:
                    cells[cell_key].config(bg="#D3D3D3")
                elif current_shift == "M":
                    cells[cell_key].config(bg="#ADD8E6")
                elif current_shift == "T":
                    cells[cell_key].config(bg="#FFA07A")
                elif current_shift == "I":
                    cells[cell_key].config(bg="#E6E6FA")
                else:
                    cells[cell_key].config(bg="white")
        
        # Update display only in empty or numeric cells
        if not current_shift or current_shift.strip() == "" or current_shift.strip().isdigit():
            cells[cell_key].delete(0, tk.END)
            cells[cell_key].insert(0, str(current_count))
            cells[cell_key].config(fg='red' if current_count >= 6 else 'gray')


def clear_schedule():
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    preview_days = 7
    consecutive_days.clear()  # Clear the consecutive days tracking
    total_hours.clear()
    
    # Clear both current month and preview days
    for (worker_index, day), cell in cells.items():
        # Clear any cell that exists (both current month and preview)
        cell.delete(0, tk.END)
        cell.config(bg="white", fg="black")
        
    # Reset total hours labels
    for label in total_hours_labels.values():
        label.config(text="0")
        
    # Reset shift buttons
    for btn in shift_buttons.values():
        btn.config(relief='raised')

def generate_remaining_schedule():
    """Generate schedule for remaining days while preserving first week"""
    days_in_month = calendar.monthrange(selected_year.get(), months[selected_month.get()])[1]
    
    # Store first week's data
    first_week_data = {}
    for worker_index, worker in enumerate(selected_workers):
        worker_data = []
        for day in range(1, 8):  # Store first 7 days
            shift = cells[(worker_index, day)].get()
            worker_data.append(shift)
        first_week_data[worker] = worker_data
    
    # Clear schedule from day 8 onwards
    for worker_index, worker in enumerate(selected_workers):
        for day in range(8, days_in_month + 1):
            cell = cells[(worker_index, day)]
            cell.delete(0, tk.END)
            cell.config(bg="white", fg="black")
    
    # Restore first week
    for worker_index, worker in enumerate(selected_workers):
        for day in range(1, 8):
            shift = first_week_data[worker][day-1]
            if shift:  # Only restore if there was a shift
                assign_shift(day, worker, shift)
    
    # Generate remaining schedule using existing functions
    assign_night_shifts(start_from_day=8)
    assign_free_sundays(start_from_day=8)
    assign_l_days(start_from_day=8)
    assign_dayshifts(start_from_day=8)
    
    update_total_hours()
    update_shift_counters()
    check_violations(include_preview=True)

def generate_schedule():
    clear_schedule()  # Complete clear
    assign_night_shifts(start_from_day=1)  # Start from beginning
    assign_free_sundays(start_from_day=1)
    assign_l_days(start_from_day=1)
    assign_dayshifts(start_from_day=1)
    update_total_hours()
    update_shift_counters()
    check_violations(include_preview=True)

def transfer_to_next_month():
    """Transfer preview data to next month ONLY"""
    print("\nDEBUG Transfer:")
    current_month_idx = months[selected_month.get()]
    current_year = selected_year.get()
    
    # Store and print preview data
    preview_data = {}
    days_in_month = calendar.monthrange(current_year, current_month_idx)[1]
    
    for worker_index, worker in enumerate(selected_workers):
        worker_shifts = []
        for day in range(1, 8):
            preview_day = days_in_month + day
            shift = cells[(worker_index, preview_day)].get()
            print(f"Getting {worker} day {day}: '{shift}' (type: {type(shift)})")
            worker_shifts.append(shift)
        preview_data[worker] = worker_shifts
    
    # Update month and year
    next_month_idx = current_month_idx + 1
    next_year = current_year
    if next_month_idx > 12:
        next_month_idx = 1
        next_year += 1
    next_month_name = list(months.keys())[next_month_idx - 1]
    
    selected_month.set(next_month_name)
    selected_year.set(next_year)
    
    # ONLY transfer the preview data to new month
    for worker_index, worker in enumerate(selected_workers):
        for day in range(1, 8):
            shift = preview_data[worker][day - 1]
            if shift:
                assign_shift(day, worker, shift)
    
    update_total_hours()

#COMPLETE AND GENERATE FUNCTION START

def complete_and_generate():
    """Complete nightshift cycles and generate rest of month after transfer"""
    # First complete any incomplete night cycles and generate rest of month
    assign_night_shifts_after_transfer()
        
    # Then do the rest of the assignments as before
    assign_free_sundays(start_from_day=8)  # Start after first week
    assign_l_days(start_from_day=8)
    assign_dayshifts(start_from_day=8)
    
    update_total_hours()
    update_shift_counters()
    check_violations()

    # COMPLETE AND GENERATE FUNCTION END

# Update the table when month or year is changed
selected_month.trace('w', lambda *args: create_table())
selected_year.trace('w', lambda *args: create_table())

# Initial table creation
create_table()

# Legend
legend_frame = tk.Frame(root)
legend_frame.pack(side='bottom', fill='x')
tk.Label(
    legend_frame,
    text="N = Noche, LN = Ultima Noche, SL/L = Saliente / Libre, DL = Domingo libre, M = Mañana, T = Tarde, I = Intermedio",
    font=default_font
).pack(pady=5)

# Run the application
root.mainloop()