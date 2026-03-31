# 🚀 Motion-to-Code: UI 动效逆向还原引擎 (Universal AI Skill Pack)

这是一个将 **视觉动效视频 (MP4/GIF)** 转化为 **生产级双端代码 (Web/Android)** 的标准化 AI 插件包。它内置了四层渲染理论、算力防御红线以及 OpenCV 自动化解析能力。

---

## 📦 包内容清单 (Package Manifest)
- `system_instructions.md`: **核心指令集**。适配所有主流大模型 (Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro)。
- `.cursorrules`: **Cursor 专属规则**。针对 Cursor IDE 优化的行为模式准则。
- `scripts/`: **执行基础设施**。
  - `extract_frames.sh`: 帧提取与光流追踪调度器。
  - `track_elements.py`: OpenCV 机器视觉解析核心。
- `examples/`: **渲染模板库**。包含 T2 (网格)、T3 (Shader)、T4 (流体) 的 Android/Web 标准骨架。

---

## 🛠️ 详细安装指南 (Detailed Installation)

### 1. 环境准备 (环境缺失将导致 Step 3 解析失败)
确保开发机（Mac/Linux）具备以下环境：
```bash
# 1. 安装基础媒体处理库
brew install ffmpeg

# 2. 安装 Python 解析依赖 (OpenCV)
pip3 install opencv-python numpy matplotlib
```

### 2. 针对不同 AI 编程体的装载 (IDE/Agent Setup)

#### 🔵 Cursor (目前体验最佳)
1. **获取规则**: 复制包内的 `.cursorrules` 文本。
2. **挂载**: 如果项目已有 `.cursorrules`，请将其内容 **追加** 到末尾；若无，请在项目根目录新建该文件。
3. **启用**: 在 Cursor Chat (Cmd+L) 中输入 `@.cursorrules /motion-to-code` 即可开始。

#### 🟢 Claude Code / Antigravity (Agent 模式)
1. **部署资源**: 将压缩包解压，保留 `motion_to_code_release/` 目录在你的工作区内。
2. **初始化**: 将 `system_instructions.md` 全文复制并作为 **System Prompt** 或 **项目说明文档** 告知 Agent。
3. **指令示例**: "请读取项目中的 `system_instructions.md` 规则，并为我执行 motion-to-code 还原流程。"

#### 🟣 VS Code Copilot / Gemini (Chat 模式)
1. **注入上下文**: 将 `system_instructions.md` 的内容逐字发送给 AI。
2. **引用脚本**: 在后续对话中，确保 AI 知道调用工作区内的 `motion_to_code_release/scripts/extract_frames.sh` 进行分析。

---

## 📖 自动化三步引导流程 (Core Workflow)

AI 在加载此技能后，**必须**严格遵循以下对话范式，**严禁跳步直接写代码**：

### 第一步：停机索要源目标 (Source Request)
- **AI 动作**: 停止生成代码，输出：“*已启用 Motion-to-Code 技能。请通过附件提供参考视频/GIF，并简要描述该动效预期。*”
- **用户操作**: 拖入视频文件，描述核心（如：卡片挤压流体漂移）。

### 第二步：敲定物理约束 (Constraint Definition)
- **AI 动作**: 确认获得视频。询问：“*请确认目标尺寸（默认 16:9 画幅）及目标平台（Web/Android）。*”
- **用户操作**: 确认比例或指定特定分辨率。

### 第三步：量化报告与层级判定 (Analysis & Tier Check)
- **AI 动作**: 
  1. 调用本地 Shell 脚本提取帧。
  2. 输出 **《动效解析报告》**，明确显示 **Render Tier (1-4)** 和 **运动学统计数据**。
  3. 进行**预期管理**：告知用户在该层级下，模型能实现到什么程度。
- **用户操作**: 确认分析无误，回复“**继续/开始实现**”。

---

## 🚨 生产质量红线 (Production Redlines)
- **Web 端**: 强制 16:9 响应式布局，由于性能考虑，严禁在 T4 以外引入任何外部 3D 库。
- **Android 端**: 
    - 带有 `remember` 的扩展 Modifier 必须使用 `composed { ... }` 包裹。
    - 针对 T2 绘制必须在 `.drawWithCache` 首行进行 `Size > 0` 防 Crash 检查。
    - 文字单位强锁定为 `sp`。
- **全局**: 不得使用 Linear 匀速运动（除非是连续流场景），必须匹配 `Spring` 或 `FastOutSlowIn` 物理曲线。
