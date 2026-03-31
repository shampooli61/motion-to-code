---
name: motion-to-code
description: 将 UI/UX 动效视频或 GIF 逆向还原为可运行的动效代码（Web + Android Compose）
---

# Motion-to-Code 动效还原技能

将 UI/UX 动效设计视频或 GIF 逆向还原为可运行的动画代码。你必须**严格遵循**以下交互与执行步骤：

## 🚀 核心工作流 (Standard Procedure)

### 第一步：启动与参考源收集 (Initialization & Inquiry) 🆕
- 当用户通过 `/motion-to-code` 或自然语言启用本技能时，你首先需要**停下来询问用户**：
  1. **参考源文件**：请用户通过聊天框的 **附件按钮 (➕/📎)** 直接选择系统文件，或者**直接将视频拖拽进对话框**（支持 `.mp4`, `.gif` 等）。
  2. **自然语言描述**：要求用户在发送文件时，顺便用一句话补充描述该动画的核心行为（例如：“*卡片从上方被吸入消失，过程中形变拉长，产生运动模糊*”）。
  > ⚠️ 此时进入等待状态，必须等待用户发送文件（或告知文件路径）并提供描述后再继续。

### 第二步：确定动效约束比例 (Dimensions & Constraints) 🆕
- 检索到用户提供的参考文件后，你需要**再次询问**生成的动效目标尺寸：
  1. 告知用户**默认约束为 16:9** 的比例（适用于大多数横屏展示场景）。
  2. 询问用户是否需要**自定义比例**或**特定尺寸**（例如：9:16、4:3、具体的 px 或 dp 值）。
- 向用户强调：无论选择何种尺寸，后续动画生成都将严格基于确定的尺寸进行**“去样机化 (De-mockup)”** + **“纯净自适应骨架”**提取，排除视频原有的设备外壳或黑边干扰。
  > ⚠️ 此时进入等待状态，必须等待用户确认目标尺寸后再继续。

### 第三步：机器视觉解析与预期管理 (Analysis & Expectation Management) 🆕
- 收集齐上述信息后，开始自动执行分析操作：
  1. 调用提取脚本 `bash .agents/skills/motion-to-code/scripts/extract_frames.sh <输入文件路径>`（脚本自带有自适应帧率逻辑）。
  2. 读取生成的 `motion-output/tracking_data.md`，并将视觉量化数据与用户第一步的自然语言描述进行**交叉验证**。
  3. 撰写中文分析报告至 `motion-output/analysis.md`。
- **与用户同步解析结果**：
  - 向用户汇报提取到的骨架特性和**渲染层级判定 (Tier 1/2/3)**（并在注释中解释该层级的含义）。
  - ⚠️ **降低预期 (Manage Expectations)**：向用户清晰说明当前生成的程度边界。告知用户生成的代码是对核心动效骨架、曲线和层级关系的还原，旨在建立可运行的交互框架，但在像素级物理形变、极复杂的粒子特效或特定的高斯光影细节上，可能无法达到对原生参考视频 100% 的视觉复现。
  > ⚠️ 此时询问用户是否同意分析结果并继续生成代码。

### 第四步：Web 预览版生成测试 (Generate Web Preview)
- 获得用户同意后，在 `motion-output/web/` 中生成基于 Vanilla CSS/JS 的还原代码。
- ⚠️ **强制规范：基于选定比例的横屏窗口 (Responsive Bounds)**
  - 根据第二步确定的比例（如默认 `aspect-ratio: 16/9`），构建一个主舞台容器包裹特效。
  - 内部界面排布必须采用 `%` 百分比、`vmin/vmax` 或 flex/grid 进行**响应式自适应布局**。
- ⚠️ **强制规范：可视化调音台 (Interactive Config Panel)**
  - 必须在页面最右侧（脱离主窗口）渲染一个浮窗式 UI 面板，包含：分组标题 + 每个参数对应一个 `<input type="range">` 滑块，实时修改 CSS Variables，所见即所得。

### 第五步：浏览器自动动效验证 (Browser Automation Testing)
- 调用 `browser_subagent` 录制并验证 `file:///.../motion-output/web/` 的动效轨迹。验证无误后，向用户简短反馈。

### 第六步：Android 原生生产代码输出 (Generate Android Code)
根据第三步判定的 Tier，选择对应的渲染引擎输出代码：

