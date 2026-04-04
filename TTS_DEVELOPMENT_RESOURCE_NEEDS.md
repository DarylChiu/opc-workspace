# TTS语音交互功能开发 - 资源协调清单 (Google TTS方案)

## 项目批准状态
**批准时间**: 2026-03-28 22:02 (GMT+7)  
**调整时间**: 2026-03-28 22:29 (切换至Google TTS)
**批准人**: Daryl (ou_7f871e4d921c449ee8a5f77b38bf6ff9)
**汇报机制**: 每小时进度报告一次
**成本追踪**: API调用成本纳入开发成本记录

## 核心技术需求清单 (Google TTS版)

### 1. API访问资源 (最紧急)
| 资源类型 | 用途 | 状态 | 协调需求 |
|----------|------|------|----------|
| **Google Cloud API密钥** | 访问Text-to-Speech API | ❌ 不可用 | **立即需要**: 创建Google Cloud项目并获取API密钥 |
| **服务账号JSON密钥** | 身份验证凭证 | ❌ 不可用 | 需要下载service account key JSON文件 |
| **预算控制** | 每月免费配额监控 | ✅ 免费 | 每月100万字符免费配额，远超$0.5/月需求 |

**Google Cloud协调步骤**:
1. **访问Google Cloud Console**: https://console.cloud.google.com
2. **创建新项目**: 项目名称 `ielts-tts-2026`
3. **启用Text-to-Speech API**: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
4. **创建服务账号**: 名称 `ielts-tts-service`
5. **生成JSON密钥**: 下载密钥文件
6. **存储到**: `~/.openclaw/auth/google/ielts_tts_2026.json`

### 2. 系统环境资源
| 资源类型 | 用途 | 状态 | 协调需求 |
|----------|------|------|----------|
| **音频播放环境** | 本地播放生成的语音文件 | ✅ 已验证 | macOS `afplay`命令可用 |
| **存储空间** | 缓存生成的音频文件 | ✅ 充足 | workspace目录有足够空间 |
| **网络访问** | 调用Google Cloud API | ✅ 正常 | 需要访问Google Cloud服务 |

### 3. 开发基础设施
| 资源类型 | 用途 | 状态 | 协调需求 |
|----------|------|------|----------|
| **Python环境** | TTS集成脚本 | ✅ 就绪 | Python 3.12可用，需安装`google-cloud-texttospeech` |
| **音频库** | MP3文件处理 | ⚠️ 需安装 | 需要 `pip install pydub` |
| **进度监控** | 每小时汇报 | 🔄 待实现 | 需要创建自动汇报脚本 |

## Google TTS技术优势

### 📊 配额对比:
- **OpenAI TTS**: $0.5/月 = 33,333字符
- **Google TTS**: **免费配额** = 1,000,000字符/月 (30倍于需求)

### 🎯 质量参数:
- **语音选择**: 100+种语音，30+种语言
- **神经网络语音**: WaveNet技术，更自然
- **发音控制**: SSML支持，精确控制语调、速度
- **多格式**: MP3、WAV、OGG_OPUS等

### 💰 成本效益:
- **完全免费**在配额内 (100万字符足够每日练习)
- **超出后成本**: $4.00/百万字符 (极低)
- **实际使用**: 预计每月使用<50,000字符

## 技术验证状态

### ✅ 已完成验证:
1. **网络连通性**: Google Cloud API端点可达
2. **系统兼容性**: macOS `afplay`命令可用
3. **存储准备**: workspace目录可存储音频文件
4. **Python环境**: 3.12就绪，可安装必需库

### ❌ 关键阻塞点:
1. **Google Cloud API密钥缺失**: 无法调用Text-to-Speech服务
2. **服务账号JSON文件**: 需要身份验证凭证

## 开发阶段分解 (Google TTS版)

### 阶段1: 基础TTS功能 (目标: 今晚完成)
**依赖资源**: Google Cloud服务账号JSON密钥
**完成标准**: 能生成并播放测试语音，验证Google TTS集成

### 阶段2: 参数化语音生成 (目标: 明早完成)  
**依赖资源**: Daryl评估结果编码 + Google TTS SSML参数
**完成标准**: 基于Daryl水平的个性化语音模板

