document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const instanceSelect = document.getElementById('instance-select');
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const outputConsole = document.getElementById('output-console');
    const currentTime = document.getElementById('current-time');
    const simStatus = document.getElementById('sim-status') || document.createElement('span'); // Fallback if not in DOM
    const resultsContainer = document.getElementById('results-container');
    const algorithmSelect = document.getElementById('algorithm-select');    
    // Order metrics elements
    const completedOrders = document.getElementById('completed-orders');
    const unallocatedOrders = document.getElementById('unallocated-orders');
    const ongoingOrders = document.getElementById('ongoing-orders');

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

    // -------------- Tải danh sách thuật toán --------------
    // Tải thuật toán qua Socket.IO
    socket.emit('get_algorithms', {}, function(response) {
        if (response && response.algorithms) {
            populateAlgorithmSelect(response.algorithms);
        } else {
            // Fallback: Dùng fetch nếu socket không thành công
            fetchAlgorithms();
        }
    });

    function fetchAlgorithms() {
        fetch('/api/algorithms')
            .then(response => response.json())
            .then(data => {
                const algorithms = data.selected.length > 0 ? data.selected : data.all;
                populateAlgorithmSelect(algorithms);
            })
            .catch(error => {
                addErrorMessage(`Failed to load algorithms: ${error.message}`);
            });
    }

    function populateAlgorithmSelect(algorithms) {
        algorithmSelect.innerHTML = '<option value="">-- Select Algorithm --</option>';
        algorithms.forEach(algorithm => {
            const option = document.createElement('option');
            option.value = algorithm;
            option.textContent = algorithm;
            algorithmSelect.appendChild(option);
        });
    }

    // -------------- Xử lý các sự kiện từ server --------------

    socket.on('order_update', function(data) {
        console.log("Order update received:", data);
        
        // Cập nhật DOM elements
        if (completedOrders) 
            completedOrders.textContent = data.completed_orders;
        if (ongoingOrders) 
            ongoingOrders.textContent = data.ongoing_orders;
        if (unallocatedOrders) 
            unallocatedOrders.textContent = data.unallocated_orders;
        if (currentTime && data.current_time)
            currentTime.textContent = data.current_time;
    });

    // Cập nhật trạng thái mô phỏng
    socket.on('state_update', function(data) {
        // Debug: in ra state update
        console.log("State update received:", data);

        // Cập nhật thời gian hiện tại
        if (data.simulation_cur_time !== undefined) {
            currentTime.textContent = data.simulation_cur_time;
        }
        
        // Cập nhật trạng thái mô phỏng
        if (data.running !== undefined) {
            if (simStatus) simStatus.textContent = data.paused ? 'Paused' : (data.running ? 'Running' : 'Idle');
        }
        
        // Thêm debug cho các thông số đơn hàng
        console.log("Order metrics:", {
            completed: data.completed_orders,
            ongoing: data.ongoing_orders,
            unallocated: data.unallocated_orders
        });
    

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
    });

    // Xử lý cập nhật log
    socket.on('log_update', function(logs) {
        if (!Array.isArray(logs)) {
            console.error('log_update received invalid data:', logs);
            return;
        }
        logs.forEach(logEntry => {
            if (logEntry && logEntry.time && logEntry.message && logEntry.level) {
                addLogMessage(logEntry.time, logEntry.message, logEntry.level);
            } else {
                console.warn('Invalid log entry:', logEntry);
            }
        });
    });

    socket.on('simulation_started', function(data) {
        addSystemMessage(`Simulation started for ${data.instance_id} , algorithm: ${data.algorithm}`);
    });

    socket.on('simulation_paused', function(data) {
        addSystemMessage(`Simulation ${data.paused ? 'paused' : 'resumed'}`);
    });

    /* socket.on('simulation_completed', function(data) {
        addSystemMessage(`Simulation completed with score: ${data.score}`);
        if (data.results && data.results.length > 0) {
            resultsContainer.innerHTML = '';
            data.results.forEach((result, index) => {
                const p = document.createElement('p');
                p.textContent = `Instance ${index + 1}: ${result}`;
                resultsContainer.appendChild(p);
            });
        }
    }); */

    socket.on('simulation_completed', function(data) {
        console.log("Simulation completed data:", data);
        
        // Hiển thị kết quả đã được tạo sẵn cấu trúc
        document.querySelector('.result-basic-info').classList.remove('hidden');
        document.querySelector('.result-order-info').classList.remove('hidden');
        document.querySelector('.result-summary-info').classList.remove('hidden');
        
        // Cập nhật thông tin cơ bản
        document.getElementById('result-instance').textContent = data.instance_id || 'Unknown';
        document.getElementById('result-algorithm').textContent = data.algorithm || 'Unknown';
        document.getElementById('result-score').textContent = formatNumber(data.final_score || data.score);
        
        // Cập nhật thông tin đơn hàng
        document.getElementById('result-completed').textContent = ((data.completed_orders || 0) + (data.ongoing_orders || 0)) || 0;
        
        // Cập nhật thông tin tổng hợp
        document.getElementById('result-distance').textContent = formatNumber(data.total_distance);
        document.getElementById('result-time').textContent = formatNumber(data.sum_over_time);
        
        // Hiển thị thông tin chi tiết phương tiện nếu có
        if (data.vehicle_distances && Object.keys(data.vehicle_distances).length > 0) {
            document.querySelector('.result-vehicle-info').classList.remove('hidden');
            
            // Tạo bảng cho thông tin phương tiện
            const vehicleTableContainer = document.getElementById('vehicle-table-container');
            let vehicleTable = `
                <table class="vehicle-table">
                    <thead>
                        <tr>
                            <th>Vehicle ID</th>
                            <th>Distance</th>
                            <th>Nodes Visited</th>
                        </tr>
                    </thead>
                    <tbody>`;
            
            // Thêm dòng cho từng phương tiện
            for (const [vehicleId, distance] of Object.entries(data.vehicle_distances)) {
                const nodes = data.vehicle_nodes?.[vehicleId] || 'N/A';
                vehicleTable += `
                    <tr>
                        <td>${vehicleId}</td>
                        <td>${formatNumber(distance)}</td>
                        <td>${nodes}</td>
                    </tr>`;
            }
            
            vehicleTable += `
                    </tbody>
                </table>`;
            
            vehicleTableContainer.innerHTML = vehicleTable;
        } else {
            document.querySelector('.result-vehicle-info').classList.add('hidden');
        }
        
        // Thêm message vào console
        addSystemMessage(`Simulation completed with score: ${formatNumber(data.final_score || data.score)}`);
        
        // Cuộn đến kết quả
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    });

    // Hàm định dạng số
    function formatNumber(value) {
        if (value === undefined || value === null) return 'N/A';
        if (typeof value === 'number') {
            // Hiển thị 2 chữ số thập phân và loại bỏ .00 nếu có
            return value.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });
        }
        return value;
    }

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

        const algorithm = algorithmSelect.value;
        if (!algorithm) {
            addErrorMessage('Please select an algorithm first');
            return;
        }
        // Xóa console trước khi bắt đầu mô phỏng mới
        outputConsole.innerHTML = '';
        
        // Sử dụng socket để bắt đầu mô phỏng
        socket.emit('start_simulation', { instance_id: instanceId  , algorithm:algorithm }, function(response) {
            if (response && response.error) {
                addErrorMessage(`Start failed: ${response.error}`);
            } else {
                addSystemMessage(`Starting simulation for ${instanceId}...`);
            }
        });
    });
    // -------------- Hàm tiện ích --------------

    function addLogMessage(time, message, level = 'info') {
        const div = document.createElement('div');
        div.className = `console-line log-${level}`;
        div.textContent = `[${time}] ${level.toUpperCase()}: ${message}`;
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