#### ⚠️ 渲染层级判定（Render Tier Classification）

在分析阶段，你**必须**判定动效的渲染复杂度等级，并在 `analysis.md` 中明确标注：

| Tier | 判定条件 | Android 渲染引擎 | Web 渲染引擎 |
|------|---------|-----------------|-------------|
| **T1 刚体动效** | 仅涉及 scale / translate / rotate / opacity / spring | Compose Animation API | CSS Transitions + Transforms |
| **T2 网格形变** | 检测到非线性形变（鱼眼膨胀、边缘弯曲、柔性拉伸、非矩形变形） | `Canvas.drawBitmapMesh()` | Canvas 2D + Mesh Grid |
| **T3 图像着色** | 检测到像素级后处理（径向模糊、热浪扭曲、色散、发光） | AGSL `RuntimeShader` (API 33+) | WebGL Fragment Shader |
| **T4 算法流体/噪声的生成** 🆕 | 分形维度算法生成（如流体动力学、Simplex 噪声纹理、Raymarching SDF 光影） | AGSL `RuntimeShader` | WebGL (原生 Boilerplate) |

**判定方法**：
- 若关键帧中的运动主体边缘始终保持**平行直线**（含 3D 梯形透视等刚体运动） → T1
- 若关键帧中观察到主体主要是基于平面网格的**柔性拉伸、膨胀或扭曲** → T2
- 若动效主要是对现成视口画面的**像素滤镜加工**（如后延时模糊、色散等） → T3
- 若动效**不依赖外部图片推演**，而是纯利用数学算法**无中生有产生流体、烟雾、斑痕**，或包含 Shadertoy 架构的纯代码生成式图形范式 → T4

### Step 3: Web 预览版生成测试 (Generate Web Preview)
- 在 `motion-output/web/` 中生成基于 Vanilla CSS/JS 的还原代码。
- ⚠️ **强制规范：16:9 横屏窗口 (Landscape Mobile Frame)** 🆕
  - 必须把所有 Web 原型特效包裹在一个水平垂直居中的 **横屏 `aspect-ratio: 16/9`** 容器中（高度或宽度自适应），非内容区域背景置灰。
  - 内部界面排布必须采用 `%` 百分比、`vmin/vmax` 或 flex/grid 进行**响应式自适应布局**，确保骨架能随外框尺寸自动缩放。
- ⚠️ **强制规范：可视化调音台 (Interactive Config Panel)**
  - 必须在页面最右侧（脱离 16:9 主窗口）渲染一个**浮窗式 UI 面板**，包含：
    - 分组标题 + 每个参数对应一个 `<input type="range">` 滑块
    - 实时修改 CSS Variables，所见即所得
  - 同时在 `<style>` 的 `:root` 中用 CSS 变量定义所有魔法数字。
- **T2 场景**：使用 HTML5 `<canvas>` + JS 网格变形代替 CSS 动画。
- **T3 场景**：使用 WebGL Shader 实现。

### Step 4: 浏览器自动动效验证 (Browser Automation Testing)
- 调用 `browser_subagent` 录制并验证 `file:///.../motion-output/web/` 的动效轨迹。

### Step 5: Android 原生生产代码输出 (Generate Android Code)
根据 Step 2 判定的 Tier，选择对应的渲染引擎输出代码：

#### T1 输出：Compose Animation（标准路径）
- 输出到 `motion-output/android/MotionAnimation.kt`
- 使用 `animateXAsState()`、`Animatable`、`spring()` 等标准 API
- ⚠️ **强制规范：独立配置数据类 (Data Class)**
  - 文件顶部定义 `data class MotionConfig(...)`，集中管理所有可调参数（时长、位移量、旋转角、张力等）。
- ⚠️ **强制规范：Android 侧边参数调音台 (Slider Config Panel)** 🆕
  - **必须**在主预览入口 `@Composable fun MotionPreview()` 中，利用 Compose 的 `Slider` 编写一个**浮层侧滑调音台**。
  - 此面板需将上述 Data class 的参数均暴露为滑块，方便客户端开发在真机实时调参（功能与 Step 3 的 Web 调音台保持一致）。

