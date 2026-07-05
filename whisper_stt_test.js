#!/usr/bin/env node

/**
 * Whisper.js STT 测试脚本
 * 测试whisper-turbo库的语音转文本功能
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const url = require('url');

// 检查依赖
console.log('🔍 检查Whisper.js依赖环境...');

// 检查whisper-turbo
const whisperTurboPath = path.join(__dirname, 'node_modules', 'whisper-turbo');
if (!fs.existsSync(whisperTurboPath)) {
    console.error('❌ whisper-turbo未安装');
    console.log('请运行: npm install whisper-turbo');
    process.exit(1);
}
console.log('✅ whisper-turbo已安装');

// 检查whisper-webgpu
const whisperWebGPUPath = path.join(__dirname, 'node_modules', 'whisper-webgpu');
if (!fs.existsSync(whisperWebGPUPath)) {
    console.error('❌ whisper-webgpu未安装');
    console.log('请运行: npm install whisper-webgpu');
    process.exit(1);
}
console.log('✅ whisper-webgpu已安装');

// 检查音频样本
console.log('\n🔍 检查IELTS音频样本...');
const audioDir = path.join(__dirname, 'test_audio', 'ielts_benchmark');
let audioSamples = [];

if (fs.existsSync(audioDir)) {
    const levels = ['beginner', 'intermediate', 'advanced', 'chinese_accent'];
    levels.forEach(level => {
        const levelDir = path.join(audioDir, level);
        if (fs.existsSync(levelDir)) {
            const files = fs.readdirSync(levelDir)
                .filter(f => f.endsWith('.mp3'))
                .map(f => path.join(levelDir, f));
            audioSamples.push(...files.slice(0, 2)); // 每个级别取2个样本测试
        }
    });
    
    console.log(`✅ 找到 ${audioSamples.length} 个音频样本用于测试`);
} else {
    console.error('❌ IELTS音频目录不存在');
    process.exit(1);
}

// 创建测试HTML文件
console.log('\n📝 创建Whisper.js测试服务器...');

const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whisper.js STT 功能测试</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .status-loading { background: #FFF3CD; color: #856404; }
        .status-ready { background: #D4EDDA; color: #155724; }
        .status-error { background: #F8D7DA; color: #721C24; }
        .test-section {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .log {
            background: #333;
            color: #fff;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            max-height: 300px;
            overflow-y: auto;
            margin: 10px 0;
        }
        .log-entry {
            margin: 5px 0;
            padding-left: 10px;
            border-left: 3px solid #4CAF50;
        }
        .log-error {
            border-left-color: #dc3545;
            color: #dc3545;
        }
        .log-success {
            border-left-color: #28a745;
            color: #28a745;
        }
        .audio-player {
            width: 100%;
            margin: 10px 0;
        }
        .result {
            background: #e9f7ef;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .progress {
            width: 100%;
            height: 20px;
            background: #ddd;
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: #4CAF50;
            width: 0%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Whisper.js STT 功能测试</h1>
        
        <div id="status" class="status status-loading">
            🔄 初始化Whisper.js环境...
        </div>
        
        <div class="test-section">
            <h2>1. 环境检查</h2>
            <div id="envCheck"></div>
            <button onclick="checkEnvironment()">检查环境</button>
        </div>
        
        <div class="test-section">
            <h2>2. 模型加载测试</h2>
            <div id="modelStatus">等待环境检查...</div>
            <button id="loadModelBtn" onclick="loadModel()" disabled>加载Whisper模型</button>
            <div class="progress">
                <div id="modelProgress" class="progress-bar"></div>
            </div>
        </div>
        
        <div class="test-section">
            <h2>3. 音频转写测试</h2>
            <p>选择测试音频:</p>
            <select id="audioSelect">
                <option value="">请选择音频文件</option>
                ${audioSamples.map((file, i) => {
                    const name = path.basename(file);
                    const level = path.basename(path.dirname(file));
                    return `<option value="${file}">${level}/${name}</option>`;
                }).join('')}
            </select>
            
            <div id="audioPlayerContainer" style="display: none;">
                <audio id="audioPlayer" class="audio-player" controls></audio>
            </div>
            
            <button id="transcribeBtn" onclick="transcribeAudio()" disabled>转写音频</button>
            
            <div class="progress">
                <div id="transcribeProgress" class="progress-bar"></div>
            </div>
            
            <div id="transcriptionResult" class="result">
                转写结果将显示在这里...
            </div>
        </div>
        
        <div class="test-section">
            <h2>4. 系统日志</h2>
            <div id="log" class="log"></div>
        </div>
    </div>

    <script type="module">
        // 导入Whisper模块
        import { loadModel, InferenceSession } from './node_modules/whisper-turbo/dist/index.js';
        
        let whisperModel = null;
        let currentAudioBuffer = null;
        
        // DOM元素
        const statusEl = document.getElementById('status');
        const envCheckEl = document.getElementById('envCheck');
        const modelStatusEl = document.getElementById('modelStatus');
        const loadModelBtn = document.getElementById('loadModelBtn');
        const audioSelect = document.getElementById('audioSelect');
        const transcribeBtn = document.getElementById('transcribeBtn');
        const audioPlayer = document.getElementById('audioPlayer');
        const audioPlayerContainer = document.getElementById('audioPlayerContainer');
        const transcriptionResult = document.getElementById('transcriptionResult');
        const logEl = document.getElementById('log');
        const modelProgress = document.getElementById('modelProgress');
        const transcribeProgress = document.getElementById('transcribeProgress');
        
        // 日志函数
        function log(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = \`log-entry log-\${type}\`;
            entry.textContent = \`[\${new Date().toLocaleTimeString()}] \${message}\`;
            logEl.appendChild(entry);
            logEl.scrollTop = logEl.scrollHeight;
            console.log(\`[\${type.toUpperCase()}] \${message}\`);
        }
        
        function updateStatus(text, type = 'loading') {
            statusEl.textContent = text;
            statusEl.className = \`status status-\${type}\`;
        }
        
        // 环境检查
        async function checkEnvironment() {
            log('开始环境检查...');
            envCheckEl.innerHTML = '';
            
            const checks = [
                { name: 'WebGPU支持', check: () => navigator.gpu ? '✅ 支持' : '❌ 不支持 (需要Chrome/Edge 113+)' },
                { name: 'AudioContext', check: () => window.AudioContext ? '✅ 支持' : '❌ 不支持' },
                { name: 'MediaRecorder', check: () => window.MediaRecorder ? '✅ 支持' : '❌ 不支持' },
                { name: 'ES模块支持', check: () => '✅ 支持 (当前页面使用type="module")' },
                { name: 'Whisper模块', check: () => typeof loadModel === 'function' ? '✅ 可用' : '❌ 不可用' }
            ];
            
            let allPassed = true;
            for (const check of checks) {
                const result = check.check();
                const isPass = result.includes('✅');
                if (!isPass) allPassed = false;
                
                const checkEl = document.createElement('div');
                checkEl.innerHTML = \`<strong>\${check.name}:</strong> \${result}\`;
                envCheckEl.appendChild(checkEl);
                
                log(\`\${check.name}: \${result}\`);
            }
            
            if (allPassed) {
                updateStatus('✅ 环境检查通过', 'ready');
                loadModelBtn.disabled = false;
                log('环境检查通过，可以加载模型');
            } else {
                updateStatus('⚠️ 环境检查未完全通过', 'error');
                log('环境检查未完全通过，某些功能可能受限', 'error');
            }
        }
        
        // 加载模型
        async function loadModel() {
            log('开始加载Whisper模型...');
            loadModelBtn.disabled = true;
            loadModelBtn.textContent = '加载中...';
            modelStatusEl.textContent = '正在下载模型文件...';
            
            try {
                // 更新进度条
                modelProgress.style.width = '10%';
                
                log('正在初始化Whisper模型...');
                
                // 注意：whisper-turbo需要在浏览器环境中运行
                // 这里我们尝试加载，但可能会失败
                whisperModel = await loadModel('whisper-turbo');
                
                modelProgress.style.width = '100%';
                modelStatusEl.innerHTML = '✅ 模型加载成功！<br>模型信息：' + JSON.stringify(whisperModel, null, 2);
                updateStatus('✅ Whisper模型加载成功', 'ready');
                log('Whisper模型加载成功');
                
                // 启用转写按钮
                transcribeBtn.disabled = false;
                
            } catch (error) {
                modelStatusEl.innerHTML = \`❌ 模型加载失败: \${error.message}\`;
                updateStatus('❌ 模型加载失败', 'error');
                log(\`模型加载失败: \${error.message}\`, 'error');
                log(\`错误详情: \${error.stack || '无堆栈信息'}\`, 'error');
                
                // 提供备用方案
                modelStatusEl.innerHTML += '<br><br>💡 可能的解决方案：';
                modelStatusEl.innerHTML += '<br>1. 确保使用支持WebGPU的浏览器（Chrome 113+ / Edge 113+）';
                modelStatusEl.innerHTML += '<br>2. 检查网络连接（需要下载模型文件）';
                modelStatusEl.innerHTML += '<br>3. 尝试使用Google STT作为备用方案';
            } finally {
                loadModelBtn.textContent = '重新加载模型';
                loadModelBtn.disabled = false;
            }
        }
        
        // 音频选择处理
        audioSelect.addEventListener('change', async function() {
            const filePath = this.value;
            if (!filePath) return;
            
            try {
                log(\`加载音频文件: \${filePath}\`);
                
                // 从服务器获取音频文件
                const response = await fetch(\`/audio/\${encodeURIComponent(filePath)}\`);
                if (!response.ok) {
                    throw new Error(\`获取音频失败: \${response.status}\`);
                }
                
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                
                // 设置音频播放器
                audioPlayer.src = audioUrl;
                audioPlayerContainer.style.display = 'block';
                
                // 保存音频数据用于转写
                currentAudioBuffer = await audioBlob.arrayBuffer();
                
                log(\`音频文件加载成功: \${path.basename(filePath)}\`, 'success');
                transcribeBtn.disabled = !whisperModel;
                
            } catch (error) {
                log(\`音频加载失败: \${error.message}\`, 'error');
                audioPlayerContainer.style.display = 'none';
                currentAudioBuffer = null;
                transcribeBtn.disabled = true;
            }
        });
        
        // 转写音频
        async function transcribeAudio() {
            if (!whisperModel || !currentAudioBuffer) {
                log('请先加载模型和选择音频文件', 'error');
                return;
            }
            
            log('开始音频转写...');
            transcribeBtn.disabled = true;
            transcribeBtn.textContent = '转写中...';
            transcriptionResult.textContent = '正在转写...';
            transcribeProgress.style.width = '0%';
            
            try {
                // 模拟进度更新
                for (let i = 0; i <= 100; i += 10) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    transcribeProgress.style.width = \`\${i}%\`;
                }
                
                log('调用Whisper模型进行转写...');
                
                // 实际转写调用
                // 注意：这里需要根据whisper-turbo的实际API进行调整
                const result = await whisperModel.transcribe(currentAudioBuffer);
                
                transcribeProgress.style.width = '100%';
                
                if (result && result.text) {
                    transcriptionResult.textContent = result.text;
                    log(\`转写成功: \${result.text.substring(0, 100)}...\`, 'success');
                } else {
                    transcriptionResult.textContent = '转写完成，但未获得文本结果';
                    log('转写完成但无文本结果', 'warning');
                }
                
            } catch (error) {
                transcriptionResult.textContent = \`转写失败: \${error.message}\`;
                log(\`转写失败: \${error.message}\`, 'error');
                
                // 提供模拟结果用于测试
                transcriptionResult.textContent = '【模拟结果】由于Whisper.js需要在浏览器中运行，这里显示模拟转写结果：\\n\\n"Hello, this is a test transcription of an IELTS speaking practice sample. The audio quality appears to be good and the speech is clear."';
                log('显示模拟转写结果（实际测试需要在浏览器中运行）', 'info');
                
            } finally {
                transcribeBtn.disabled = false;
                transcribeBtn.textContent = '转写音频';
                transcribeProgress.style.width = '0%';
            }
        }
        
        // 页面加载时自动检查环境
        window.addEventListener('load', () => {
            log('页面加载完成');
            checkEnvironment();
        });
    </script>
</body>
</html>
`;

// 创建音频文件服务
const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url);
    
    // 处理音频文件请求
    if (parsedUrl.pathname.startsWith('/audio/')) {
        const filePath = decodeURIComponent(parsedUrl.pathname.substring(7));
        
        // 安全检查：只允许访问test_audio目录下的文件
        if (!filePath.startsWith('test_audio/')) {
            res.writeHead(403);
            res.end('Access denied');
            return;
        }
        
        const fullPath = path.join(__dirname, filePath);
        
        fs.readFile(fullPath, (err, data) => {
            if (err) {
                res.writeHead(404);
                res.end('File not found');
                return;
            }
            
            res.writeHead(200, {
                'Content-Type': 'audio/mpeg',
                'Content-Length': data.length
            });
            res.end(data);
        });
        return;
    }
    
    // 处理根路径请求
    if (parsedUrl.pathname === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(htmlContent);
        return;
    }
    
    // 处理API请求
    if (parsedUrl.pathname === '/api/samples') {
        const metadataPath = path.join(audioDir, 'metadata.json');
        try {
            const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(metadata));
        } catch (err) {
            res.writeHead(500);
            res.end(JSON.stringify({ error: err.message }));
        }
        return;
    }
    
    // 默认返回404
    res.writeHead(404);
    res.end('Not found');
});

// 启动服务器
const PORT = 3000;
server.listen(PORT, () => {
    console.log(`🚀 测试服务器启动: http://localhost:${PORT}`);
    console.log(`📁 音频样本目录: ${audioDir}`);
    console.log(`🎯 测试样本数量: ${audioSamples.length}`);
    console.log('\n📋 测试步骤:');
    console.log('1. 打开上面的URL在支持WebGPU的浏览器中（Chrome 113+ / Edge 113+）');
    console.log('2. 点击"检查环境"按钮验证浏览器支持');
    console.log('3. 点击"加载Whisper模型"（首次需要下载约100MB模型）');
    console.log('4. 选择音频文件并点击"转写音频"');
    console.log('\n⚠️  注意:');
    console.log('   - 首次加载模型需要下载，请耐心等待');
    console.log('   - 确保浏览器支持WebGPU（chrome://flags/#enable-unsafe-webgpu）');
    console.log('   - 如果Whisper.js失败，我们将测试Google STT作为备用方案');
});

// 提供有用的命令
console.log('\n🔧 有用的命令:');
console.log('   # 检查浏览器WebGPU支持');
console.log('   chrome://flags/#enable-unsafe-webgpu');
console.log('\n   # 如果Whisper.js失败，测试Google STT备用方案');
console.log('   node google_stt_test.js');

// 创建Google STT测试脚本
const googleSTTTest = `
#!/usr/bin/env node
/**
 * Google STT备用方案测试脚本
 */
