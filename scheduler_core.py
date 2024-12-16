import calendar
import random
from datetime import datetime, timedelta
import json
import os

class SchedulerCore:
    def __init__(self):
        # Define all staff groups
        self.staff_groups = {
            'sala': {
                'name': 'Personal de Sala',
                'workers_full_time': [  # Regular full-time workers
                    "Alejandrina", "Isabel", "Paulina", "Yuli", "Camila", "Javier",
                    "Natalia", "Fiorella", "Martina", "Felipe", "Javiera", "Marianella", "Krishna"
                ],
                'workers_part_time': [  # Part-time workers
                    "Anais", "Diego Cisterna", "Diego Nuñez", "Jennifer", "Joaquin"
                ],
                'special_rules': ['marianella_javiera']
            },
            'coperia': {
                'name': 'Copería',
                'workers_full_time': [
                    "Eric", "Soledad", "Ester", "Kelly", "Marthita"
                ],
                'workers_part_time': [],
                'special_rules': []
            },
            'cocina': {
                'name': 'Cocina',
                'workers_full_time': [
                    "Soledad", "Gonzalo", "Christopher", "Ahyran", 
                    "Dominique", "Carolina", "Donkan"
                ],
                'workers_part_time': [],
                'special_rules': []
            }
        }
        
        # Start with sala as default
        self.current_group = 'sala'
        # Combine full-time and part-time workers, maintaining order
        self.selected_workers = (
            self.staff_groups[self.current_group]['workers_full_time'] +
            self.staff_groups[self.current_group]['workers_part_time']
        )
        
        # Schedule storage
        self.schedule = {}  # Format: {(worker_index, day): shift_type}
        self.total_hours = {}
    
            # Create autosave directory if it doesn't exist
        if not os.path.exists('autosave'):
            os.makedirs('autosave')
        
            self.load_last_session()


       
    def set_current_group(self, group):
        """Switch to a different staff group"""
        if group in self.staff_groups:
            self.current_group = group
            self.selected_workers = (
                self.staff_groups[group]['workers_full_time'] +
                self.staff_groups[group]['workers_part_time']
            )
            self.schedule.clear()
            self.total_hours.clear()
            return True
        return False

    def is_part_time(self, worker):
        """Check if a worker is part-time"""
        return worker in self.staff_groups[self.current_group]['workers_part_time']

    def has_special_rule(self, rule):
        """Check if current group has a specific special rule"""
        return rule in self.staff_groups[self.current_group]['special_rules']
        
    def initialize_month(self, year, month):
        """Initialize empty schedule for given month"""
        self.year = year
        self.month = month
        self.days_in_month = calendar.monthrange(year, month)[1]
        self.preview_days = 7
        self.schedule.clear()
        self.total_hours.clear()

    def get_shift(self, worker_index, day):
        """Get shift for a specific worker and day"""
        return self.schedule.get((worker_index, day), "")

    def assign_shift(self, day, worker, shift_type):
        """Assign a shift to a worker on a specific day"""
        worker_index = self.selected_workers.index(worker)
        self.schedule[(worker_index, day)] = shift_type
        self.update_total_hours()
        self.save_last_session() 

    def clear_shift(self, day, worker):
        """Clear a shift assignment"""
        worker_index = self.selected_workers.index(worker)
        if (worker_index, day) in self.schedule:
            del self.schedule[(worker_index, day)]
        self.update_total_hours()
        self.save_last_session()
    
    def update_total_hours(self):
        """Calculate total hours for each worker"""
        self.total_hours.clear()
        
        for worker_index, worker in enumerate(self.selected_workers):
            total = 0
            for day in range(1, self.days_in_month + 1):
                shift = self.get_shift(worker_index, day)
                
                if shift in ["M4", "2T", "10N", "10LN"]:
                    total += 8.5
                elif shift in ["N", "LN", "M", "T", "I"]:
                    total += 7.5
                elif shift in ["SL", "L", "DL"]:
                    total += 0
                
            self.total_hours[worker_index] = total

    def assign_night_shifts(self, start_from_day=1):
        """Assign night shift cycles based on group-specific rules"""
        if start_from_day == 1:
            self.clear_schedule()
            
        if self.current_group == 'sala':
            self._assign_sala_nights(start_from_day)
        elif self.current_group == 'cocina':
            self._assign_cocina_nights(start_from_day)
        elif self.current_group == 'coperia':
            self._assign_coperia_nights(start_from_day)

    def _assign_sala_nights(self, start_from_day):
        """Original night shift logic for Sala"""
        day = start_from_day
        worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
        used_workers = []
        last_night_workers = []

        while day <= self.days_in_month + self.preview_days:
            # Replenish pool if needed
            if len(worker_pool) < 3:
                worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
                used_workers = []

            # Select workers for this cycle
            available_pool = [w for w in worker_pool if w not in last_night_workers]
            if len(available_pool) >= 3:
                selected_for_night = random.sample(available_pool, 3)
            else:
                selected_for_night = random.sample(worker_pool, 3)
            
            # Assign the cycle
            cycle_complete = True
            for day_offset in range(4):
                current_day = day + day_offset
                if current_day > self.days_in_month + self.preview_days:
                    cycle_complete = False
                    break
                
                for worker in selected_for_night:
                    shift_type = "N" if day_offset < 3 else "LN"
                    self.assign_shift(current_day, worker, shift_type)
            
            # Handle rest days after cycle
            if cycle_complete:
                rest_day = day + 4
                if rest_day <= self.days_in_month + self.preview_days:
                    for worker in selected_for_night:
                        self.assign_shift(rest_day, worker, "SL")
                        
                        next_day = rest_day + 1
                        if next_day <= self.days_in_month + self.preview_days:
                            worker_index = self.selected_workers.index(worker)
                            if self.get_shift(worker_index, next_day) != "DL":
                                self.assign_shift(next_day, worker, "L")
                
                used_workers.extend(selected_for_night)
                worker_pool = [w for w in worker_pool if w not in selected_for_night]
            
            last_night_workers = selected_for_night
            day = day + 4

    def _assign_cocina_nights(self, start_from_day):
        """Single worker night shift cycles for Cocina"""
        day = start_from_day
        worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
        used_workers = []
        last_night_worker = None
        
        while day <= self.days_in_month + self.preview_days:
            # Replenish pool if needed
            if len(worker_pool) < 1:
                worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
                used_workers = []
            
            # Select worker for this cycle
            available_pool = [w for w in worker_pool if w != last_night_worker]
            if len(available_pool) >= 1:
                selected_for_night = random.choice(available_pool)
            else:
                selected_for_night = random.choice(worker_pool)
            
            # Assign the cycle
            cycle_complete = True
            for day_offset in range(4):
                current_day = day + day_offset
                if current_day > self.days_in_month + self.preview_days:
                    cycle_complete = False
                    break
                
                shift_type = "N" if day_offset < 3 else "LN"
                self.assign_shift(current_day, selected_for_night, shift_type)
            
            # Handle rest days after cycle
            if cycle_complete:
                rest_day = day + 4
                if rest_day <= self.days_in_month + self.preview_days:
                    self.assign_shift(rest_day, selected_for_night, "SL")
                    
                    next_day = rest_day + 1
                    if next_day <= self.days_in_month + self.preview_days:
                        if self.get_shift(self.selected_workers.index(selected_for_night), next_day) != "DL":
                            self.assign_shift(next_day, selected_for_night, "L")
                
                used_workers.append(selected_for_night)
                worker_pool = [w for w in worker_pool if w != selected_for_night]
            
            last_night_worker = selected_for_night
            day = day + 4


    def _assign_coperia_nights(self, start_from_day=1):
        """Marthita-focused night shifts for Coperia"""
        if start_from_day == 1:
            self.schedule.clear()
            self.total_hours.clear()
        
        day = start_from_day
        other_workers = [w for w in self.selected_workers if w != "Marthita" and not self.is_part_time(w)]
        used_workers = []
        cycle_day = 0  # Track where we are in the 6-day cycle

        while day <= self.days_in_month + self.preview_days:
            # Days 1-3: N shifts
            if cycle_day < 3:
                self.assign_shift(day, "Marthita", "N")
            # Day 4: LN shift
            elif cycle_day == 3:
                self.assign_shift(day, "Marthita", "LN")
            # Day 5: SL + random worker N
            elif cycle_day == 4:
                self.assign_shift(day, "Marthita", "SL")
                replacement_worker = random.choice(other_workers)
                self.assign_shift(day, replacement_worker, "N")
            # Day 6: L + different random worker N
            elif cycle_day == 5:
                self.assign_shift(day, "Marthita", "L")
                available_workers = [w for w in other_workers if not self.get_shift(self.selected_workers.index(w), day-1) == "N"]
                if available_workers:
                    second_replacement = random.choice(available_workers)
                    self.assign_shift(day, second_replacement, "N")
            
            cycle_day = (cycle_day + 1) % 6  # Reset to 0 after completing a cycle
            day += 1
    def assign_free_sundays(self, start_from_day=1):
        """Assign DL (free Sunday) shifts"""
        all_sundays = [day for day in range(1, self.days_in_month + 1) 
                      if calendar.weekday(self.year, self.month, day) == 6]
        
        if not all_sundays:
            return False
        
        dl_per_sunday = {day: [] for day in all_sundays}
        worker_dls = {worker: [] for worker in self.selected_workers if not self.is_part_time(worker)}
        
        # Count existing DLs
        for worker in self.selected_workers:
            if self.is_part_time(worker):
                continue
            worker_index = self.selected_workers.index(worker)
            for sunday in all_sundays:
                if self.get_shift(worker_index, sunday) == "DL":
                    dl_per_sunday[sunday].append(worker)
                    worker_dls[worker].append(sunday)
        
        # First pass - assign first DLs
        for worker in self.selected_workers:
            if self.is_part_time(worker):
                continue
            if len(worker_dls[worker]) >= 2:
                continue
                
            worker_index = self.selected_workers.index(worker)
            first_dl_assigned = False
            for i, sunday in enumerate(all_sundays):
                if i % 2 == 0 and len(dl_per_sunday[sunday]) < 7:
                    if self.get_shift(worker_index, sunday) not in ["N", "LN", "SL"]:
                        self.assign_shift(sunday, worker, "DL")
                        dl_per_sunday[sunday].append(worker)
                        worker_dls[worker].append(sunday)
                        first_dl_assigned = True
                        break
            
            # If couldn't assign on even Sundays, try odd ones
            if not first_dl_assigned:
                for i, sunday in enumerate(all_sundays):
                    if i % 2 == 1 and len(dl_per_sunday[sunday]) < 7:
                        if self.get_shift(worker_index, sunday) not in ["N", "LN", "SL"]:
                            self.assign_shift(sunday, worker, "DL")
                            dl_per_sunday[sunday].append(worker)
                            worker_dls[worker].append(sunday)
                            break
        
        # Second pass - assign second DLs
        for worker in self.selected_workers:
            if self.is_part_time(worker):
                continue
            if len(worker_dls[worker]) >= 2 or not worker_dls[worker]:
                continue
                
            first_dl = worker_dls[worker][0]
            first_dl_index = all_sundays.index(first_dl)
            
            # Try to maintain alternating pattern
            for offset in [2, -2, 3, -3]:
                target_index = first_dl_index + offset
                if 0 <= target_index < len(all_sundays):
                    target_sunday = all_sundays[target_index]
                    worker_index = self.selected_workers.index(worker)
                    if (len(dl_per_sunday[target_sunday]) < 7 and 
                        self.get_shift(worker_index, target_sunday) not in ["N", "LN", "SL"]):
                        self.assign_shift(target_sunday, worker, "DL")
                        dl_per_sunday[target_sunday].append(worker)
                        worker_dls[worker].append(target_sunday)
                        break
        
        # Get workers missing DLs for warnings
        missing_dls = [worker for worker, dls in worker_dls.items() if len(dls) < 2]
        return missing_dls

    def assign_l_days(self, start_from_day=1):
        """Assign L (free) days"""
        # First pass: Handle L days before SL
        for worker_index, worker in enumerate(self.selected_workers):
            if self.is_part_time(worker):
                continue
            for day in range(1, self.days_in_month + self.preview_days + 1):
                if self.get_shift(worker_index, day) == "SL":
                    # Check if needs L before SL
                    needs_l = True
                    for prev_day in range(max(1, day - 7), day):
                        if self.get_shift(worker_index, prev_day) in ["L", "DL"]:
                            needs_l = False
                            break
                    
                    if needs_l:
                        l_day = day - 7
                        if l_day > 0 and self.can_place_l_here(worker_index, l_day):
                            self.assign_shift(l_day, worker, "L")
        
        # Second pass: Handle consecutive working days
        for worker_index, worker in enumerate(self.selected_workers):
            if self.is_part_time(worker):
                continue
            consecutive_days = 0
            consecutive_start = 0
            for day in range(1, self.days_in_month + self.preview_days + 1):
                current_shift = self.get_shift(worker_index, day)
                
                if current_shift in ["L", "SL", "DL"]:
                    consecutive_days = 0
                    consecutive_start = day + 1
                else:
                    if consecutive_days == 0:
                        consecutive_start = day
                    consecutive_days += 1
                    if consecutive_days >= 6:
                        next_day = day + 1
                        if (next_day <= self.days_in_month + self.preview_days and 
                            self.can_place_l_here(worker_index, next_day)):
                            self.assign_shift(next_day, worker, "L")
                            consecutive_days = 0

        # Return workers with violations (7+ consecutive days)
        violations = []
        for worker_index, worker in enumerate(self.selected_workers):
            if self.is_part_time(worker):
                continue
            consecutive_days = 0
            for day in range(1, self.days_in_month + self.preview_days + 1):
                current_shift = self.get_shift(worker_index, day)
                if current_shift in ["L", "SL", "DL"]:
                    consecutive_days = 0
                else:
                    consecutive_days += 1
                    if consecutive_days >= 7 and worker not in violations:
                        violations.append(worker)
        return violations

    def assign_dayshifts(self, start_from_day=1):
        """Assign morning (M) and afternoon (T) shifts"""
        worker_shift_type = {}
        last_shift = {}  # Track the last non-free shift for each worker
        
        # Initialize shift types
        for worker in self.selected_workers:
            if self.is_part_time(worker):
                continue
            if worker != "Marianella":  # Keep original Marianella condition
                worker_shift_type[worker] = random.choice(['M', 'T'])
                last_shift[worker] = worker_shift_type[worker]
        
        # Assign shifts day by day
        for day in range(start_from_day, self.days_in_month + self.preview_days + 1):
            morning_count = afternoon_count = 0
            
            # Count existing shifts
            for worker in self.selected_workers:
                if self.is_part_time(worker):
                    continue
                if worker == "Marianella":
                    continue
                worker_index = self.selected_workers.index(worker)
                current_shift = self.get_shift(worker_index, day)
                if current_shift == 'M':
                    morning_count += 1
                elif current_shift == 'T':
                    afternoon_count += 1
            
            # Handle regular workers
            for worker in self.selected_workers:
                if self.is_part_time(worker):
                    continue
                if worker == "Marianella":
                    continue
                    
                worker_index = self.selected_workers.index(worker)
                
                # Skip if already has a shift
                if self.get_shift(worker_index, day) in ["N", "LN", "SL", "DL", "L", "M", "T"]:
                    continue
                
                # Check previous day and switch shift type after free days
                if day > 1:
                    prev_shift = self.get_shift(worker_index, day - 1)
                    if prev_shift in ["L", "SL", "DL"]:  # After a free day
                        # Switch from M to T or T to M
                        if last_shift.get(worker) == 'M':
                            worker_shift_type[worker] = 'T'
                        elif last_shift.get(worker) == 'T':
                            worker_shift_type[worker] = 'M'
                
                # STRICT T->M VALIDATION
                if day > 1 and self.get_shift(worker_index, day - 1) == "T":
                    self.assign_shift(day, worker, "T")
                    afternoon_count += 1
                    worker_shift_type[worker] = "T"
                    last_shift[worker] = "T"
                    continue
                
                # Regular shift assignment if not forced to T
                if morning_count >= 4:
                    worker_shift_type[worker] = 'T'
                elif afternoon_count >= 5:
                    worker_shift_type[worker] = 'M'
                
                self.assign_shift(day, worker, worker_shift_type[worker])
                last_shift[worker] = worker_shift_type[worker]
                if worker_shift_type[worker] == 'M':
                    morning_count += 1
                else:
                    afternoon_count += 1
            
            # Now handle Marianella separately (keep existing Marianella logic)
            if self.has_special_rule('marianella_javiera'):
                marianella_index = self.selected_workers.index("Marianella")
                javiera_index = self.selected_workers.index("Javiera")
                
                if not self.get_shift(marianella_index, day):
                    # First check T->T rule
                    if day > 1 and self.get_shift(marianella_index, day - 1) == "T":
                        self.assign_shift(day, "Marianella", "T")
                        continue
                    
                    # Follow Javiera's opposite schedule
                    javiera_shift = self.get_shift(javiera_index, day)
                    if javiera_shift == "M":
                        self.assign_shift(day, "Marianella", "T")
                    elif javiera_shift == "T":
                        if day > 1 and self.get_shift(marianella_index, day - 1) == "T":
                            self.assign_shift(day, "Marianella", "T")  # Keep T after T
                        else:
                            self.assign_shift(day, "Marianella", "M")
                    elif javiera_shift in ["N", "LN", "L", "SL", "DL"]:
                        if day > 1 and self.get_shift(marianella_index, day - 1) == "T":
                            self.assign_shift(day, "Marianella", "T")
                        else:
                            self.assign_shift(day, "Marianella", "M")
    
          
    def clear_schedule(self):
        """Clear the entire schedule"""
        self.schedule.clear()
        self.total_hours.clear()
        self.save_last_session()

    def can_place_l_here(self, worker_index, day):
        """Check if an L day can be placed on this day"""
        if self.get_shift(worker_index, day) in ["N", "LN", "SL", "DL", "L", "M", "T"]:
            return False
        
        # Check adjacent days
        if day > 1 and self.get_shift(worker_index, day - 1) == "L":
            return False
        if day < self.days_in_month and self.get_shift(worker_index, day + 1) == "L":
            return False
        
        return True

    def get_month_schedule(self):
        """Return the complete schedule in a structured format"""
        schedule_data = []
        for worker_index, worker in enumerate(self.selected_workers):
            worker_schedule = {
                'name': worker,
                'shifts': {},
                'total_hours': self.total_hours.get(worker_index, 0),
                'part_time': self.is_part_time(worker)
            }
            for day in range(1, self.days_in_month + self.preview_days + 1):
                shift = self.get_shift(worker_index, day)
                if shift:
                    worker_schedule['shifts'][day] = shift
            schedule_data.append(worker_schedule)
        return schedule_data
    
    def save_last_session(self):
        """Save current state to a JSON file"""
        session_data = {
            'current_group': self.current_group,
            'year': getattr(self, 'year', None),
            'month': getattr(self, 'month', None),
            'days_in_month': getattr(self, 'days_in_month', None),
            'preview_days': getattr(self, 'preview_days', None),
            'total_hours': self.total_hours
        }
        
        # Convert tuple keys to strings for JSON serialization
        schedule_dict = {}
        for key, value in self.schedule.items():
            schedule_dict[f"{key[0]},{key[1]}"] = value
        session_data['schedule'] = schedule_dict
        
        filename = f'autosave/last_session_{self.current_group}.json'
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_last_session(self):
        """Load last saved session if it exists"""
        filename = f'autosave/last_session_{self.current_group}.json'
        
        if not os.path.exists(filename):
            return
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            # Restore simple attributes
            self.current_group = session_data['current_group']
            if session_data['year'] and session_data['month']:
                self.year = session_data['year']
                self.month = session_data['month']
                self.days_in_month = session_data['days_in_month']
                self.preview_days = session_data['preview_days']
            
            # Restore schedule (converting string keys back to tuples)
            self.schedule = {}
            for key_str, value in session_data['schedule'].items():
                worker_idx, day = map(int, key_str.split(','))
                self.schedule[(worker_idx, day)] = value
                
            # Restore total hours
            self.total_hours = session_data['total_hours']
            
        except Exception as e:
            print(f"Error loading session: {e}")

    def transfer_to_next_month(self):
        """Transfer preview data to next month ONLY"""
        # Store preview data
        preview_data = {}
        
        # Get current month info
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        
        # Store the preview shifts for each worker
        for worker_index, worker in enumerate(self.selected_workers):
            worker_shifts = []
            for day in range(1, 8):  # Get 7 preview days
                preview_day = days_in_month + day
                shift = self.get_shift(worker_index, preview_day)
                worker_shifts.append(shift)
            preview_data[worker] = worker_shifts
        
        # Calculate next month and year
        next_month = self.month + 1
        next_year = self.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # Initialize the new month
        self.initialize_month(next_year, next_month)
        
        # Transfer the preview data to first week of new month
        for worker_index, worker in enumerate(self.selected_workers):
            for day in range(1, 8):
                shift = preview_data[worker][day - 1]
                if shift:
                    self.assign_shift(day, worker, shift)
        
        self.update_total_hours()
        
    def assign_night_shifts_after_transfer(self):
        """Special version of night shift assignment for after month transfer"""
        if self.current_group == 'sala':
            self._assign_sala_nights_after_transfer()
        elif self.current_group == 'cocina':
            self._assign_cocina_nights_after_transfer()
        elif self.current_group == 'coperia':
            self._assign_coperia_nights_after_transfer()

    def _assign_sala_nights_after_transfer(self):
        """Sala version of night shifts after transfer - handles 3 workers per cycle"""
        # Step 1: Identify and complete preview cycles
        preview_night_workers = []
        
        for worker_index, worker in enumerate(self.selected_workers):
            if self.is_part_time(worker):
                continue
            for day in range(1, 8):
                if self.get_shift(worker_index, day) == "N":
                    sequence = []
                    for check_day in range(day, 8):
                        check_shift = self.get_shift(worker_index, check_day)
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
                    break

        # Step 2: Complete existing night cycles
        latest_completion = 8
        workers_in_cycles = set()  # Keep track of all workers involved in night cycles
        
        for worker, start_day, completion_type in preview_night_workers:
            workers_in_cycles.add(worker)
            
            if completion_type == "needs_sl_l":
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_ln_sl_l":
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_n_ln_sl_l":
                self.assign_shift(start_day + 2, worker, "N")
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_nn_ln_sl_l":
                self.assign_shift(start_day + 1, worker, "N")
                self.assign_shift(start_day + 2, worker, "N")
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)

        # Step 3: Setup initial pool for new assignments
        worker_pool = [w for w in self.selected_workers if not self.is_part_time(w) and w not in workers_in_cycles]
        used_workers = []
        last_night_workers = []
        
        # Find SL day of last completed cycle to start new cycles
        day = latest_completion
        for check_day in range(latest_completion, 0, -1):
            sl_count = 0
            for worker_index, worker in enumerate(self.selected_workers):
                if self.get_shift(worker_index, check_day) == "SL":
                    sl_count += 1
            if sl_count == 3:  # Found where a group hits SL
                day = check_day
                break

        # Step 4: Continue with regular night shift assignment
        while day <= self.days_in_month + self.preview_days:
            # Replenish pool if needed
            if len(worker_pool) < 3:
                worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
                worker_pool = [w for w in worker_pool if w not in last_night_workers]  # Avoid back-to-back
                used_workers = []

            # Select workers for this cycle
            available_pool = [w for w in worker_pool if w not in last_night_workers]
            if len(available_pool) >= 3:
                selected_for_night = random.sample(available_pool, 3)
            else:
                selected_for_night = random.sample(worker_pool, 3)

            # Assign the cycle
            cycle_complete = True
            for day_offset in range(4):
                current_day = day + day_offset
                if current_day > self.days_in_month + self.preview_days:
                    cycle_complete = False
                    break
                
                for worker in selected_for_night:
                    shift_type = "N" if day_offset < 3 else "LN"
                    self.assign_shift(current_day, worker, shift_type)
            
            # Handle rest days after cycle
            if cycle_complete:
                rest_day = day + 4
                if rest_day <= self.days_in_month + self.preview_days:
                    for worker in selected_for_night:
                        self.assign_shift(rest_day, worker, "SL")
                        
                        next_day = rest_day + 1
                        if next_day <= self.days_in_month + self.preview_days:
                            worker_index = self.selected_workers.index(worker)
                            if self.get_shift(worker_index, next_day) != "DL":
                                self.assign_shift(next_day, worker, "L")
                
                used_workers.extend(selected_for_night)
                worker_pool = [w for w in worker_pool if w not in selected_for_night]
            
            last_night_workers = selected_for_night
            day = day + 4
    
    def _assign_cocina_nights_after_transfer(self):
        """Cocina version of nights after transfer - single worker cycles"""
        # Step 1: Identify preview cycles
        preview_night_workers = []
        
        for worker_index, worker in enumerate(self.selected_workers):
            if self.is_part_time(worker):  # Skip part-time workers
                continue
            for day in range(1, 8):
                if self.get_shift(worker_index, day) == "N":
                    # Count consecutive N/LN
                    sequence = []
                    for check_day in range(day, 8):
                        check_shift = self.get_shift(worker_index, check_day)
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
                    break

        # Step 2: Complete existing night cycles
        latest_completion = 8
        for worker, start_day, completion_type in preview_night_workers:
            if completion_type == "needs_sl_l":
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_ln_sl_l":
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_n_ln_sl_l":
                self.assign_shift(start_day + 2, worker, "N")
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)
            elif completion_type == "needs_nn_ln_sl_l":
                self.assign_shift(start_day + 1, worker, "N")
                self.assign_shift(start_day + 2, worker, "N")
                self.assign_shift(start_day + 3, worker, "LN")
                self.assign_shift(start_day + 4, worker, "SL")
                self.assign_shift(start_day + 5, worker, "L")
                latest_completion = max(latest_completion, start_day + 5)

        # Step 3: Continue with regular night assignment from latest completion
        day = latest_completion
        worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
        used_workers = []
        last_night_worker = None
        
        while day <= self.days_in_month + self.preview_days:
            if len(worker_pool) < 1:
                worker_pool = [w for w in self.selected_workers if not self.is_part_time(w)]
                used_workers = []
            
            available_pool = [w for w in worker_pool if w != last_night_worker]
            if len(available_pool) >= 1:
                selected_for_night = random.choice(available_pool)
            else:
                selected_for_night = random.choice(worker_pool)
            
            for day_offset in range(4):
                current_day = day + day_offset
                if current_day > self.days_in_month + self.preview_days:
                    break
                
                shift_type = "N" if day_offset < 3 else "LN"
                self.assign_shift(current_day, selected_for_night, shift_type)
            
            rest_day = day + 4
            if rest_day <= self.days_in_month + self.preview_days:
                self.assign_shift(rest_day, selected_for_night, "SL")
                next_day = rest_day + 1
                if next_day <= self.days_in_month + self.preview_days:
                    if self.get_shift(self.selected_workers.index(selected_for_night), next_day) != "DL":
                        self.assign_shift(next_day, selected_for_night, "L")
            
            used_workers.append(selected_for_night)
            worker_pool = [w for w in worker_pool if w != selected_for_night]
            last_night_worker = selected_for_night
            day = day + 4

    def _assign_coperia_nights_after_transfer(self):
        """Coperia version of nights after transfer - Marthita focused"""
        marthita_index = self.selected_workers.index("Marthita")
        other_workers = [w for w in self.selected_workers if w != "Marthita" and not self.is_part_time(w)]

        # Check if we end with exactly 2 Ns
        last_shifts = []
        for day in range(6, 8):  # Check days 6 and 7
            shift = self.get_shift(marthita_index, day)
            last_shifts.append(shift)

        if last_shifts == ["N", "N"]:
            # We found N N at the end - this is start of new cycle
            # Just need to add N LN SL L to complete it
            day = 8  # Start after preview week
            if day <= self.days_in_month + self.preview_days:
                self.assign_shift(day, "Marthita", "N")
                if day + 1 <= self.days_in_month + self.preview_days:
                    self.assign_shift(day + 1, "Marthita", "LN")
                    if day + 2 <= self.days_in_month + self.preview_days:
                        self.assign_shift(day + 2, "Marthita", "SL")
                        replacement_worker = random.choice(other_workers)
                        self.assign_shift(day + 2, replacement_worker, "N")
                        if day + 3 <= self.days_in_month + self.preview_days:
                            self.assign_shift(day + 3, "Marthita", "L")
                            available_workers = [w for w in other_workers if w != replacement_worker]
                            second_replacement = random.choice(available_workers)
                            self.assign_shift(day + 3, second_replacement, "N")
            day = day + 4  # Move to start of next cycle
        else:
            # Find where we are in current cycle and continue from there
            day = 8

        # Continue with regular cycles
        while day <= self.days_in_month + self.preview_days:
            # Regular 4-day night cycle
            for i in range(4):
                current_day = day + i
                if current_day > self.days_in_month + self.preview_days:
                    break
                shift_type = "N" if i < 3 else "LN"
                self.assign_shift(current_day, "Marthita", shift_type)
            
            # Rest days
            rest_day = day + 4
            if rest_day <= self.days_in_month + self.preview_days:
                self.assign_shift(rest_day, "Marthita", "SL")
                replacement_worker = random.choice(other_workers)
                self.assign_shift(rest_day, replacement_worker, "N")
                
                next_day = rest_day + 1
                if next_day <= self.days_in_month + self.preview_days:
                    self.assign_shift(next_day, "Marthita", "L")
                    available_workers = [w for w in other_workers if w != replacement_worker]
                    second_replacement = random.choice(available_workers)
                    self.assign_shift(next_day, second_replacement, "N")
            
            day = rest_day + 2

    
