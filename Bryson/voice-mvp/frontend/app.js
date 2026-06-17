// Bryson语音MVP - 前端JavaScript
// WebRTC连接和UI控制

class BrysonVoiceApp {
    constructor() {
        this.sessionId = null;
        this.websocket = null;
        this.peerConnection = null;
        this.localStream = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isConnected = false;
        this.isVoiceActive = false;
        this.startTime = null;
        this.volumeInterval = null;
        
        // DOM元素
        this.elements = {
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.querySelector('.status-text'),
            sessionId: document.getElementById('sessionId'),
            connectionStatus: document.getElementById('connectionStatus'),
            sessionDuration: document.getElementById('sessionDuration'),
            audioStatus: document.getElementById('audioStatus'),
            startVoiceBtn: document.getElementById('startVoiceBtn'),
            stopVoiceBtn: document.getElementById('stopVoiceBtn'),
            testAudioBtn: document.getElementById('testAudioBtn'),
            audioInput: document.getElementById('audioInput'),
            audioOutput: document.getElementById('audioOutput'),
            volumeBar: document.getElementById('volumeBar'),
            chatDisplay: document.getElementById('chatDisplay'),
            messageInput: document.getElementById('messageInput'),
            sendMessageBtn: document.getElementById('sendMessageBtn'),
            serverStatus: document.getElementById('serverStatus'),
            webrtcStatus: document.getElementById('webrtcStatus'),
            latencyValue: document.getElementById('latencyValue'),
            uptimeValue: document.getElementById('uptimeValue'),
            footerSessionId: document.getElementById('footerSessionId'),
            connectionModal: document.getElementById('connectionModal'),
            modalMessage: document.getElementById('modalMessage'),
            connectionProgress: document.getElementById('connectionProgress'),
            retryBtn: document.getElementById('retryBtn'),
            closeModalBtn: document.getElementById('closeModalBtn')
        };
        
        this.init();
    }

    async init() {
        // 获取会话ID
        this.getSessionId();
        
        // 初始化事件监听器
        this.setupEventListeners();
        
        // 检测音频设备
        await this.detectAudioDevices();
        
        // 更新会话信息
        this.updateSessionInfo();
        
        // 开始会话计时器
        this.startSessionTimer();
        
        // 检查服务器状态
        this.checkServerStatus();
        
        // 建立WebSocket连接
        this.connectWebSocket();
    }

    getSessionId() {
        const urlParams = new URLSearchParams(window.location.search);
        this.sessionId = urlParams.get('session') || 'test-' + Date.now().toString().slice(-6);
        this.elements.sessionId.textContent = this.sessionId;
        this.elements.footerSessionId.textContent = this.sessionId;
    }

    setupEventListeners() {
        // 语音控制按钮
        this.elements.startVoiceBtn.addEventListener('click', () => this.startVoiceChat());
        this.elements.stopVoiceBtn.addEventListener('click', () => this.stopVoiceChat());
        this.elements.testAudioBtn.addEventListener('click', () => this.testAudio());
        
        // 重试连接按钮
        this.elements.retryBtn.addEventListener('click', () => this.retryConnection());
        this.elements.closeModalBtn.addEventListener('click', () => this.closeModal());
        
        // 设备选择变化
        this.elements.audioInput.addEventListener('change', (e) => this.changeAudioDevice('input', e.target.value));
        this.elements.audioOutput.addEventListener('change', (e) => this.changeAudioDevice('output', e.target.value));
        
        // 消息发送
        this.elements.sendMessageBtn.addEventListener('click', () => this.sendTextMessage());
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
    }

    async detectAudioDevices() {
        try {
            // 获取麦克风权限
            await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // 枚举设备
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            const audioOutputs = devices.filter(device => device.kind === 'audiooutput');
            
            // 填充输入设备选择
            this.elements.audioInput.innerHTML = '';
            audioInputs.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `麦克风 ${this.elements.audioInput.children.length + 1}`;
                this.elements.audioInput.appendChild(option);
            });
            
