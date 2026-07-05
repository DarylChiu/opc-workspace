#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const configPath = path.join(process.env.HOME, '.openclaw/openclaw.json');

function fixDeepseekConfig() {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        console.log('📋 当前配置:');
        console.log('- xiaofeng agent模型:', config.agents.list.find(a => a.id === 'xiaofeng')?.model);
        console.log('- 默认primary模型:', config.agents.defaults.model.primary);
        console.log('- 默认fallbacks:', config.agents.defaults.model.fallbacks?.join(', '));
        
        // 修复配置
        config.agents.defaults.model.primary = 'deepseek/deepseek-r1';
        config.agents.defaults.model.fallbacks = ['openrouter/deepseek/deepseek-r1'];
        
        // 确保模型配置中包含deepseek直连
        if (!config.agents.defaults.models['deepseek/deepseek-r1']) {
            config.agents.defaults.models['deepseek/deepseek-r1'] = {};
        }
        
        // 保存配置
        fs.writeFileSync(configPath, JSON.stringify(config, null, 4));
        
        console.log('\n✅ 配置已修复:');
        console.log('- 默认primary模型:', config.agents.defaults.model.primary);
        console.log('- 默认fallbacks:', config.agents.defaults.model.fallbacks.join(', '));
        
        // 验证配置
        const envKey = process.env.DEEPSEEK_API_KEY;
        console.log('\n🔑 Deepseek API环境变量:', envKey ? '已设置 (长度:' + envKey.length + ')' : '未设置');
        
        if (!envKey) {
            console.log('⚠️  警告: DEEPSEEK_API_KEY环境变量未设置');
            console.log('   请运行: export DEEPSEEK_API_KEY=你的密钥');
        }
        
        return true;
        
    } catch (error) {
        console.error('❌ 修复配置失败:', error.message);
        return false;
    }
}

function verifyApiKeys() {
    console.log('\n🔍 API密钥验证:');
    console.log('1. Deepseek API Key:', process.env.DEEPSEEK_API_KEY ? '已设置' : '未设置');
    console.log('2. OpenRouter API Key:', process.env.OPENROUTER_API_KEY ? '已设置' : '未设置');
    
    // 检查配置文件中的auth配置
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        const authProfiles = config.auth?.profiles || {};
        
        console.log('\n🎯 配置文件验证:');
        for (const [name, profile] of Object.entries(authProfiles)) {
            console.log(`- ${name}: ${profile.provider}/${profile.mode}`);
        }
    } catch (e) {
        console.log('❌ 读取配置文件失败:', e.message);
    }
}

function checkDeepseekModelSupport() {
    console.log('\n🤖 Deepseek直连模型验证:');
    console.log('1. 模型标识: deepseek/deepseek-r1');
    console.log('2. 格式说明: provider/modelName');
    console.log('3. 预期行为: 应该通过Deepseek API密钥直接调用');
    console.log('\n⚠️ 常见问题:');
    console.log('   - 如果出现"Unknown model"，可能是:');
    console.log('     * Deepseek不支持此模型名称');
    console.log('     * API密钥无效');
    console.log('     * 模型名称格式错误');
    console.log('     * OpenClaw版本不兼容');
}

if (require.main === module) {
    console.log('🔧 Deepseek配置修复工具\n');
    checkDeepseekModelSupport();
    verifyApiKeys();
    const success = fixDeepseekConfig();
    
    if (success) {
        console.log('\n🎉 执行下一步:');
        console.log('1. 重启Gateway: export PATH=$PATH:~/.nvm/versions/node/v24.14.0/bin && openclaw gateway restart');
        console.log('2. 验证状态: openclaw status');
        console.log('3. 检查session: session_status');
    } else {
        process.exit(1);
    }
}

module.exports = { fixDeepseekConfig };