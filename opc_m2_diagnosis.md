# OPC看板M2问题诊断报告
**时间**: 2026-06-09 08:20  
**诊断人**: Bryson  
**项目路径**: `~/.openclaw/workspace/opc_dashboard/`

## 一、问题定位

### 1.1 运行状态检查
✅ **服务正常运行**:
- Port 8090: PID 73086 (旧版?)
- Port 8091: PID 9274 (IELTS陪练)
- Port 8092: PID 58413 (OPC看板新版)

### 1.2 发现的问题

#### 🔴 P0 - BrokenPipeError异常
**位置**: `server.py:379` (GET /api/cost)
**症状**:
```python
BrokenPipeError: [Errno 32] Broken pipe
  at do_GET() -> self.wfile.write(json.dumps(cost_data).encode())
```

**根因**: 
- 客户端在服务器完成响应前断开连接
- 可能是前端轮询过于频繁，或超时设置不当
- 缺少异常捕获，导致后端日志污染

**影响**: 
- ⚠️ 服务器日志堆满异常栈
- ⚠️ 可能导致部分API响应失败
- ⚠️ 用户体验：数据加载不稳定

---

#### 🟡 P1 - 任务编辑功能状态不明
**现状**: 
- 代码中存在`/save-tasks`和`/api/new-task`两个POST端点
- 未找到前端调用`/api/new-task`的代码（可能在被压缩的JS中）
- 缺少任务编辑的错误处理和反馈

**待验证**:
1. 前端编辑任务后是否能成功保存到`data/tasks.json`?
2. DM通知队列(`/tmp/opc_task_dm_queue.json`)是否正常写入?
3. Agent接收任务后是否有反馈机制?

---

#### 🟡 P1 - 端口混乱
**问题**: 3个端口同时运行Python server
- 8090: 旧版（缓存?）
- 8091: IELTS陪练（我启动的）
- 8092: OPC看板新版（Kitty启动的）

**风险**:
- 用户访问错误端口看到旧版
- 资源浪费（3个进程占用内存）
- 日志分散难以追踪

---

## 二、修复方案

### 2.1 立即修复（P0）

#### Fix #1: 捕获BrokenPipe异常
**文件**: `server.py:379`

```python
# 当前代码（有问题）
def do_GET(self):
    ...
    self.wfile.write(json.dumps(cost_data, ensure_ascii=False).encode())

# 修复后
def do_GET(self):
    ...
    try:
        self.wfile.write(json.dumps(cost_data, ensure_ascii=False).encode())
    except BrokenPipeError:
        # 客户端已断开，静默处理
        pass
    except Exception as e:
        print(f"⚠️ Error writing response: {e}")
```

**同时修复所有`wfile.write()`调用点**（估计5-8处）

---

#### Fix #2: 优化前端轮询频率
**文件**: `index.html` (搜索`setInterval`或`fetch(/api/cost)`)

**建议**:
- 成本数据：30秒轮询 → 60秒
- Agent状态：5秒轮询 → 10秒
- 使用指数退避：连续失败后延长间隔

---

### 2.2 中期修复（P1）

#### Fix #3: 统一端口管理
**行动**:
1. 停止旧版8090进程：`kill 73086`
2. 确认IELTS陪练使用8091
3. OPC看板固定使用8092
4. 更新启动脚本`manage.sh`，加入端口检测

---

#### Fix #4: 任务编辑功能完善
**待做**:
1. 前端加入保存成功/失败提示
2. 后端返回详细错误信息
3. 增加任务状态同步机制（保存后刷新Agent状态）

---

## 三、测试清单

完成修复后，逐项验证：

- [ ] 访问 http://localhost:8092 看到最新版看板
- [ ] 成本面板数据正确显示（无BrokenPipe错误）
- [ ] 创建新任务后成功保存到`data/tasks.json`
- [ ] 编辑现有任务，刷新页面后修改保留
- [ ] 指定Agent后，对应Agent卡片显示任务数量更新
- [ ] DM通知功能正常（如果启用）
- [ ] 后端日志`opc_dashboard.log`中无异常栈（除非真的有错误）
- [ ] 浏览器Console无JavaScript错误
- [ ] 页面响应流畅（无卡顿/loading timeout）

---

## 四、分工建议

### Bryson负责:
1. ✅ **修复BrokenPipe异常** (5分钟)
   - 在所有`wfile.write()`外包裹try-except
   - 测试API端点是否稳定
2. ✅ **清理端口混乱** (3分钟)
   - 停止冗余进程
   - 验证服务运行在正确端口
3. ✅ **前端轮询优化** (10分钟)
   - 调整setInterval频率
   - 加入重试逻辑

**预计完成时间**: 20分钟

### Kitty负责:
1. **任务编辑功能review** (15分钟)
   - 验证前端JS是否正确调用`/save-tasks`
   - 检查`data/tasks.json`写入权限
   - 测试各种边界情况（空任务、特殊字符等）
2. **DM通知机制测试** (10分钟)
   - 验证`/tmp/opc_task_dm_queue.json`是否正常生成
   - 确认heartbeat是否能读取并发送通知
3. **UI交互反馈** (10分钟)
   - 加入"保存成功"提示
   - 处理保存失败情况（如后端不可用）

**预计完成时间**: 35分钟

---

## 五、验收标准（M2完整交付）

1. ✅ 无后端异常（BrokenPipe等）
2. ✅ 任务CRUD功能完整可用
3. ✅ Agent状态实时更新
4. ✅ 成本面板数据准确
5. ✅ 页面响应流畅（<2秒加载）
6. ✅ 日志干净（只记录正常请求，异常有清晰错误信息）

---

## 六、记忆更新

完成修复后，更新以下文件：
- `memory/2026-06-09.md` — 记录今天的诊断和修复
- `memory/active.md` — 将OPC看板M2状态改为✅已完成
- `memory/lessons.md` — 加入"前端轮询要考虑BrokenPipe场景"

---

**Daryl**: 这是我的诊断报告。我现在立即开始修复P0问题（BrokenPipe），预计5分钟完成。需要我现在开始吗？还是等Kitty上线后一起分工？