#### T2 输出：Canvas.drawBitmapMesh（网格形变路径）🆕
- 输出到 `motion-output/android/MotionAnimation.kt`
- **参考骨架**：阅读 `.agents/skills/motion-to-code/examples/MeshMorphRenderer.kt`
- 核心 API：`Canvas.drawBitmapMesh(bitmap, meshW, meshH, verts, ...)`
- ⚠️ **强制规范**：文件顶部定义 `data class MeshMorphConfig(网格密度, 膨胀强度, 膨胀半径, ...)` 配置对象
- 渲染流程：
  1. 将内容渲染为 Bitmap（或传入现有 Bitmap）
  2. `createBaseMesh()` 构建均匀网格
  3. `applyBulgeMesh()` 按当前动画进度计算形变顶点
  4. `drawBitmapMesh()` 输出到 Canvas
- **零依赖**，API Level 1 即可用

#### T3 输出：AGSL RuntimeShader（着色器路径）🆕
- 输出到 `motion-output/android/MotionAnimation.kt`
- **参考骨架**：阅读 `.agents/skills/motion-to-code/examples/ShaderEffectRenderer.kt`
- 核心 API：`RuntimeShader(agslCode)` + `RenderEffect.createRuntimeShaderEffect()`
- ⚠️ **限制**：需要 minSdk 33 (Android 13)
- ⚠️ **强制规范**：文件顶部定义 `data class ShaderEffectConfig(...)` 配置对象
- **零依赖**，直接使用 Android 原生 GPU 渲染管线

#### T4 输出：高阶算法 Shader（流体/噪声/SDF路径） 🆕
- **目标**：将 Shadertoy/OpenProcessing 的开源数学模型代码转化为我们的大模型生产边界能力，实现液态融化、火焰、烟雾或光影噪点流动等高级物理特效。
- **输出端**：Android 端写入 `motion-output/android/...`，基于 Compose `RuntimeShader`；Web 端写入 `motion-output/web/...`。
- **参考骨架**：必须查考阅读 `.agents/skills/motion-to-code/examples/FluidNoiseRenderer.kt`
- ⚠️ **Web 端强约束**：**绝对禁止引入 `Three.js`、`Pixi.js` 等庞大重量级 3D 库**。必须手写一个少于 100 行代码的纯净 WebGL Boilerplate，将算法挂载并投影在一个全屏 Quad 三角面上。必须向下文传入 `u_resolution`、`u_time` 以及 `u_mouse`。
- ⚠️ **算力坍缩底线防范 (Performance Bound)**：移动端设备 GPU 算力有限薄弱。在转化 Shadertoy 公式时，严禁使用过于昂贵的**高深度嵌套循环 SDF Raymarching 步进测试**及多重贴材质运算。请针对 FBM 设置极少层级（不超过 4-6 个 Octaves 下采阶层）或直接利用快速 2D Simplex Noise 代替 3D 算法算绘画面。

---
### 🌐 Shadertoy/GLSL 到全端迁移翻译引擎 (Translation Pipeline) ⚠️
为杜绝语言变元报错，当你跨端复现并改造社区已验证好的数学模型源码时，**必须完全遵照**以下数据类型强行映射替换准则：

#### 1. AGSL 编译转换 (针对 Android Compose `RuntimeShader`)
AGSL 本质是 GLSL ES 1.0 的限制超集语言，对于传统 Web Shader 的语法，大模型你在翻译重写时必须使用以下的映射格式替代：
- **基础运算数据类型坍缩**：
  - `vec2`, `vec3`, `vec4` => `float2`, `float3`, `float4` （在处理色彩或者 uv 值时更推荐其对应的 `half2`, `half3`, `half4` 半精度格式可提效）。
  - `mat2`, `mat3`, `mat4` => `float2x2`, `float3x3`, `float4x4`。
- **主片元函数入口重新声明**：
  - 传统声明：~~`void mainImage(out vec4 fragColor, in vec2 fragCoord)`~~ 必须抛弃。
  - **合法转录为**：`half4 main(float2 fragCoord) { ... return half4(r, g, b, a); }`。
- **动态坐标系强绑定**：
  - Shader 域内无直接全量 `gl_FragCoord` 获取尺寸。所有入参全部借由 `main` 进来的参传入，并需要自主映射 UV：`float2 uv = fragCoord.xy / resolution.xy;`。