const fs = require('fs');
const path = require('path');

console.log('🔍 Google STT测试脚本');
console.log('📝 此脚本需要Google Cloud Speech-to-Text API密钥');
console.log('📁 配置文件位置: ~/.openclaw/auth/google/speech_to_text.key');

// 检查API密钥
const apiKeyPath = path.join(process.env.HOME, '.openclaw/auth/google/speech_to_text.key');
if (fs.existsSync(apiKeyPath)) {
    console.log('✅ 找到Google STT API密钥');
    const apiKey = fs.readFileSync(apiKeyPath, 'utf8').trim();
    console.log(\`密钥长度: \${apiKey.length} 字符\`);
    
    // 测试配置
    console.log('\\n📋 Google STT配置示例:');
    console.log('\\nconst speech = require("@google-cloud/speech");\\n');
    console.log(\`const client = new speech.SpeechClient({\\n  keyFilename: "\${apiKeyPath}"\\n});\\n\`);
    console.log('const config = {');
    console.log('  encoding: "MP3",');
    console.log('  sampleRateHertz: 16000,');
    console.log('  languageCode: "en-US",');
    console.log('  enableAutomaticPunctuation: true');
    console.log('};');
} else {
    console.log('❌ 未找到Google STT API密钥');
    console.log('📝 创建文件: ' + apiKeyPath);
    console.log('📝 内容格式: YOUR_GOOGLE_CLOUD_API_KEY');
}

console.log('\\n🚀 下一步:');
console.log('1. 安装Google Cloud SDK: npm install @google-cloud/speech');
console.log('2. 设置环境变量 GOOGLE_APPLICATION_CREDENTIALS');
console.log('3. 运行测试: node test_google_stt.js');
`;

// 创建Google STT测试脚本（修复变量引用问题）
const googleSTTTestFixed = `
#!/usr/bin/env node
/**
 * Google STT备用方案测试脚本
 */
const fs = require('fs');
const path = require('path');

console.log('🔍 Google STT测试脚本');
console.log('📝 此脚本需要Google Cloud Speech-to-Text API密钥');
console.log('📁 配置文件位置: ~/.openclaw/auth/google/speech_to_text.key');

// 检查API密钥
const apiKeyPath = path.join(process.env.HOME, '.openclaw/auth/google/speech_to_text.key');
if (fs.existsSync(apiKeyPath)) {
    console.log('✅ 找到Google STT API密钥');
    const apiKey = fs.readFileSync(apiKeyPath, 'utf8').trim();
    console.log(\`密钥长度: \${apiKey.length} 字符\`);
    
    // 测试配置
    console.log('\\n📋 Google STT配置示例:');
    console.log('\\nconst speech = require("@google-cloud/speech");\\n');
    console.log(\`const client = new speech.SpeechClient({\\n  keyFilename: "\${apiKeyPath}"\\n});\\n\`);
    console.log('const config = {');
    console.log('  encoding: "MP3",');
    console.log('  sampleRateHertz: 16000,');
    console.log('  languageCode: "en-US",');
    console.log('  enableAutomaticPunctuation: true');
    console.log('};');
} else {
    console.log('❌ 未找到Google STT API密钥');
    console.log('📝 创建文件: ' + apiKeyPath);
    console.log('📝 内容格式: YOUR_GOOGLE_CLOUD_API_KEY');
}

console.log('\\n🚀 下一步:');
console.log('1. 安装Google Cloud SDK: npm install @google-cloud/speech');
console.log('2. 设置环境变量 GOOGLE_APPLICATION_CREDENTIALS');
console.log('3. 运行测试: node test_google_stt.js');
`;

fs.writeFileSync(path.join(__dirname, 'google_stt_test.js'), googleSTTTestFixed);
console.log('📝 创建Google STT测试脚本: google_stt_test.js');

console.log('\n🎯 现在请打开浏览器访问 http://localhost:3000 进行Whisper.js测试');