### 阶段3: 投资者演示场景 (目标: 明天完成)
**依赖资源**: Google TTS神经网络语音 + 商务语调控制
**完成标准**: 完整的投资者演示语音练习系统

## 实施时间表 (更新版)

### 当前时间: 22:29 GMT+7
- **22:29-22:45**: 等待Google Cloud资源配置
- **22:45-23:29**: 第一小时开发冲刺（如获API密钥）
- **23:29**: 第一次进度汇报
- **每小时后**: 持续汇报直至功能完成

## 紧急协调优先级 (Google TTS方案)

### 🚨 最高优先级 (立即需要):
1. **Google Cloud项目创建**
   - 链接: https://console.cloud.google.com
   - 项目名: `ielts-tts-2026` (建议)
   
2. **启用Text-to-Speech API**
   - 链接: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
   - 点击"启用"按钮

3. **创建服务账号和密钥**
   - 导航: IAM & Admin → Service Accounts
   - 创建: `ielts-tts-service` 账号
   - 权限: `Text-to-Speech API User`
   - 生成并下载JSON密钥文件

4. **存储JSON密钥**
   - 目标路径: `~/.openclaw/auth/google/ielts_tts_2026.json`
   - 格式: JSON文件，包含`private_key`等字段

### 📋 我的准备工作 (并行进行):
1. ✅ 创建进度汇报模板
2. ✅ 建立成本追踪框架 (虽然免费但需监控)
3. ✅ 准备Daryl参数编码脚本
4. ✅ 设计Google TTS SSML参数映射

## Google Cloud详细步骤指南

### 步骤1: 创建项目
1. 访问 https://console.cloud.google.com
2. 点击左上角项目选择器 → "新建项目"
3. 项目名称: `ielts-tts-2026`
4. 位置: 组织选择"无组织" (如果提示)
5. 点击"创建"

### 步骤2: 启用API
1. 在项目内访问: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
2. 点击"启用"按钮
3. 等待启用完成 (约1分钟)

### 步骤3: 创建服务账号
1. 导航到: IAM & Admin → Service Accounts
2. 点击"创建服务账号"
3. 服务账号名称: `ielts-tts-service`
4. 服务账号ID: 自动生成
5. 点击"创建并继续"

### 步骤4: 分配权限
1. 角色选择: 搜索并选择 `Text-to-Speech API User`
2. 点击"继续"
3. 点击"完成" (跳过用户访问部分)

### 步骤5: 生成密钥
1. 在服务账号列表中，找到 `ielts-tts-service`
2. 点击右侧三个点 → "管理密钥"
3. 点击"添加密钥" → "创建新密钥"
4. 密钥类型: JSON
5. 点击"创建" - 自动下载JSON文件

### 步骤6: 存储密钥
1. 确保目录存在: `mkdir -p ~/.openclaw/auth/google`
2. 移动下载的JSON文件: `mv ~/Downloads/*.json ~/.openclaw/auth/google/ielts_tts_2026.json`
3. 验证文件: `ls -la ~/.openclaw/auth/google/`

## 风险缓解措施

### 高风险项: Google账户权限
**缓解措施**: 
- 使用现有Google/Gmail账户
- 如遇组织限制，创建个人项目
- 确保项目在免费配额内

### 中等风险项: API启用延迟
**缓解措施**:
- 同时准备本地TTS备选方案
- 测试其他TTS服务作为备份

### 低风险项: 语音质量差异
**缓解措施**:
- Google TTS质量较高，接近OpenAI
- 可调整SSML参数优化发音
- 多语音选项可供选择

## 当前可并行工作项

### 无需API密钥可进行:
1. ✅ 创建每小时进度汇报模板
2. ✅ 建立字符用量监控框架
3. ✅ 设计Daryl参数→Google TTS SSML映射
4. ✅ 准备投资者演示文本模板

### 需API密钥后进行:
1. ❌ Google TTS API集成测试
2. ❌ 语音质量对比验证
3. ❌ SSML参数优化测试

---

**清单创建时间**: 2026-03-28 22:05 GMT+7  
**清单更新**: 2026-03-28 22:29 GMT+7 (切换至Google TTS)  
**创建人**: 吹点小风 (Bryson)  
**状态**: **等待Google Cloud资源配置** → TTS开发就绪