- **自定义采样机制**：
  - 取色操作需用 `uniform shader iChannel0;` 而非纹理类型定义。拉取像素命令从 ~~`texture(iChannel0, uv)`~~ 转录为 **`iChannel0.eval(uv * resolution.xy)`**。

#### 2. WebGL 原生移植约定 
在生成配套的 Web HTML 等价文件时，所有 GLSL 必须遵循以下转换法配合原生挂载：
- **入口和内建输出**：保留 `void main() { ... gl_FragColor = vec4(color, 1.0); }`，并挂载 `varying vec2 vUv;` 辅助接收前端定点传递。
- **统一定义头**：强制要求顶层暴露 `uniform vec2 u_resolution;`、`uniform float u_time;` 和 `uniform vec2 u_mouse;` 三大神器数据位。

#### ⚠️ 全局输出规范：独立配置数据类与跨端调音台对齐 ⚠️
对于**所有渲染层级** (T1/T2/T3)，你都必须在输出 Android 原生代码时遵守以下对齐策略：
1. **独立配置数据类 (Data Class)**：顶部定义如 `data class MotionConfig(...)`，集中管理所有核心可调参数（曲线轨迹、弹性张力、形变强度、流密度等）。
2. **Android 侧边参数调音台 (Slider Config Panel)** 🆕：
   - 必须在入口 `@Composable fun MotionPreview()` 中，利用 Compose 编写一个悬浮或侧滑的调音台面板。
   - 面板需将前述 Data class 的所有核心参数暴露为实时交互的 `Slider` 滑块。
   - 配置联动必须即时反映在底层的绘制渲染中，达到与 Web 调音台完全一致的用户体验。
3. **16:9 横屏锁定与响应式骨架 (Landscape & Responsive Bounds)** 🆕：
   - 最外层的 Compose 动效展示区必须使用 `Modifier.aspectRatio(16f / 9f)` 来限制其渲染比例，成为统一的横版视窗界限。
   - 内部的 UI/Canvas 坐标、控件大小及偏移量，全数须依赖 `LocalConfiguration` 或 `BoxWithConstraints` 注入的屏幕宽高按百分比映射，实现**严丝合缝的自适应特性**。
4. **🚨 移动端 Compose 语法防劣化红线 (Anti-Degradation Redlines)** 🚨：
   - **自定义 Modifier 生命周期越权**：当封装扩展 Modifier (如绘制网格或 Shader) 且内部须保存状态 (`remember`) 或动画 (`animate*AsState`) 时，**绝对禁止**直接函数域调用。必须外包一层 `@SuppressLint("ModifierFactoryUnreferencedReceiver") fun Modifier.ext() = composed { ... }`！
   - **绘制上下文 Size 防爆 (Size Guarding)**：在 `Modifier.drawWithCache` 提取截帧或分配 FloatArray 时，必须做零界限检查 `if (size.width <= 0f || size.height <= 0f) return@drawWithCache onDrawWithContent {}` 防制 Native 层 Crash。
   - **文字与度量单位混用**：向 `Text` 传递大小绝对禁止使用 `xx.dp`。`fontSize` 必经由 `import androidx.compose.ui.unit.sp` 限定强转为 `.sp`。
   - **作用域修饰链防越界 (Scope Misalignment)**：封装独立子组件 `@Composable fun Widget()` 时，禁止在内部根节点绑死如 `Modifier.align` 等必须依赖父 `BoxScope` 的 API。应暴露 `(modifier: Modifier = Modifier)` 交由上层父容器指派对齐策略。

---

## ⚠️ 智能缓动曲线引擎 (Smart Easing Engine) ⚠️

**核心原则**: 禁止使用千篇一律的 `linear` 或单一 `ease-in` 曲线。必须根据**交互语义**和**目标平台特性**智能选择缓动参数，让动画具有生命力。

### 1. 交互语义缓动词表 (Interaction Easing Vocabulary)

动画的每一个运动阶段都必须被归类为以下语义之一，然后查表选取推荐曲线：

