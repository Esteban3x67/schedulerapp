// Global variables
let scheduleState = {
    'sala': null,
    'cocina': null,
    'coperia': null
};
let currentGroup = 'sala';
let isSelecting = false;
let selectedCells = new Set();
let currentSchedule = null;
let currentShift = null;

// Constants for group management
const GROUPS = {
    SALA: 'sala',
    COCINA: 'cocina',
    COPERIA: 'coperia'
};

const GROUP_NAMES = {
    [GROUPS.SALA]: 'Personal de Sala',
    [GROUPS.COCINA]: 'Cocina',
    [GROUPS.COPERIA]: 'Copería'
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Add group selector
    const groupSelect = document.createElement('select');
    groupSelect.id = 'groupSelect';
    groupSelect.className = 'p-2 border rounded mr-4';
    
    Object.entries(GROUP_NAMES).forEach(([value, name]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = name;
        groupSelect.appendChild(option);
    });

    document.getElementById('loadSessionBtn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/load-session'

                , {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    group: currentGroup 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the UI controls to match loaded data
                document.getElementById('monthSelect').value = data.month_data.month.toString();
                document.getElementById('yearSelect').value = data.month_data.year.toString();
                
                // Display the schedule
                displaySchedule(data.schedule, data.month_data);
                
                // Update stored state
                scheduleState[currentGroup] = {
                    schedule: data.schedule,
                    month: data.month_data.month.toString(),
                    year: data.month_data.year.toString()
                };
            } else {
                alert('Failed to load session: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load session. Please check the console for details.');
        }
    });
    // Insert before month select
    const monthSelect = document.getElementById('monthSelect');
    monthSelect.parentNode.insertBefore(groupSelect, monthSelect);
    
    // Add event listener for group changes
    groupSelect.addEventListener('change', handleGroupChange);
    // Add event listeners
    document.getElementById('generateBtn').addEventListener('click', generateSchedule);
    document.getElementById('transferBtn').addEventListener('click', transferPreview);
    document.getElementById('completeBtn').addEventListener('click', completeGenerate);

    // Add shift button listeners
    document.querySelectorAll('.shift-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Clear other button selections
            document.querySelectorAll('.shift-btn').forEach(b => 
                b.classList.remove('selected'));
            
            if (isSelecting) {
                applyShiftToSelected(btn.dataset.shift);
            } else {
                currentShift = btn.dataset.shift;
                btn.classList.add('selected');
            }
        });
    });

    document.getElementById('selectBtn').addEventListener('click', toggleSelectMode);
    document.getElementById('clearBtn').addEventListener('click', clearSelected);
    document.getElementById('deleteBtn').addEventListener('click', () => {
        if (selectedCells.size > 0) {
            applyShiftToSelected('');
        } else {
            currentShift = '';  // Set delete mode
            document.querySelectorAll('.shift-btn').forEach(b => 
                b.classList.remove('selected'));
        }
    });

    // Add export button
    const exportBtn = document.createElement('button');
    exportBtn.id = 'exportBtn';
    exportBtn.className = 'bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600';
    exportBtn.textContent = 'Export to Excel';
    exportBtn.addEventListener('click', exportToExcel);
    
    // Add import button and file input
    const importBtn = document.createElement('button');
    importBtn.id = 'importBtn';
    importBtn.className = 'bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600';
    importBtn.textContent = 'Import Excel';
    
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.id = 'excelFile';
    fileInput.accept = '.xlsx';
    fileInput.style.display = 'none';
    
    importBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    
    // Add buttons to the page
    const completeBtn = document.getElementById('completeBtn');
    completeBtn.parentNode.insertBefore(exportBtn, completeBtn.nextSibling);
    completeBtn.parentNode.insertBefore(importBtn, exportBtn.nextSibling);
    completeBtn.parentNode.insertBefore(fileInput, importBtn.nextSibling);

    // Add this line to the existing event listeners section in DOMContentLoaded
    document.getElementById('manageWorkersBtn').addEventListener('click', showModal);

    // Worker Management Functions
    async function manageWorker(action) {
        const password = document.getElementById('managerPassword').value;
        const worker = document.getElementById('workerName').value;
        const isFullTime = document.getElementById('workerType').value === 'full';
        
        if (!worker) {
            alert('Please enter a worker name');
            return;
        }
        
        if (!password) {
            alert('Please enter the manager password');
            return;
        }
        
        try {
            const response = await fetch('/api/workers/manage', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Basic ${password}`
                },
                body: JSON.stringify({
                    action,
                    group: currentGroup,
                    worker,
                    is_full_time: isFullTime
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert(`Worker successfully ${action}ed`);
                closeModal();
                // Regenerate schedule to reflect changes
                await generateSchedule();
            } else {
                alert(data.error || 'Operation failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to manage worker');
        }
    }

    function showModal() {
        document.getElementById('workerManagementModal').classList.remove('hidden');
    }

    function closeModal() {
        document.getElementById('workerManagementModal').classList.add('hidden');
        document.getElementById('managerPassword').value = '';
        document.getElementById('workerName').value = '';
        document.getElementById('workerType').value = 'full';
    }

    const addWorker = () => manageWorker('add');
    const removeWorker = () => manageWorker('remove');

}); // This is the end of DOMContentLoaded
async function generateSchedule() {
    const month = document.getElementById('monthSelect').value;
    const year = document.getElementById('yearSelect').value;
    
    try {
        const response = await fetch('api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                month: parseInt(month), 
                year: parseInt(year),
                group: currentGroup
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displaySchedule(data.schedule, data.month_data);
            scheduleState[currentGroup] = {
                schedule: data.schedule,
                month: month,
                year: year
            };
            updateConsecutiveDays();
            
            try {
                const verifyResponse = await fetch(`/api/verify-schedule?group=${currentGroup}`);
                const verifyData = await verifyResponse.json();
                if (verifyData.total_violations > 0) {
                    console.error('Schedule violations found:', verifyData.violations);
                }
            } catch (error) {
                console.error('Error verifying schedule:', error);
            }
        } else {
            alert('Failed to generate schedule: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to generate schedule. Please check the console for details.');
    }
}
function displaySchedule(schedule, monthData) {
    currentSchedule = schedule;  // Store schedule globally
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = ''; // Clear existing content
    
    // Create table
    const table = document.createElement('table');
    table.className = 'min-w-full border-collapse border';
    
    // Create header rows
    const thead = document.createElement('thead');
    
    // Add month name row
    const monthRow = document.createElement('tr');
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    const monthCell = document.createElement('th');
    monthCell.colSpan = monthData.days_in_month + 3 + monthData.preview_days; // +3 for worker column, separator, and hours
    monthCell.className = 'border p-2 text-center text-xl font-bold bg-gray-100';
    monthCell.textContent = `${monthNames[monthData.month - 1]} ${monthData.year}`;
    monthRow.appendChild(monthCell);
    thead.appendChild(monthRow);
    
    // Add day names row
    const dayNamesRow = document.createElement('tr');
    // Empty cell for worker names column
    dayNamesRow.appendChild(createHeaderCell('Workers'));
    
    // Function to get day name
    function getDayName(year, month, day) {
        const date = new Date(year, month - 1, day);
        const dayIndex = date.getDay();
        return ['D', 'L', 'M', 'X', 'J', 'V', 'S'][dayIndex];
    }
    
    // Add day names for current month
    for (let day = 1; day <= monthData.days_in_month; day++) {
        const dayCell = createHeaderCell(
            `${getDayName(monthData.year, monthData.month, day)}\n${day}`
        );
        dayCell.className = 'border p-2 text-center whitespace-pre-line';
        dayNamesRow.appendChild(dayCell);
    }
    
    // Add separator
    dayNamesRow.appendChild(createHeaderCell('║'));
    
    // Add preview days with day names
    const nextMonth = monthData.month === 12 ? 1 : monthData.month + 1;
    const nextYear = monthData.month === 12 ? monthData.year + 1 : monthData.year;
    
    for (let day = 1; day <= monthData.preview_days; day++) {
        const dayCell = createHeaderCell(
            `${getDayName(nextYear, nextMonth, day)}\n${day}`
        );
        dayCell.className = 'border p-2 text-center whitespace-pre-line';
        dayNamesRow.appendChild(dayCell);
    }
    
    // Add total hours header
    dayNamesRow.appendChild(createHeaderCell('Total Hours'));
    
    thead.appendChild(dayNamesRow);
    table.appendChild(thead);
    
    // Rest of the existing table creation code...
    const tbody = document.createElement('tbody');
    
    schedule.forEach((worker, index) => {
        const row = document.createElement('tr');
        row.className = index % 2 === 0 ? 'bg-gray-50' : 'bg-white';
        
        // Add worker name
        const nameCell = createCell(worker.name);
        row.appendChild(nameCell);
        
        // Add shifts for current month
        for (let day = 1; day <= monthData.days_in_month; day++) {
            const shift = worker.shifts[day] || '';
            const cell = createCell(shift, worker.name, day);
            setShiftColor(cell, shift);
            row.appendChild(cell);
        }
        
        // Add separator
        row.appendChild(createCell('║'));
        
        // Add preview days
        for (let day = 1; day <= monthData.preview_days; day++) {
            const actualDay = monthData.days_in_month + day;
            const shift = worker.shifts[actualDay] || '';
            const cell = createCell(shift, worker.name, actualDay);
            setShiftColor(cell, shift);
            row.appendChild(cell);
        }
        
        // Add total hours
        row.appendChild(createCell(worker.total_hours.toString()));
        
        tbody.appendChild(row);
    });
    
    // Add shift counters at the bottom (keep existing code)
    const shiftTypes = ['Morning', 'Afternoon', 'Night'];
    shiftTypes.forEach(type => {
        const row = document.createElement('tr');
        const labelCell = document.createElement('td');
        labelCell.textContent = `${type}:`;
        labelCell.className = 'border p-2 text-right font-bold';
        row.appendChild(labelCell);
        
        for (let day = 1; day <= monthData.days_in_month; day++) {
            const cell = document.createElement('td');
            cell.className = 'border p-2 text-center';
            cell.textContent = '0';
            row.appendChild(cell);
        }
        
        row.appendChild(createCell('║'));
        
        for (let day = 1; day <= monthData.preview_days; day++) {
            const cell = document.createElement('td');
            cell.className = 'border p-2 text-center';
            cell.textContent = '0';
            row.appendChild(cell);
        }
        
        row.appendChild(document.createElement('td'));
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);
    
    // Update all the counters and verifications
    updateConsecutiveDays();
    updateShiftCounters();
    updateDLVerification();
    updateWarnings();
}
function updateConsecutiveDays() {
    if (!currentSchedule) return;

    currentSchedule.forEach((worker) => {
        // First, handle part-time worker highlighting
        if (worker.part_time) {
            // Just highlight their name in purple
            const rows = document.querySelectorAll('tr');
            rows.forEach(row => {
                const firstCell = row.querySelector('td');
                if (firstCell && firstCell.textContent === worker.name) {
                    firstCell.style.backgroundColor = '#E9D8FD'; // Light purple
                }
            });
            return; // Skip rest of checks for part-time workers
        }

        let consecutive = 0;
        let hasViolation = false;
        
        // For full-time workers, continue with normal logic
        for (let day = 1; day <= 38; day++) {
            const cell = document.querySelector(`[data-cell-info="${worker.name}-${day}"]`);
            if (!cell) continue;

            const shiftDiv = cell.querySelector('.shift-display');
            const counterDiv = cell.querySelector('.counter-display');
            const shift = shiftDiv.textContent;
            
            if (shift === 'L' || shift === 'SL' || shift === 'DL') {
                consecutive = 0;
            } else {
                consecutive++;
            }
            
            // Show counter
            counterDiv.textContent = consecutive || '';
            
            // Handle violation highlighting
            if (consecutive >= 7) {
                shiftDiv.style.backgroundColor = '#EF4444'; // Bright red
                shiftDiv.style.color = 'white';
                hasViolation = true;
            } else {
                setShiftColor(cell, shift); // Reapply normal color
            }
        }

        // Handle name highlighting for violations
        const rows = document.querySelectorAll('tr');
        rows.forEach(row => {
            const firstCell = row.querySelector('td');
            if (firstCell && firstCell.textContent === worker.name) {
                if (hasViolation) {
                    firstCell.style.backgroundColor = '#EF4444';
                    firstCell.style.color = 'white';
                } else {
                    firstCell.style.backgroundColor = '';
                    firstCell.style.color = 'black';
                }
            }
        });
    });
}
function createHeaderCell(text) {
    const th = document.createElement('th');
    th.textContent = text;
    th.className = 'border p-2 text-center';
    return th;
}

function createCell(text, worker, day) {
    const td = document.createElement('td');
    td.className = 'border text-center shift-cell';

    if (!day && worker) {
        // This is a worker name cell
        td.className = 'worker-name';
        td.dataset.workerName = worker;
    } else {
        td.className = 'border text-center shift-cell';
    }
    
    // Create counter div (bottom layer)
    const counterDiv = document.createElement('div');
    counterDiv.className = 'counter-display';
    
    // Create shift div (top layer)
    const shiftDiv = document.createElement('div');
    shiftDiv.className = 'shift-display';
    shiftDiv.textContent = text;
    
    td.appendChild(counterDiv);
    td.appendChild(shiftDiv);
    
if (worker && day) {
    td.dataset.cellInfo = `${worker}-${day}`;
    td.addEventListener('click', async () => {
        if (isSelecting) {
            td.classList.toggle('cell-selected');
            if (selectedCells.has(td)) {
                selectedCells.delete(td);
            } else {
                selectedCells.add(td);
            }
        } else if (currentShift !== null) {
            const shiftDiv = td.querySelector('.shift-display');
            const oldShift = shiftDiv.textContent;
            
            try {
                await updateShift(worker, day, currentShift);
                // Only change display after successful API update
                if (currentShift === '') {
                    shiftDiv.textContent = '';
                } else {
                    shiftDiv.textContent = currentShift;
                }
                setShiftColor(td, currentShift);
                // Update counters right after shift change
                updateConsecutiveDays();
                updateShiftCounters();
                updateHourCount(worker);
            } catch (error) {
                // Revert on error
                shiftDiv.textContent = oldShift;
                setShiftColor(td, oldShift);
            }
        }
    });
}
    
    return td;
}

function setShiftColor(cell, shift) {
    const shiftDiv = cell.querySelector('.shift-display');
    // Remove all color classes
    shiftDiv.className = 'shift-display';
    
    if (!shift) {
        shiftDiv.style.backgroundColor = ''; // Clear background if no shift
        shiftDiv.style.color = 'black';  // Ensure text is black
        return;
    }
    
    // Set both the class and explicit colors
    switch (shift) {
        case 'N':
        case 'LN':
        case '10N':
        case '10LN':
            shiftDiv.style.backgroundColor = '#D3D3D3';
            shiftDiv.classList.add('shift-N');
            break;
        case 'L':
        case 'SL':
            shiftDiv.style.backgroundColor = '#FFFF99';
            shiftDiv.classList.add('shift-L');
            break;
        case 'DL':
            shiftDiv.style.backgroundColor = '#90EE90';
            shiftDiv.classList.add('shift-DL');
            break;
        case 'M':
        case 'M4':
            shiftDiv.style.backgroundColor = '#ADD8E6';
            shiftDiv.classList.add('shift-M');
            break;
        case 'T':
        case '2T':
            shiftDiv.style.backgroundColor = '#FFA07A';
            shiftDiv.classList.add('shift-T');
            break;
        case 'I':
            shiftDiv.style.backgroundColor = '#E6E6FA';
            shiftDiv.classList.add('shift-I');
            break;
    }
    shiftDiv.style.color = 'black';  // Always keep text black
}
function toggleSelectMode() {
    isSelecting = !isSelecting;
    const selectBtn = document.getElementById('selectBtn');
    
    if (isSelecting) {
        selectBtn.classList.add('bg-blue-700');
        selectBtn.textContent = 'Done';
        currentShift = null;
        document.querySelectorAll('.shift-btn').forEach(b => 
            b.classList.remove('selected'));
    } else {
        selectBtn.classList.remove('bg-blue-700');
        selectBtn.textContent = 'Select';
        clearSelected();
    }
}

function clearSelected() {
    selectedCells.forEach(cell => {
        cell.classList.remove('cell-selected');
    });
    selectedCells.clear();
}

async function applyShiftToSelected(shift) {
    if (selectedCells.size === 0) return;
    
    for (const cell of selectedCells) {
        const [worker, day] = cell.dataset.cellInfo.split('-');
        const shiftDiv = cell.querySelector('.shift-display');
        
        try {
            await updateShift(worker, parseInt(day), shift);
            shiftDiv.textContent = shift;
            setShiftColor(cell, shift);
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    clearSelected();
    toggleSelectMode();
    updateConsecutiveDays();
}
function updateShiftCounters() {
    const rows = document.querySelectorAll('#scheduleContainer tbody tr');
    const totalDays = 38; // 31 + 7 preview days
    
    for (let day = 1; day <= totalDays; day++) {
        let morning = 0, afternoon = 0, night = 0;
        
        // Count shifts from what's actually displayed in the table
        for (let i = 0; i < rows.length - 3; i++) { // -3 to exclude counter rows
            const cell = rows[i].children[day];
            const shiftDisplay = cell.querySelector('.shift-display');
            if (!shiftDisplay) continue;
            
            const shift = shiftDisplay.textContent;
            if (shift === 'M' || shift === 'M4') morning++;
            else if (shift === 'T' || shift === '2T') afternoon++;
            else if (['N', 'LN', '10N', '10LN'].includes(shift)) night++;
        }
        
        // Update counters
        const lastRows = [...rows].slice(-3);
        if (lastRows[0]) lastRows[0].children[day].textContent = morning;
        if (lastRows[1]) lastRows[1].children[day].textContent = afternoon;
        if (lastRows[2]) lastRows[2].children[day].textContent = night;
    }
}
async function updateShift(worker, day, shift) {
    try {
        const response = await fetch('/api/update-shift'

            , {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ worker, day, shift, group: currentGroup })
        });
        
        const data = await response.json();  
        
        if (data.success) {
            // Update the display first
            const cell = document.querySelector(`[data-cell-info="${worker}-${day}"]`);
            const shiftDiv = cell.querySelector('.shift-display');
            const oldShift = shiftDiv.textContent;
            
            if (shift === '') {
                shiftDiv.textContent = '';
            } else {
                shiftDiv.textContent = shift;
            }
            setShiftColor(cell, shift);

            // Then update the schedule data
            currentSchedule = data.schedule;
            
            // Basic updates
            updateHourCount(worker);  
            updateShiftCounters();    
            updateConsecutiveDays();
            updateWarnings(); // Add this line to update warnings whenever any shift changes

            
            // Only verify DLs if we're adding/removing a DL
            if (shift === 'DL' || oldShift === 'DL') {
                const dlResponse = await fetch(`/api/verify-dl-counts?group=${currentGroup}`);
                const dlData = await dlResponse.json();
                if (dlData.success) {
                    console.log('DL Status data:', dlData.dl_status);  // Debug log
                    
                    // Process each worker separately
                    const rows = document.querySelectorAll('tr');
                    rows.forEach(row => {
                        const firstCell = row.querySelector('td');
                        if (!firstCell) return;
                        
                        const workerName = firstCell.textContent;
                        const workerStatus = dlData.dl_status.find(s => s.worker === workerName);
                        
                        console.log(`Worker ${workerName}:`, workerStatus);  // Debug log
                        
                        if (workerStatus) {
                            // Only modify styling if this worker's status changed
                            if (workerStatus.needs_more) {
                                firstCell.classList.add('dl-violation');
                                firstCell.style.backgroundColor = '#22C55E';
                                firstCell.setAttribute('title', 
                                    `Only ${workerStatus.dl_count} DL assigned (Days: ${workerStatus.dl_days.join(', ')})`);
                            } else if (workerName === worker) {  // Only clear for the worker we're updating
                                firstCell.classList.remove('dl-violation');
                                firstCell.style.backgroundColor = '';
                                firstCell.removeAttribute('title');
                            }
                        }
                    });
                    
                    updateWarnings();
                }
            }
            
            // Update stored state after all changes
            scheduleState[currentGroup] = {
                schedule: currentSchedule,
                month: document.getElementById('monthSelect').value,
                year: document.getElementById('yearSelect').value
            };
            
            return true;
        } else {
            alert(data.error || 'Failed to update shift');
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to update shift. Please check the console for details.');
        return false;
    }
}
// Helper function to update DL status for a single worker
function updateDLVerificationForWorker(status) {
    const rows = document.querySelectorAll('tr');
    rows.forEach(row => {
        const firstCell = row.querySelector('td');
        if (firstCell && firstCell.textContent === status.worker) {
            firstCell.classList.remove('dl-violation');
            if (status.needs_more) {
                firstCell.classList.add('dl-violation');
                firstCell.style.backgroundColor = '#22C55E';  // Green
                firstCell.setAttribute('title', 
                    `Only ${status.dl_count} DL assigned (Days: ${status.dl_days.join(', ')})`);
            }
        }
    });
}
function updateHourCount(worker) {
    const workerIndex = currentSchedule.findIndex(w => w.name === worker);
    // Add 3 to account for month name row, day names row, and 0-based indexing
    const totalHoursCell = document.querySelectorAll('#scheduleContainer tbody tr')[workerIndex].lastElementChild;
    let totalHours = 0;
    
    // Get current month days
    const month = parseInt(document.getElementById('monthSelect').value);
    const year = parseInt(document.getElementById('yearSelect').value);
    const daysInMonth = new Date(year, month, 0).getDate();
    
    // Calculate hours only for current month (not preview days)
    for (let day = 1; day <= daysInMonth; day++) {
        const cell = document.querySelector(`[data-cell-info="${worker}-${day}"]`);
        if (!cell) continue;
        
        const shift = cell.querySelector('.shift-display').textContent;
        
        // Calculate hours based on shift type
        if (['M4', '2T', '10N', '10LN'].includes(shift)) {
            totalHours += 8.5;  // Extra hour shifts
        } else if (['N', 'LN', 'M', 'T', 'I'].includes(shift)) {
            totalHours += 7.5;  // Regular shifts
        }
        // L, SL, DL add 0 hours
    }
    
    // Update the display
    totalHoursCell.textContent = totalHours.toFixed(1);
    
    // Update the stored schedule data
    if (currentSchedule[workerIndex]) {
        currentSchedule[workerIndex].total_hours = totalHours;
    }
}
function updateDLVerification() {
    if (!currentSchedule) return;
    
    // Get current month and year from selects
    const month = parseInt(document.getElementById('monthSelect').value);
    const year = parseInt(document.getElementById('yearSelect').value);
    
    // Get Sundays in current month
    const daysInMonth = new Date(year, month, 0).getDate();
    const sundays = [];
    
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month - 1, day);
        if (date.getDay() === 0) { // 0 is Sunday
            sundays.push(day);
        }
    }

    currentSchedule.forEach((worker) => {
        // Skip part-time workers
        if (worker.part_time) {
            return;
        }

        let dlCount = 0;
        
        // Count DLs for each Sunday
        sundays.forEach(sunday => {
            const cell = document.querySelector(`[data-cell-info="${worker.name}-${sunday}"]`);
            if (cell) {
                const shiftDiv = cell.querySelector('.shift-display');
                if (shiftDiv.textContent === 'DL') {
                    dlCount++;
                }
            }
        });
        
        // Find worker's name cell and apply/maintain highlighting
        const rows = document.querySelectorAll('tr');
        rows.forEach(row => {
            const firstCell = row.querySelector('td');
            if (firstCell && firstCell.textContent === worker.name) {
                // Remove previous DL violation state
                firstCell.classList.remove('dl-violation');
                
                // If DLs are missing, reapply the violation state
                if (dlCount < 2) {
                    firstCell.classList.add('dl-violation');
                    firstCell.setAttribute('title', `Only ${dlCount} DL assigned`);
                    // Add green background explicitly
                    firstCell.style.backgroundColor = '#22C55E';
                } else {
                    // Only remove DL-specific styling
                    firstCell.classList.remove('dl-violation');
                    if (firstCell.getAttribute('title')?.includes('DL')) {
                        firstCell.removeAttribute('title');
                    }
                    // Don't reset backgroundColor if there's a consecutive days violation
                    if (!firstCell.style.backgroundColor.includes('EF4444')) {
                        firstCell.style.backgroundColor = '';
                    }
                }
            }
        });
    });
}

function getSundaysInMonth(year, month) {
    const sundays = [];
    const date = new Date(year, month - 1, 1);
    while (date.getMonth() === month - 1) {
        if (date.getDay() === 0) {
            sundays.push(date.getDate());
        }
        date.setDate(date.getDate() + 1);
    }
    return sundays;
}

function updateWarnings() {
    const warningsContainer = document.getElementById('warningsContainer');
    warningsContainer.innerHTML = ''; // Clear existing warnings
    
    if (!currentSchedule) return;
    
    const consecutiveViolations = [];
    const dlViolations = [];
    
    currentSchedule.forEach((worker) => {
        // Skip part-time workers
        if (worker.part_time) {
            return;
        }

        // Check consecutive days
        let consecutive = 0;
        let violationDays = [];
        
        for (let day = 1; day <= 38; day++) {
            const cell = document.querySelector(`[data-cell-info="${worker.name}-${day}"]`);
            if (!cell) continue;

            const shiftDiv = cell.querySelector('.shift-display');
            const shift = shiftDiv.textContent;
            
            if (!shift || shift === 'L' || shift === 'SL' || shift === 'DL') {
                consecutive = 0;
            } else {
                consecutive++;
                if (consecutive >= 7) {
                    violationDays.push(day);
                }
            }
        }
        
        if (violationDays.length > 0) {
            consecutiveViolations.push({
                worker: worker.name,
                days: violationDays
            });
        }

        // Check DLs
        const month = parseInt(document.getElementById('monthSelect').value);
        const year = parseInt(document.getElementById('yearSelect').value);
        const sundays = [];
        const daysInMonth = new Date(year, month, 0).getDate();
        
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month - 1, day);
            if (date.getDay() === 0) { // Sunday
                sundays.push(day);
            }
        }

        let dlCount = 0;
        sundays.forEach(sunday => {
            const cell = document.querySelector(`[data-cell-info="${worker.name}-${sunday}"]`);
            if (cell) {
                const shiftDiv = cell.querySelector('.shift-display');
                if (shiftDiv.textContent === 'DL') {
                    dlCount++;
                }
            }
        });
        
        if (dlCount < 2) {
            dlViolations.push({
                worker: worker.name,
                count: dlCount
            });
        }
    });
    
    // Create warning messages
    if (consecutiveViolations.length > 0) {
        consecutiveViolations.forEach(violation => {
            const warning = document.createElement('p');
            warning.className = 'text-red-600 font-bold mb-2';
            warning.textContent = `${violation.worker} has more than 6 consecutive days on days ${violation.days.join(', ')}`;
            warningsContainer.appendChild(warning);
        });
    }
    
    if (dlViolations.length > 0) {
        dlViolations.forEach(violation => {
            const warning = document.createElement('p');
            warning.className = 'text-green-600 font-bold mb-2';
            warning.textContent = `${violation.worker} has only ${violation.count} DL this month`;
            warningsContainer.appendChild(warning);
        });
    }
}

// Helper function to count DLs
function getDLCount(worker) {
    const month = parseInt(document.getElementById('monthSelect').value);
    const year = parseInt(document.getElementById('yearSelect').value);
    const daysInMonth = new Date(year, month, 0).getDate();
    let dlCount = 0;

    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month - 1, day);
        if (date.getDay() === 0) { // Sunday
            const cell = document.querySelector(`[data-cell-info="${worker.name}-${day}"]`);
            if (cell) {
                const shiftDiv = cell.querySelector('.shift-display');
                if (shiftDiv.textContent === 'DL') {
                    dlCount++;
                }
            }
        }
    }
    
    return dlCount;
}
async function transferPreview() {
    try {
        const response = await fetch('/api/transfer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                group: currentGroup 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the month dropdown to the next month
            const monthSelect = document.getElementById('monthSelect');
            let newMonth = parseInt(monthSelect.value) + 1;
            if (newMonth > 12) {
                newMonth = 1;
                // Optionally update year if needed
                const yearSelect = document.getElementById('yearSelect');
                yearSelect.value = (parseInt(yearSelect.value) + 1).toString();
            }
            monthSelect.value = newMonth.toString();
            
            displaySchedule(data.schedule, data.month_data);
            
            // Update the stored state
            scheduleState[currentGroup] = {
                schedule: data.schedule,
                month: newMonth.toString(),
                year: document.getElementById('yearSelect').value
            };
        } else {
            alert('Failed to transfer preview: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to transfer preview. Please check the console for details.');
    }
}
async function completeGenerate() {
    try {
        const response = await fetch('/api/complete-generate'

            , {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                group: currentGroup 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displaySchedule(data.schedule, data.month_data);
            
            // Update stored state
            scheduleState[currentGroup] = {
                schedule: data.schedule,
                month: data.month_data.month.toString(),
                year: data.month_data.year.toString()
            };
            
            // Rest of your existing verification code
            const verifyResponse = await fetch('/api/verify-schedule');
            const verifyData = await verifyResponse.json();
            if (verifyData.total_violations > 0) {
                console.error('Schedule violations found:', verifyData.violations);
            }
            
            // Verify DL counts
            const dlResponse = await fetch('/api/verify-dl-counts');
            const dlData = await dlResponse.json();
            if (dlData.success) {
                updateDLVerification();
            }
        } else {
            alert('Failed to complete schedule: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to complete schedule. Please check the console for details.');
    }
}

// Update the existing updateDLVerification function to use the new endpoint
async function updateDLVerification() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/verify-dl-counts');
        const data = await response.json();
        
        if (data.success) {
            data.dl_status.forEach(status => {
                const rows = document.querySelectorAll('tr');
                rows.forEach(row => {
                    const firstCell = row.querySelector('td');
                    if (firstCell && firstCell.textContent === status.worker) {
                        firstCell.classList.remove('dl-violation');
                        if (status.needs_more) {
                            firstCell.classList.add('dl-violation');
                            firstCell.setAttribute('title', 
                                `Only ${status.dl_count} DL assigned (Days: ${status.dl_days.join(', ')})`);
                        }
                    }
                });
            });
        }
    } catch (error) {
        console.error('Error verifying DLs:', error);
    }
}
async function exportToExcel() {
    try {
        const response = await fetch('/api/export-excel', {
            method: 'POST',
        });
        
        if (response.ok) {
            // Create blob from response
            const blob = await response.blob();
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'schedule.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            const error = await response.json();
            alert('Failed to export schedule: ' + error.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to export schedule. Please check the console for details.');
    }
}
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`/api/import-excel?group=${currentGroup}`
            , {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            // Store all schedules
            Object.keys(data.schedules).forEach(group => {
                scheduleState[group] = {
                    schedule: data.schedules[group].schedule,
                    month: data.schedules[group].month_data.month.toString(),
                    year: data.schedules[group].month_data.year.toString()
                };
            });

            // Display current group's schedule
            const currentGroupData = data.schedules[currentGroup];
            document.getElementById('monthSelect').value = currentGroupData.month_data.month.toString();
            document.getElementById('yearSelect').value = currentGroupData.month_data.year.toString();
            displaySchedule(currentGroupData.schedule, currentGroupData.month_data);
            
            // Clear the file input
            event.target.value = '';
        } else {
            alert('Failed to import schedule: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to import schedule. Please check the console for details.');
    }
}
// Handle group changes
async function handleGroupChange(event) {
    const newGroup = event.target.value;
    
    // Store current schedule state before switching
    if (currentSchedule) {
        scheduleState[currentGroup] = {
            schedule: currentSchedule,
            month: document.getElementById('monthSelect').value,
            year: document.getElementById('yearSelect').value
        };
    }
    
    // Update current group
    currentGroup = newGroup;
    
    // Load stored schedule if exists
    if (scheduleState[currentGroup]) {
        const storedState = scheduleState[currentGroup];
        document.getElementById('monthSelect').value = storedState.month;
        document.getElementById('yearSelect').value = storedState.year;
        displaySchedule(storedState.schedule, {
            month: parseInt(storedState.month),
            year: parseInt(storedState.year),
            days_in_month: new Date(storedState.year, storedState.month, 0).getDate(),
            preview_days: 7
        });
    } else {
        // If no stored schedule, generate a new one
        await generateSchedule();
    }
    
    // Update warnings
    updateWarnings();
}
