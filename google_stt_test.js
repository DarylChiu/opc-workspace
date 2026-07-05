
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
    console.log(`密钥长度: ${apiKey.length} 字符`);
    
    // 测试配置
    console.log('\n📋 Google STT配置示例:');
    console.log('\nconst speech = require("@google-cloud/speech");\n');
    console.log(`const client = new speech.SpeechClient({\n  keyFilename: "${apiKeyPath}"\n});\n`);
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

console.log('\n🚀 下一步:');
console.log('1. 安装Google Cloud SDK: npm install @google-cloud/speech');
console.log('2. 设置环境变量 GOOGLE_APPLICATION_CREDENTIALS');
console.log('3. 运行测试: node test_google_stt.js');