| 交互语义 | 运动特征 | Web (CSS/JS) 推荐 | Android (Compose) 推荐 |
|---------|---------|-------------------|----------------------|
| **入场 (Enter)** | 元素从无到有，由远及近 | `cubic-bezier(0.0, 0.0, 0.2, 1)` (Material decelerate) | `FastOutSlowInEasing` 或 `spring(dampingRatio=0.7, stiffness=300)` |
| **退场 (Exit)** | 元素消失，由近及远 | `cubic-bezier(0.4, 0.0, 1, 1)` (accelerate) | `FastOutLinearInEasing` + `tween(300)` |
| **强调 (Emphasis)** | 引起注意的脉冲/抖动 | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` (overshoot) | `spring(dampingRatio=0.4, stiffness=500)`（明显弹跳） |
| **跟手 (Gesture Tracking)** | 拖拽/滑动时实时跟随 | 无 transition，直接绑定 pointer 坐标 | `Animatable.snapTo()` 或直接赋值（零延迟） |
| **惯性释放 (Fling)** | 手指松开后的惯性滑行 | `cubic-bezier(0.4, 0.0, 0.0, 1)` + `400ms` | `decay(absVelocityThreshold=..)` 或 `spring(stiffness=StiffnessLow)` |
| **弹性回位 (Spring Back)** | 越界后弹回原位 | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | `spring(dampingRatio=DampingRatioMediumBouncy, stiffness=StiffnessMedium)` |
| **连续流 (Continuous Flow)** | 循环播放/粒子轨迹 | `linear` + `requestAnimationFrame` | `infiniteRepeatable` + `LinearEasing`（仅此场景允许 linear） |
| **级联交错 (Stagger)** | 列表项依次入场 | `stagger-delay: index * 50ms` + decelerate | `tween(delay = index * 60, easing = FastOutSlowInEasing)` |

### 2. 平台差异化策略 (Platform-Specific Strategy)

#### Web 端策略
- **优先使用 `cubic-bezier` 参数化曲线**：CSS transition 引擎对贝塞尔曲线有硬件加速。
- **模拟弹簧效果**：使用 `cubic-bezier(0.175, 0.885, 0.32, 1.275)` 产生轻微过冲（overshoot），而非依赖 JS 弹簧库。
- **手势跟随**：使用 `pointermove` 事件直接赋值 `transform`，不加任何 `transition`。
- **惯性延续**：使用 `requestAnimationFrame` 循环，每帧按衰减系数 `velocity *= 0.95` 递减速度。

#### Android Compose 端策略
- **优先使用 `spring()` 物理弹簧**：Compose 的弹簧引擎利用了原生 API 的帧同步机制，天生比 `tween` 流畅。
- `spring()` 的 `dampingRatio` 和 `stiffness` 是灵魂参数，可以精确模拟从过阻尼到欠阻尼的全部物理特性。
- **跟手拖拽**：使用 `Animatable.snapTo()` 达到无延迟追随。
- **惯性释放**：使用 `Animatable.animateDecay(initialVelocity, exponentialDecay())`。
- **级联交错**：使用 `LaunchedEffect(index)` 中延迟 `delay(index * 60L)` 后再启动动画。

### 3. 强制应用规则

在生成代码时，**必须遵循以下判定流程**：
1. 识别动画运动阶段的**交互语义**（从上表 8 类中选择）。
2. 根据目标平台（Web / Android）查表选取**推荐曲线**。
3. 如果参考视频中能观测到**过冲 (overshoot)** 或**回弹 (bounce)**，则 Android 必须用 `spring()` 而非 `tween()`。
4. **绝对禁止**在入场/退场/跟手/弹性语义中使用 `LinearEasing` 或 `linear`。
5. Config Panel 中必须暴露**至少一个缓动参数**（如弹簧阻尼比、曲线控制点等）供实时调优。

---

## 动画参数映射字典
| Web (CSS) | Android (Compose) |
|-----------|-------------------|
| `transition` | `animateXAsState()` |
| `@keyframes` | `Animatable` + `animateTo()` |
| `ease-in-out` | `FastOutSlowInEasing` |
| `ease-out` | `FastOutLinearInEasing` |
| `ease-in` | `LinearOutSlowInEasing` |
| `linear` | `LinearEasing` |
| `cubic-bezier(x1,y1,x2,y2)` | `CubicBezierEasing(x1,y1,x2,y2)` |
| `spring` | `spring(dampingRatio, stiffness)` |
| `canvas.bindTexture()` (WebGL) | `RuntimeShader.setInputShader()` (AGSL) |
| `canvas drawBitmapMesh` (2D) | `Canvas.drawBitmapMesh()` |
