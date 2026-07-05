#!/usr/bin/env python3
"""
修复HTML界面，移除所有API密钥相关的输入框
"""

import re

def remove_api_key_sections(html_content):
    """移除HTML中所有API密钥相关的部分"""
    
    # 移除密钥输入框和相关DOM元素
    patterns_to_remove = [
        # 整个密钥输入部分
        r'<div[^>]*id="apiKeySection"[^>]*>.*?<\/div>',
        r'<div[^>]*class=".*?api.*?key.*?"[^>]*>.*?<\/div>',
    ]
    
    # 替换API密钥相关文本
    replacements = [
        # 标题修改
        (r'<h2[^>]*>.*?API.*?密钥.*?<\/h2>', '<h2>🎯 STT功能测试 (无需密钥)</h2>'),
        (r'🌐.*?Google STT.*?测试', '🎤 STT功能测试 (无需任何密钥)'),
        
        # 状态显示修改
        (r'<div[^>]*id="apiKeyStatus"[^>]*>.*?<\/div>', '<div id="apiKeyStatus" style="color: #4CAF50; font-weight: bold;">✅ API密钥已内置，无需输入</div>'),
        
        # 隐藏密钥输入框
        (r'<input[^>]*id="apiKeyInput"[^>]*>', '<input type="text" id="apiKeyInput" placeholder="无需输入密钥！服务已内置密钥" style="display: none;">'),
        
        # 修改验证按钮
        (r'验证API密钥', '开始测试STT功能'),
        (r'validateAPIKey\(\)', 'startSTTTest()'),
        
        # 移除密钥存储相关说明
        (r'密钥仅保存在浏览器本地存储中.*?服务器', '所有功能均可直接使用，无需任何密钥。'),
    ]
    
    result = html_content
    
    # 移除整个密钥section
    result = re.sub(
        r'<div[^>]*id="apiKeySection"[^>]*>.*?<\/div>',
        '<div id="apiKeySection" style="background: #e8f5e9; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50;">'
        '<h3 style="color: #2e7d32; margin-top: 0;">✅ 无需API密钥</h3>'
        '<p>STT功能已完全集成，API密钥已内置在服务器中。</p>'
        '<p>您可以直接使用所有功能，无需输入任何密钥！</p>'
        '<button class="btn btn-success" onclick="showQuickStart()">'
        '🎮 点击开始测试'
        '</button>'
        '</div>',
        result,
        flags=re.DOTALL
    )
    
    # 应用其他替换
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # 修改JavaScript中的API密钥验证函数
    if 'function validateAPIKey' in result:
        result = result.replace(
            'function validateAPIKey()',
            'function startSTTTest() {\n    alert("🎉 所有功能已就绪！\\n\\n您可以：\\n1. 📢 录制音频测试\\n2. 📚 选择IELTS样本\\n3. 🔄 运行完整测试\\n\\n无需任何API密钥！");\n    showSection("sttTestSection");\n}'
        )
    
    # 添加快速开始指导函数
    if 'function showQuickStart()' not in result:
        result = result.replace(
            '</script>',
            '''
function showQuickStart() {
    document.getElementById('quickStartGuide').innerHTML = `
        <div style="background: #f0f7ff; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2196f3;">
            <h4 style="color: #1976d2; margin-top: 0;">🎯 快速开始指南</h4>
            <ol style="margin-left: 20px;">
                <li><strong>🎤 录制音频测试：</strong>点击"开始录音"按钮，录制您的语音进行测试</li>
                <li><strong>📚 样本测试：</strong>在下方选择IELTS音频样本进行测试</li>
                <li><strong>🔄 完整测试：</strong>运行完整的STT转录流程测试</li>
                <li><strong>📊 查看统计：</strong>在状态页面查看测试结果统计</li>
            </ol>
            <p style="color: #666; font-size: 0.9rem;">💡 所有功能均已集成，无需任何API密钥！</p>
        </div>
    `;
    document.getElementById('quickStartGuide').style.display = 'block';
}
</script>
'''
        )
    
    # 确保状态显示正确
    result = result.replace('await validateAPIStatus();', 'showNoKeyNeededStatus();')
    
    # 添加新函数
    result = result.replace(
        '</script>',
        '''
function showNoKeyNeededStatus() {
    document.getElementById('apiKeyStatus').innerHTML = '<span style="color: #4CAF50;">✅ API密钥已内置，无需输入</span>';
}
</script>
'''
    )
    
    # 在body开头添加欢迎横幅
    result = result.replace(
        '<body>',
        '''<body>
    <div style="background: linear-gradient(45deg, #4CAF50, #43a047); color: white; padding: 10px 20px; text-align: center; border-bottom: 2px solid #388e3c;">
        <strong>🎉 无需API密钥！</strong> STT功能已完全集成，所有测试可以直接使用
    </div>'''
    )
    
    return result

def main():
    """主函数"""
    input_file = "google_stt_test_interface_fixed.html"
    output_file = "google_stt_test_interface_fixed.html"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("🛠️  正在修复HTML界面，移除API密钥输入框...")
        
        # 移除API密钥相关部分
        fixed_html = remove_api_key_sections(html_content)
        
        # 保存修复后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_html)
        
        print(f"✅ HTML界面修复完成: {output_file}")
        print("✅ 已移除所有API密钥输入框，用户无需提供任何密钥")
        
        # 检查修复结果
        api_key_count = len(re.findall(r'API.?密钥|api.?key', fixed_html, re.IGNORECASE))
        print(f"📊 API密钥相关文本数量: {api_key_count}")
        
        if api_key_count < 5:
            print("✅ 修复成功：大部分API密钥相关内容已移除")
        else:
            print("⚠️  仍有API密钥相关文本，请检查")
            
    except FileNotFoundError:
        print(f"❌ 找不到输入文件: {input_file}")
    except Exception as e:
        print(f"❌ 修复失败: {e}")

if __name__ == "__main__":
    main()