            // 填充输出设备选择
            this.elements.audioOutput.innerHTML = '';
            audioOutputs.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `扬声器 ${this.elements.audioOutput.children.length + 1}`;
                this.elements.audioOutput.appendChild(option);
            });
            
            this.addChatMessage('system', '✅ 音频设备检测完成');
        } catch (error) {
            console.error('设备检测失败:', error);
            this.addChatMessage('system', '❌ 无法访问麦克风，请检查权限设置');
            this.showModal('需要麦克风权限', '请允许浏览器访问麦克风以使用语音功能');
        }
    }

    async connectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        this.updateStatus('connecting', '正在连接服务器...');
        this.showModal('建立连接', '正在连接到语音服务器...');
        this.updateProgress(30);
        
        try {
            // 构建WebSocket URL - 智能适配本地和远程环境
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            
            // 检查当前是否是通过LocalTunnel访问
            const isLocalTunnelAccess = window.location.hostname.includes('.loca.lt');
            let wsHost;
            
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                // 本地开发环境
                wsHost = 'localhost:8080';  // 修改为8080端口
            } else if (isLocalTunnelAccess) {
                // LocalTunnel环境：LocalTunnel会将WebSocket流量转发到相同端口
                // 所以我们应该使用与HTTP相同的host和端口
                wsHost = window.location.host;  // 使用相同的host，不需要指定端口
                console.log('✅ LocalTunnel环境，WebSocket使用相同host:', wsHost);
            } else {
                // 其他远程环境：假设WebSocket服务与HTTP同服务器
                wsHost = window.location.host;
            }
            
            const wsUrl = `${wsProtocol}//${wsHost}/ws/${this.sessionId}`;
            console.log(`构建WebSocket URL: ${wsUrl}, isLocalTunnel: ${isLocalTunnelAccess}`);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket连接已建立');
                this.updateStatus('connected', '已连接');
                this.updateProgress(70);
                this.elements.websocketStatus.textContent = '已连接';
                
                this.websocket.send(JSON.stringify({
                    type: 'ready',
                    session_id: this.sessionId
                }));
                
                this.addChatMessage('system', '✅ 服务器连接成功，准备就绪');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('消息解析失败:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket连接关闭:', event.code, event.reason);
                this.updateStatus('disconnected', '连接断开');
                this.elements.websocketStatus.textContent = '已断开';
                
                if (event.code !== 1000) {
                    this.addChatMessage('system', '❌ 连接已断开，正在尝试重连...');
                    setTimeout(() => this.connectWebSocket(), 3000);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                this.updateStatus('error', '连接错误');
                this.showModal('连接错误', '无法连接到服务器，请检查网络连接');
            };
            
            this.updateProgress(100);
            setTimeout(() => this.closeModal(), 1000);
            
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this.updateStatus('error', '连接失败');
            this.showModal('连接失败', '无法建立WebSocket连接: ' + error.message);
        }
    }

    handleWebSocketMessage(data) {
        console.log('收到消息:', data);
        
        switch (data.type) {
            case 'connection_established':
                this.addChatMessage('system', '🎉 WebRTC信令服务器已连接');
                this.isConnected = true;
                this.updateProgress(100);
                setTimeout(() => this.closeModal(), 500);
                break;
                
            case 'system':
                this.addChatMessage('system', data.message);
                break;
                
            case 'offer':
                // 处理WebRTC offer
                this.handleOffer(data.offer);
                break;
                
            case 'answer':
                // 处理WebRTC answer
                this.handleAnswer(data.answer);
                break;
                
            case 'candidate':
                // 处理ICE candidate
                this.handleCandidate(data.candidate);
                break;
                
            case 'heartbeat_ack':
                // 心跳响应
                this.updateLatency(Date.now() - data.timestamp);
                break;
        }
    }

    async startVoiceChat() {
        if (this.isVoiceActive) {
            this.addChatMessage('system', '⚠️ 语音对话已在进行中');
            return;
        }
        
        this.updateStatus('connected', '正在启动语音...');
        this.showModal('启动语音', '正在初始化音频设备和WebRTC连接...');
        this.updateProgress(20);
        
        try {
            // 获取麦克风权限
            const constraints = {
                audio: {
                    deviceId: this.elements.audioInput.value ? { exact: this.elements.audioInput.value } : undefined,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            };
            
            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.updateProgress(50);
            
            // 创建WebRTC连接
            await this.createPeerConnection();
            this.updateProgress(80);
            
            // 添加本地流
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // 开始音量监控
            this.startVolumeMonitor();
            
            this.isVoiceActive = true;
            this.elements.startVoiceBtn.disabled = true;
            this.elements.stopVoiceBtn.disabled = false;
            this.elements.audioStatus.textContent = '激活中';
            
            this.addChatMessage('system', '🎤 语音对话已开始！现在可以说话了');
            this.updateProgress(100);
            setTimeout(() => this.closeModal(), 500);
            
        } catch (error) {
            console.error('启动语音失败:', error);
            this.addChatMessage('system', '❌ 启动语音失败: ' + error.message);
            this.showModal('启动失败', '无法启动语音: ' + error.message);
        }
    }

    async createPeerConnection() {
        const configuration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        this.peerConnection = new RTCPeerConnection(configuration);
        
        // 事件监听器
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate && this.websocket) {
                this.websocket.send(JSON.stringify({
                    type: 'candidate',
                    candidate: event.candidate
                }));
            }
        };
        
        this.peerConnection.onconnectionstatechange = () => {
            console.log('WebRTC连接状态:', this.peerConnection.connectionState);
            this.elements.webrtcStatus.textContent = this.peerConnection.connectionState;
        };
        
        this.peerConnection.ontrack = (event) => {
            // 处理远程音频流
            const remoteAudio = document.createElement('audio');
            remoteAudio.srcObject = event.streams[0];
            remoteAudio.autoplay = true;
            
            // 添加到页面（隐藏播放）
            remoteAudio.style.display = 'none';
            document.body.appendChild(remoteAudio);
            
            this.addChatMessage('system', '🔊 收到远程音频流');
        };
        
        // 创建offer（在真实场景中，这应该由一端发起）
        if (!this.isConnected) {
            this.addChatMessage('system', '⚠️ 等待服务器连接建立...');
            return;
        }
    }

    async stopVoiceChat() {
        if (!this.isVoiceActive) return;
        
        this.isVoiceActive = false;
        this.elements.startVoiceBtn.disabled = false;
        this.elements.stopVoiceBtn.disabled = true;
        this.elements.audioStatus.textContent = '已停止';
        
        // 停止本地流
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        
        // 停止音量监控
        if (this.volumeInterval) {
            clearInterval(this.volumeInterval);
            this.volumeInterval = null;
            this.elements.volumeBar.style.width = '0%';
        }
        
        // 关闭WebRTC连接
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }
        
        this.addChatMessage('system', '⏹️ 语音对话已停止');
    }

    startVolumeMonitor() {
        if (!this.localStream) return;
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(this.localStream);
        const analyser = audioContext.createAnalyser();
        
        analyser.fftSize = 256;
        source.connect(analyser);
        
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        
        this.volumeInterval = setInterval(() => {
            analyser.getByteFrequencyData(dataArray);
            
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            
            const average = sum / dataArray.length;
            const volume = Math.min(100, Math.max(0, (average / 128) * 100));
            
            this.elements.volumeBar.style.width = volume + '%';
        }, 100);
    }

    async testAudio() {
        try {
            // 创建测试音频
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 440; // A4音
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            
            this.addChatMessage('system', '🔊 播放测试音频 (440Hz)');
            
            // 1秒后停止
            setTimeout(() => {
                oscillator.stop();
                this.addChatMessage('system', '✅ 测试音频播放完成');
            }, 1000);
            
        } catch (error) {
            console.error('测试音频失败:', error);
            this.addChatMessage('system', '❌ 测试音频失败: ' + error.message);
        }
    }

    sendTextMessage() {
        const text = this.elements.messageInput.value.trim();
        if (!text || !this.websocket) return;
        
        this.addChatMessage('user', text);
        
        this.websocket.send(JSON.stringify({
            type: 'text_message',
            text: text,
            timestamp: Date.now()
        }));
        
        this.elements.messageInput.value = '';
    }

    addChatMessage(sender, message) {
        const chatDiv = this.elements.chatDisplay;
        const messageDiv = document.createElement('div');
        
        messageDiv.className = sender === 'system' ? 'system-message' : 'user-message';
        
        if (sender === 'system') {
            messageDiv.innerHTML = `
                <i class="fas fa-robot"></i>
                <div class="message-content">
                    <strong>系统:</strong> ${message}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <i class="fas fa-user"></i>
                <div class="message-content">
                    <strong>您:</strong> ${message}
                </div>
            `;
        }
        
        chatDiv.appendChild(messageDiv);
        chatDiv.scrollTop = chatDiv.scrollHeight;
    }

    updateStatus(status, text) {
        this.elements.statusIndicator.className = `status-indicator ${status}`;
        this.elements.statusText.textContent = text;
        this.elements.connectionStatus.textContent = text;
    }

    updateSessionInfo() {
        if (this.sessionId) {
            this.elements.sessionId.textContent = this.sessionId;
        }
    }

    startSessionTimer() {
        this.startTime = Date.now();
        
        setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            this.elements.sessionDuration.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            this.elements.uptimeValue.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const data = await response.json();
                this.elements.serverStatus.textContent = '运行中';
                this.elements.serverStatus.style.color = '#2ecc71';
            } else {
                this.elements.serverStatus.textContent = '未响应';
                this.elements.serverStatus.style.color = '#e74c3c';
            }
        } catch (error) {
            this.elements.serverStatus.textContent = '检测失败';
            this.elements.serverStatus.style.color = '#e74c3c';
        }
        
        // 每30秒检查一次
        setTimeout(() => this.checkServerStatus(), 30000);
    }

    updateLatency(latency) {
        this.elements.latencyValue.textContent = `${latency} ms`;
        
        // 颜色编码
        if (latency < 100) {
            this.elements.latencyValue.style.color = '#2ecc71'; // 绿色
        } else if (latency < 300) {
            this.elements.latencyValue.style.color = '#f39c12'; // 黄色
        } else {
            this.elements.latencyValue.style.color = '#e74c3c'; // 红色
        }
    }

    showModal(title, message) {
        this.elements.modalMessage.textContent = message;
        this.elements.connectionModal.style.display = 'flex';
    }

    closeModal() {
        this.elements.connectionModal.style.display = 'none';
        this.elements.connectionProgress.style.width = '0%';
    }

    updateProgress(percent) {
        this.elements.connectionProgress.style.width = percent + '%';
    }

    retryConnection() {
        this.closeModal();
        this.connectWebSocket();
    }

    changeAudioDevice(type, deviceId) {
        console.log(`切换${type}设备到:`, deviceId);
        this.addChatMessage('system', `切换${type === 'input' ? '麦克风' : '扬声器'}设备`);
        
        // 如果正在语音通话中，需要重新连接
        if (this.isVoiceActive) {
            this.addChatMessage('system', '⚠️ 设备切换需要在下次通话时生效');
        }
    }

    // WebRTC处理函数（占位符）
    async handleOffer(offer) {
        console.log('收到offer:', offer);
        // 实现WebRTC offer处理
    }

    async handleAnswer(answer) {
        console.log('收到answer:', answer);
        // 实现WebRTC answer处理
    }

    async handleCandidate(candidate) {
        console.log('收到ICE candidate:', candidate);
        // 实现ICE candidate处理
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BrysonVoiceApp();
    console.log('Bryson语音MVP应用已启动');
});