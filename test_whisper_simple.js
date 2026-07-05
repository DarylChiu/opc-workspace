#!/usr/bin/env node

/**
 * Whisper.js 简单测试脚本
 * 测试whisper-turbo库是否能正常加载和运行
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 检查Whisper.js环境...');

// 检查node_modules中的whisper-turbo
const whisperPath = path.join(__dirname, 'node_modules', 'whisper-turbo');
if (!fs.existsSync(whisperPath)) {
    console.error('❌ whisper-turbo未安装');
    process.exit(1);
}

console.log('✅ whisper-turbo已安装');

// 检查package.json中的依赖
const packageJson = require('./package.json');
if (!packageJson.dependencies || !packageJson.dependencies['whisper-turbo']) {
    console.warn('⚠️  whisper-turbo不在package.json依赖中，但已安装');
}

// 尝试导入whisper-turbo
console.log('🔄 尝试导入whisper-turbo模块...');

try {
    // 注意：whisper-turbo可能需要在浏览器环境中运行
    // 这里我们先检查其结构
    const whisperModule = require('whisper-turbo');
    console.log('✅ whisper-turbo模块可以导入');
    console.log('模块导出:', Object.keys(whisperModule));
    
    // 检查是否有必需的导出
    const requiredExports = ['loadModel', 'transcribe', 'WhisperTurbo'];
    const missingExports = requiredExports.filter(exp => !whisperModule[exp]);
    
    if (missingExports.length > 0) {
        console.warn(`⚠️  缺少导出: ${missingExports.join(', ')}`);
    } else {
        console.log('✅ 所有必需导出都存在');
    }
    
} catch (error) {
    console.error('❌ 导入whisper-turbo失败:', error.message);
    console.log('📝 这可能是因为whisper-turbo需要在浏览器环境中运行');
}

// 检查音频样本文件
console.log('\n🔍 检查IELTS音频样本...');
const audioDir = path.join(__dirname, 'test_audio', 'ielts_benchmark');
if (fs.existsSync(audioDir)) {
    console.log('✅ IELTS音频目录存在');
    
    // 统计各等级样本数量
    const levels = ['beginner', 'intermediate', 'advanced', 'chinese_accent'];
    levels.forEach(level => {
        const levelDir = path.join(audioDir, level);
        if (fs.existsSync(levelDir)) {
            const files = fs.readdirSync(levelDir).filter(f => f.endsWith('.mp3'));
            console.log(`   ${level}: ${files.length}个样本`);
        } else {
            console.log(`   ${level}: 目录不存在`);
        }
    });
    
    // 检查元数据
    const metadataPath = path.join(audioDir, 'metadata.json');
    if (fs.existsSync(metadataPath)) {
        try {
            const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
            console.log(`✅ 元数据文件: ${metadata.total_samples}个样本`);
            console.log(`   生成时间: ${metadata.generated_at}`);
        } catch (err) {
            console.error('❌ 无法解析元数据文件:', err.message);
        }
    } else {
        console.log('❌ 元数据文件不存在');
    }
} else {
    console.log('❌ IELTS音频目录不存在');
    console.log('📝 请先运行音频生成器或等待子Agent完成');
}

// 创建简单的HTML测试文件
console.log('\n📝 创建Whisper.js测试环境...');
const htmlTest = `
<!DOCTYPE html>
<html>
<head>
    <title>Whisper.js 最小测试</title>
</head>
<body>
    <h1>Whisper.js 测试</h1>
    <p>这是一个最小化的Whisper.js测试页面。</p>
    
    <div>
        <input type="file" id="audioFile" accept="audio/*">
        <button onclick="testWhisper()">测试Whisper</button>
    </div>
    
    <div id="result"></div>
    
    <script type="module">
        import { loadModel } from './node_modules/whisper-turbo/dist/index.js';
        
        let whisperModel = null;
        
        async function testWhisper() {
            const fileInput = document.getElementById('audioFile');
            const resultDiv = document.getElementById('result');
            
            if (!fileInput.files[0]) {
                resultDiv.innerHTML = '<p style="color: red;">请先选择音频文件</p>';
                return;
            }
            
            resultDiv.innerHTML = '<p>加载Whisper模型...</p>';
            
            try {
                // 加载模型
                if (!whisperModel) {
                    whisperModel = await loadModel('whisper-turbo');
                    resultDiv.innerHTML = '<p>✅ 模型加载成功</p>';
                }
                
                // 读取音频文件
                const audioFile = fileInput.files[0];
                const audioBuffer = await audioFile.arrayBuffer();
                
                resultDiv.innerHTML += '<p>开始转写音频...</p>';
                
                // 转写音频
                const transcription = await whisperModel.transcribe(audioBuffer);
                
                resultDiv.innerHTML += \`<p>✅ 转写完成:</p>
                <textarea style="width: 100%; height: 100px;">\${transcription.text}</textarea>\`;
                
            } catch (error) {
                resultDiv.innerHTML = \`<p style="color: red;">错误: \${error.message}</p>\`;
                console.error(error);
            }
        }
        
        // 初始化检查
        window.addEventListener('load', () => {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<p>Whisper.js测试页面已加载</p>';
            
            // 检查WebGPU支持
            if (!navigator.gpu) {
                resultDiv.innerHTML += '<p style="color: orange;">⚠️ 浏览器不支持WebGPU</p>';
            } else {
                resultDiv.innerHTML += '<p>✅ 浏览器支持WebGPU</p>';
            }
        });
    </script>
</body>
</html>
`;

const testHtmlPath = path.join(__dirname, 'whisper_minimal_test.html');
fs.writeFileSync(testHtmlPath, htmlTest);
console.log(`✅ 创建最小测试页面: ${testHtmlPath}`);

console.log('\n📋 下一步:');
console.log('1. 打开 whisper_minimal_test.html 在支持WebGPU的浏览器中');
console.log('2. 选择一个音频文件进行测试');
console.log('3. 检查控制台是否有错误');
console.log('\n📋 完整测试建议:');
console.log('1. 使用Chrome/Edge浏览器（支持WebGPU）');
console.log('2. 确保有网络连接下载模型');
console.log('3. 首次运行需要下载~100MB模型文件');

// 提供服务器启动命令
console.log('\n🚀 启动本地服务器:');
console.log('   npx serve .');
console.log('或 python3 -m http.server 8080');
console.log('然后访问: http://localhost:8080/whisper_minimal_test.html');