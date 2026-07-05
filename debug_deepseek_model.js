#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const configPath = path.join(process.env.HOME, '.openclaw/openclaw.json');

function debugDeepseekModel() {
    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        console.log('🔍 Deepseek模型支持调试');
        console.log('='.repeat(50));
        
        // 1. 检查auth配置
        console.log('\n1. 🔑 认证配置:');
        const authProfiles = config.auth?.profiles || {};
        for (const [name, profile] of Object.entries(authProfiles)) {
            console.log(`   ${name}:`);
            console.log(`     provider: ${profile.provider}`);
            console.log(`     mode: ${profile.mode}`);
            if (profile.provider === 'deepseek') {
                console.log(`     ✅ 找到Deepseek provider配置`);
            }
        }
        
        // 2. 检查agents配置
        console.log('\n2. 🤖 Agent模型配置:');
        const xiaofengAgent = config.agents?.list?.find(a => a.id === 'xiaofeng');
        if (xiaofengAgent) {
            console.log(`   xiaofeng agent model: ${xiaofengAgent.model}`);
        }
        
        // 3. 检查默认模型配置
        console.log('\n3. ⚙️ 默认模型配置:');
        const defaults = config.agents?.defaults;
        if (defaults) {
            console.log(`   primary: ${defaults.model?.primary}`);
            console.log(`   fallbacks: ${JSON.stringify(defaults.model?.fallbacks)}`);
            
            console.log('\n   🏷️ 支持的模型列表:');
            const models = defaults.models || {};
            for (const [modelName, modelConfig] of Object.entries(models)) {
                console.log(`   - ${modelName}: ${JSON.stringify(modelConfig)}`);
            }
        }
        
        // 4. 检查OpenClaw版本和支持的provider
        console.log('\n4. 📦 OpenClaw版本信息:');
        try {
            const { execSync } = require('child_process');
            const versionCmd = process.env.NODE_PATH + '/node_modules/openclaw/package.json';
            
            const pkg = JSON.parse(fs.readFileSync('/Users/zhaoyuzhao/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/package.json', 'utf8'));
            console.log(`   版本: ${pkg.version}`);
            
            // 检查provider支持
            const providersPath = '/Users/zhaoyuzhao/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/dist/providers';
            console.log(`   Provider路径: ${providersPath}`);
            
            if (fs.existsSync(providersPath)) {
                console.log('   Provider文件:');
                const files = fs.readdirSync(providersPath).filter(f => f.endsWith('.js'));
                files.forEach(f => console.log(`   - ${f}`));
                
                // 检查是否有deepseek provider
                const hasDeepseek = files.some(f => f.includes('deepseek'));
                console.log(`   ${hasDeepseek ? '✅' : '❌'} Deepseek provider: ${hasDeepseek ? '存在' : '不存在'}`);
            }
            
        } catch (e) {
            console.log(`   无法获取版本信息: ${e.message}`);
        }
        
        // 5. 可能的模型名称问题
        console.log('\n5. 🤔 可能的模型名称问题:');
        console.log('   a) Deepseek直接调用格式: deepseek/deepseek-r1');
        console.log('   b) 通过OpenRouter格式: openrouter/deepseek/deepseek-r1');
        console.log('   c) Deepseek API支持的模型名称:');
        console.log('      - deepseek-chat');
        console.log('      - deepseek-coder');
        console.log('      - deepseek-r1');
        console.log('      需要验证具体支持哪些模型名称');
        
        // 6. 立即测试Deepseek API
        console.log('\n6. 🧪 Deepseek API测试:');
        const apiKey = process.env.DEEPSEEK_API_KEY;
        console.log(`   API密钥: ${apiKey ? '已设置 (长度:' + apiKey.length + ')' : '❌ 未设置'}`);
        
        if (apiKey) {
            console.log('   ℹ️  测试API调用可能由于网络或配置失败');
            console.log('      建议手动测试:');
            console.log(`      curl -X POST https://api.deepseek.com/chat/completions \\
                      -H "Authorization: Bearer ${apiKey.substring(0, 10)}..." \\
                      -H "Content-Type: application/json" \\
                      -d '{"model":"deepseek-r1","messages":[{"role":"user","content":"Hello"}]}'`);
        }
        
        // 7. 建议解决方案
        console.log('\n7. 💡 建议解决方案:');
        console.log('   ✅ 方案A (推荐): 使用openrouter/deepseek/deepseek-r1');
        console.log('       - 已经测试可用');
        console.log('       - 有fallback机制保障');
        console.log('       - 成本可能略高');
        
        console.log('   🚧 方案B: 修复deepseek provider');
        console.log('       - 确认Deepseek provider是否存在');
        console.log('       - 验证Deepseek API密钥有效性');
        console.log('       - 确认"deepseek-r1"是正确模型名称');
        
        console.log('   🔧 方案C: 临时切换模型');
        console.log(`      修改xiaofeng agent模型为: openrouter/deepseek/deepseek-r1`);
        
        return {
            hasDeepseekAuth: authProfiles.deepseek_bryson?.provider === 'deepseek',
            xiaofengModel: xiaofengAgent?.model,
            apiKeySet: !!apiKey,
            openclawVersion: '需要手动检查'
        };
        
    } catch (error) {
        console.error('❌ 调试失败:', error.message);
        return null;
    }
}

if (require.main === module) {
    const result = debugDeepseekModel();
    
    console.log('\n' + '='.repeat(50));
    console.log('📋 诊断结果:');
    console.log(`- Deepseek认证配置: ${result?.hasDeepseekAuth ? '✅' : '❌'}`);
    console.log(`- xiaofeng模型: ${result?.xiaofengModel}`);
    console.log(`- API密钥设置: ${result?.apiKeySet ? '✅' : '❌'}`);
    
    if (!result?.hasDeepseekAuth) {
        console.log('\n⚠️  问题: 缺少Deepseek认证配置');
        console.log('   需要确保auth.profiles中有deepseek_bryson配置');
    }
    
    console.log('\n🔧 修复脚本:');
    console.log('   node fix_deepseek_config.js');
}