document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const instanceSelect = document.getElementById('instance-select');
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const outputConsole = document.getElementById('output-console');
    const currentTime = document.getElementById('current-time');
    const simStatus = document.getElementById('sim-status') || document.createElement('span'); // Fallback if not in DOM
    const resultsContainer = document.getElementById('results-container');
    
    // Order metrics elements
    const completedOrders = document.getElementById('completed-orders');
    const unallocatedOrders = document.getElementById('unallocated-orders');
    const ongoingOrders = document.getElementById('ongoing-orders');
    const failedOrders = document.getElementById('failed-orders');

    // Khởi tạo Socket.IO với auto reconnect
    const socket = io('http://localhost:5000', {
        reconnectionAttempts: 5,
        timeout: 10000,
        transports: ['websocket', 'polling']
    });

    // -------------- Xử lý kết nối Socket.IO --------------

    socket.on('connect', function() {
        addSystemMessage('Connected to server');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', function(reason) {
        addSystemMessage(`Disconnected from server: ${reason}`);
        updateConnectionStatus(false);
    });

    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addErrorMessage(`Connection error: ${error.message}`);
    });

    socket.on('reconnect_attempt', (attemptNumber) => {
        addSystemMessage(`Attempting to reconnect (${attemptNumber})...`);
    });

    socket.on('reconnect', (attemptNumber) => {
        addSystemMessage(`Reconnected after ${attemptNumber} attempts`);
        updateConnectionStatus(true);
    });

    socket.on('reconnect_error', (error) => {
        addErrorMessage(`Failed to reconnect: ${error.message}`);
    });

    socket.on('reconnect_failed', () => {
        addErrorMessage('Failed to reconnect after multiple attempts');
    });

    // -------------- Tải danh sách instances --------------

    // Tải instances qua Socket.IO
    socket.emit('get_instances', {}, function(response) {
        if (response && response.instances) {
            populateInstanceSelect(response.instances);
        } else {
            // Fallback: Dùng fetch nếu socket không thành công
            fetchInstances();
        }
    });

    function fetchInstances() {
        fetch('/api/instances')
            .then(response => response.json())
            .then(data => {
                const instances = data.selected.length > 0 ? data.selected : data.all;
                populateInstanceSelect(instances);
            })
            .catch(error => {
                addErrorMessage(`Failed to load instances: ${error.message}`);
            });
    }

    function populateInstanceSelect(instances) {
        instanceSelect.innerHTML = '<option value="">-- Select Instance --</option>';
        instances.forEach(instance => {
            const option = document.createElement('option');
            option.value = instance;
            option.textContent = instance;
            instanceSelect.appendChild(option);
        });
    }

    // -------------- Xử lý các sự kiện từ server --------------

    // Cập nhật trạng thái mô phỏng
    socket.on('state_update', function(data) {
        // Cập nhật thời gian hiện tại
        if (data.current_time !== undefined) {
            currentTime.textContent = data.current_time;
        }
        
        // Cập nhật trạng thái mô phỏng
        if (data.running !== undefined) {
            if (simStatus) simStatus.textContent = data.paused ? 'Paused' : (data.running ? 'Running' : 'Idle');
        }
        
        // Cập nhật trạng thái nút
        startBtn.disabled = data.running;
        pauseBtn.disabled = !data.running;
        pauseBtn.textContent = data.paused ? 'Resume' : 'Pause';
        
        // Cập nhật kết quả
        if (data.scores && data.scores.length > 0) {
            resultsContainer.innerHTML = '';
            data.scores.forEach((score, index) => {
                const p = document.createElement('p');
                p.textContent = `Instance ${index + 1}: ${score}`;
                resultsContainer.appendChild(p);
            });
        }

        // Cập nhật số liệu đơn hàng
        if (data.completed_orders !== undefined && completedOrders) 
            completedOrders.textContent = data.completed_orders;
        if (data.unallocated_orders !== undefined && unallocatedOrders) 
            unallocatedOrders.textContent = data.unallocated_orders;
        if (data.ongoing_orders !== undefined && ongoingOrders) 
            ongoingOrders.textContent = data.ongoing_orders;
        if (data.failed_orders !== undefined && failedOrders) 
            failedOrders.textContent = data.failed_orders;
    });

    // Xử lý cập nhật log
    socket.on('log_update', function(logEntry) {
        addLogMessage(logEntry.time, logEntry.message, logEntry.level);
    });

    socket.on('simulation_started', function(data) {
        addSystemMessage(`Simulation started for ${data.instance_id}`);
    });

    socket.on('simulation_paused', function(data) {
        addSystemMessage(`Simulation ${data.paused ? 'paused' : 'resumed'}`);
    });

    socket.on('simulation_completed', function(data) {
        addSystemMessage(`Simulation completed with score: ${data.score}`);
    });

    socket.on('simulation_error', function(data) {
        addErrorMessage(`Simulation error: ${data.error}`);
    });

    // -------------- Xử lý sự kiện nút bấm --------------

    // Xử lý nút Start
    startBtn.addEventListener('click', function() {
        const instanceId = instanceSelect.value;
        if (!instanceId) {
            addErrorMessage('Please select an instance first');
            return;
        }
        
        // Xóa console trước khi bắt đầu mô phỏng mới
        outputConsole.innerHTML = '';
        
        // Sử dụng socket để bắt đầu mô phỏng
        socket.emit('start_simulation', { instance_id: instanceId }, function(response) {
            if (response && response.error) {
                addErrorMessage(`Start failed: ${response.error}`);
            } else {
                addSystemMessage(`Starting simulation for ${instanceId}...`);
            }
        });
    });

    // Xử lý nút Pause
    pauseBtn.addEventListener('click', function() {
        socket.emit('pause_simulation', {}, function(response) {
            if (response && response.error) {
                addErrorMessage(`Pause/resume failed: ${response.error}`);
            }
        });
    });

    // -------------- Hàm tiện ích --------------

    function addLogMessage(time, message, level = 'info') {
        const div = document.createElement('div');
        div.className = `console-line log-${level}`;
        div.textContent = `[${time}] ${message}`;
        outputConsole.appendChild(div);
        scrollToBottom();
    }

    function addSystemMessage(message) {
        const time = new Date().toTimeString().split(' ')[0];
        const div = document.createElement('div');
        div.className = 'console-line system-message';
        div.textContent = `[${time}] SYSTEM: ${message}`;
        outputConsole.appendChild(div);
        scrollToBottom();
    }

    function addErrorMessage(message) {
        const time = new Date().toTimeString().split(' ')[0];
        const div = document.createElement('div');
        div.className = 'console-line error-message';
        div.textContent = `[${time}] ERROR: ${message}`;
        outputConsole.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        outputConsole.scrollTop = outputConsole.scrollHeight;
    }

    function updateConnectionStatus(connected) {
        startBtn.disabled = !connected;
        if (!connected) {
            pauseBtn.disabled = true;
        }
    }
});