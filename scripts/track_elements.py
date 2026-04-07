#!/usr/bin/env python3
"""
OpenCV 多策略运动追踪脚本 v3
===========================
v3 新增（抗误判增强）:
4. 宽高比变化追踪：检测不等比形变 (scaleX≠scaleY)
5. 光流方向分类：区分汇聚/发散/旋转/剪切/定向 型运动
6. 运动模糊方向检测：识别竖向/横向模糊拖尾
7. AI 动效行为预判：基于多维信号输出 Top-3 候选类型 + 置信度

v2 基础:
1. 光流法 (Optical Flow)：追踪全局帧间运动方向和幅度
2. 多轮廓边界框检测：逐帧独立检测所有显著色块的位置与面积
3. 帧差法 (Frame Differencing)：检测帧间变化的激烈程度，自动识别转场
"""
import cv2
import numpy as np
import glob
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
FRAMES_DIR = BASE_DIR / "motion-input" / "frames"
OUTPUT_DIR = BASE_DIR / "motion-output"

def detect_contours(gray_frame, min_area_ratio=0.005):
    """检测单帧中所有显著轮廓的边界框"""
    h, w = gray_frame.shape
    min_area = h * w * min_area_ratio
    
    blurred = cv2.GaussianBlur(gray_frame, (7, 7), 0)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=2)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        boxes.append({
            "x": x, "y": y, "w": bw, "h": bh,
            "cx": x + bw / 2, "cy": y + bh / 2,
            "area": bw * bh,
            "aspect_ratio": bw / max(bh, 1)  # v3: 宽高比
        })
    
    boxes.sort(key=lambda b: b["area"], reverse=True)
    return boxes[:5]

def compute_optical_flow_magnitude(prev_gray, curr_gray):
    """计算两帧之间的密集光流平均运动幅度和方向"""
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0
    )
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    avg_mag = float(np.mean(mag))
    avg_dx = float(np.mean(flow[..., 0]))
    avg_dy = float(np.mean(flow[..., 1]))
    return avg_mag, avg_dx, avg_dy, flow

def compute_frame_diff(prev_gray, curr_gray):
    """计算帧差百分比"""
    diff = cv2.absdiff(prev_gray, curr_gray)
    changed_pixels = np.sum(diff > 30)
    total_pixels = diff.shape[0] * diff.shape[1]
    return changed_pixels / total_pixels * 100

# ============== v3 新增函数 ==============

def classify_flow_pattern(flow):
    """
    v3: 光流方向分类 — 区分运动模式
    返回: convergent(汇聚), divergent(发散), rotational(旋转), 
          shear(剪切/形变), directional(方向性平移), static(静止)
    """
    h, w = flow.shape[:2]
    mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    avg_mag = np.mean(mag)
    
    if avg_mag < 0.5:
        return "static"
    
    # 计算从中心到各像素的方向向量
    cy, cx = h / 2, w / 2
    yy, xx = np.mgrid[0:h, 0:w]
    radial_x = (xx - cx).astype(np.float32)
    radial_y = (yy - cy).astype(np.float32)
    radial_len = np.sqrt(radial_x**2 + radial_y**2) + 1e-6
    radial_x /= radial_len
    radial_y /= radial_len
    
    # 光流在径向的投影 (正=发散, 负=汇聚)
    flow_norm = mag + 1e-6
    fx = flow[..., 0] / flow_norm
    fy = flow[..., 1] / flow_norm
    radial_proj = fx * radial_x + fy * radial_y
    avg_radial = float(np.mean(radial_proj[mag > avg_mag * 0.3]))
    
    # 光流在切向的投影 (正=逆时针, 负=顺时针)
    tangent_x = -radial_y
    tangent_y = radial_x
    tangent_proj = fx * tangent_x + fy * tangent_y
    avg_tangent = float(np.mean(tangent_proj[mag > avg_mag * 0.3]))
    
    # X/Y 方向不对称 (剪切/形变)
    avg_fx = float(np.mean(np.abs(flow[..., 0])))
    avg_fy = float(np.mean(np.abs(flow[..., 1])))
    xy_ratio = max(avg_fx, avg_fy) / max(min(avg_fx, avg_fy), 0.01)
    
    # 决策
    if abs(avg_radial) > 0.4:
        return "divergent" if avg_radial > 0 else "convergent"
    elif abs(avg_tangent) > 0.4:
        return "rotational"
    elif xy_ratio > 2.5:
        return "shear"
    else:
        return "directional"

def detect_blur_direction(gray_frame):
    """
    v3: 运动模糊方向检测
    通过 Sobel 梯度分析图像模糊的主方向
    返回: "vertical", "horizontal", "none"
    """
    sobelx = cv2.Sobel(gray_frame, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_frame, cv2.CV_64F, 0, 1, ksize=3)
    
    grad_x_energy = np.mean(np.abs(sobelx))
    grad_y_energy = np.mean(np.abs(sobely))
    
    if grad_x_energy < 1 and grad_y_energy < 1:
        return "none"
    
    ratio = grad_x_energy / max(grad_y_energy, 0.01)
    
    # 如果 X 梯度远大于 Y 梯度 → Y 方向模糊 (垂直方向运动模糊使得 Y 梯度消失)
    if ratio > 1.5:
        return "vertical"
    elif ratio < 0.67:
        return "horizontal"
    else:
        return "none"

def predict_motion_behavior(frame_data):
    """
    v3: AI 动效行为预判
    基于多维信号输出 Top-3 候选动效类型 + 置信度
    """
    if not frame_data:
        return []
    
    # 收集信号
    ar_changes = [d["ar_change"] for d in frame_data if d["ar_change"] is not None]
    flow_patterns = [d["flow_pattern"] for d in frame_data if d["flow_pattern"] != "static"]
    blur_dirs = [d["blur_direction"] for d in frame_data]
    max_diff = max(d["diff_pct"] for d in frame_data)
    areas = [d["main_w"] * d["main_h"] for d in frame_data if d["main_w"] > 0]
    area_ratio = max(areas) / max(min(areas), 1) if areas else 1.0
    
    has_deformation = any(abs(c) > 15 for c in ar_changes)  # 宽高比变化 > 15%
    has_convergent = "convergent" in flow_patterns
    has_divergent = "divergent" in flow_patterns
    has_rotational = "rotational" in flow_patterns
    has_shear = "shear" in flow_patterns
    has_vertical_blur = "vertical" in blur_dirs
    has_horizontal_blur = "horizontal" in blur_dirs
    has_directional = "directional" in flow_patterns
    
    candidates = []
    
    # 吸入/弹出 (Suck-In)
    score = 0
    reasons = []
    if has_deformation:
        score += 30; reasons.append("宽高比突变")
    if has_vertical_blur:
        score += 20; reasons.append("竖向运动模糊")
    if has_convergent or has_divergent:
        score += 15; reasons.append("汇聚/发散光流")
    if has_directional:
        score += 10; reasons.append("定向光流")
    if score > 0:
        candidates.append(("吸入/弹出 (Suck-In/Pop-Out)", score, reasons))
    
    # 3D 旋转
    score = 0
    reasons = []
    if has_rotational:
        score += 35; reasons.append("旋转型光流")
    if has_deformation and not has_vertical_blur:
        score += 10; reasons.append("宽度变化(可能是透视)")
    if area_ratio < 1.3:
        score += 10; reasons.append("面积近似恒定")
    if score > 0:
        candidates.append(("3D Y轴旋转 (Card Flip)", score, reasons))
    
    # 平移滑入
    score = 0
    reasons = []
    if has_directional and not has_deformation:
        score += 30; reasons.append("统一方向光流+无形变")
    if has_horizontal_blur:
        score += 15; reasons.append("横向运动模糊")
    if score > 0:
        candidates.append(("平移滑入 (Slide In/Out)", score, reasons))
    
    # 缩放入场
    score = 0
    reasons = []
    if (has_convergent or has_divergent) and not has_deformation:
        score += 25; reasons.append("径向光流+无形变")
    if area_ratio > 2.0:
        score += 15; reasons.append(f"面积比 {area_ratio:.1f}x")
    if score > 0:
        candidates.append(("缩放入场/退场 (Scale In/Out)", score, reasons))
    
    # 形变过渡
    score = 0
    reasons = []
    if has_shear:
        score += 30; reasons.append("剪切型光流")
    if has_deformation:
        score += 20; reasons.append("不等比形变")
    if score > 0:
        candidates.append(("柔性形变 (Deformation)", score, reasons))
    
    # 淡入淡出
    if max_diff < 15 and not has_deformation and not flow_patterns:
        candidates.append(("淡入淡出 (Fade)", 20, ["低帧差+无运动"]))
    
    # 归一化为百分比
    total = sum(c[1] for c in candidates)
    if total > 0:
        candidates = [(name, round(score / total * 100), reasons) for name, score, reasons in candidates]
    
    # 排序取 Top-3
    candidates.sort(key=lambda c: c[1], reverse=True)
    return candidates[:3]

def run():
    frame_files = sorted(glob.glob(str(FRAMES_DIR / "*.png")))
    if not frame_files:
        print("⏭️ 未找到提取的帧序列，跳过特征追踪。")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_file = OUTPUT_DIR / "tracking_data.md"

    print(f"👁️‍🗨️ OpenCV v3 正在进行多策略运动分析 ({len(frame_files)} 帧)...")

    frame_data = []
    prev_gray = None
    prev_ar = None  # 上一帧宽高比

    for i, fpath in enumerate(frame_files):
        frame = cv2.imread(fpath)
        if frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 轮廓检测
        boxes = detect_contours(gray)
        main_box = boxes[0] if boxes else None
        
        # v3: 宽高比
        curr_ar = main_box["aspect_ratio"] if main_box else None
        ar_change = None
        if curr_ar is not None and prev_ar is not None and prev_ar > 0:
            ar_change = (curr_ar - prev_ar) / prev_ar * 100  # 百分比变化

        # 光流 + 帧差
        flow_mag, flow_dx, flow_dy = 0, 0, 0
        diff_pct = 0
        flow_pattern = "static"
        blur_dir = detect_blur_direction(gray)
        
        if prev_gray is not None:
            flow_mag, flow_dx, flow_dy, flow = compute_optical_flow_magnitude(prev_gray, gray)
            diff_pct = compute_frame_diff(prev_gray, gray)
            flow_pattern = classify_flow_pattern(flow)

        frame_data.append({
            "frame": i + 1,
            "main_cx": main_box["cx"] if main_box else gray.shape[1] / 2,
            "main_cy": main_box["cy"] if main_box else gray.shape[0] / 2,
            "main_w": main_box["w"] if main_box else 0,
            "main_h": main_box["h"] if main_box else 0,
            "num_blocks": len(boxes),
            "flow_mag": flow_mag,
            "flow_dx": flow_dx,
            "flow_dy": flow_dy,
            "diff_pct": diff_pct,
            "aspect_ratio": curr_ar,
            "ar_change": ar_change,
            "flow_pattern": flow_pattern,
            "blur_direction": blur_dir,
        })
        prev_gray = gray
        prev_ar = curr_ar

    # ===== 生成 Markdown 报告 =====
    md = "# OpenCV 运动追踪分析报告 v3\n\n"
    md += "> 🤖 **AI 提示**：此报告包含 **6 类数据**（v3 新增 3 类标记 🆕）。\n"
    md += "> 1. **主体色块位置**：帧中最大可视元素的中心坐标与尺寸。\n"
    md += "> 2. **光流位移 (Optical Flow)**：帧间全局平均运动向量。\n"
    md += "> 3. **变化强度 (Diff%)**：帧间像素变化百分比。超过 30% 通常意味着转场。\n"
    md += "> 4. 🆕 **宽高比变化 (AR Δ%)**：主体宽高比的帧间变化。>15% 提示不等比形变。\n"
    md += "> 5. 🆕 **光流方向分类 (Flow Pattern)**：convergent/divergent/rotational/shear/directional/static。\n"
    md += "> 6. 🆕 **运动模糊方向 (Blur Dir)**：检测图像中的定向模糊拖尾。\n\n"

    md += "## 逐帧追踪表\n\n"
    md += "| 帧号 | 主体宽 | 主体高 | 宽高比 | AR Δ% 🆕 | 光流幅度 | 光流ΔY | 变化% | 光流分类 🆕 | 模糊方向 🆕 |\n"
    md += "|------|--------|--------|--------|----------|----------|--------|-------|------------|------------|\n"

    for d in frame_data:
        ar_str = f"{d['aspect_ratio']:.2f}" if d['aspect_ratio'] is not None else "-"
        ar_chg = f"{d['ar_change']:+.1f}%" if d['ar_change'] is not None else "-"
        md += (
            f"| {d['frame']:03d} "
            f"| {d['main_w']}px "
            f"| {d['main_h']}px "
            f"| {ar_str} "
            f"| {ar_chg} "
            f"| {d['flow_mag']:.1f} "
            f"| {d['flow_dy']:+.1f}px "
            f"| {d['diff_pct']:.1f}% "
            f"| {d['flow_pattern']} "
            f"| {d['blur_direction']} |\n"
        )

    # ===== 转场检测 =====
    transitions = [d for d in frame_data if d["diff_pct"] > 25]
    if transitions:
        md += "\n## 🔄 自动检测到的转场/切换点\n\n"
        for t in transitions:
            md += f"- **帧 {t['frame']:03d}**：变化强度 {t['diff_pct']:.1f}%\n"
    
    # ===== 形变事件检测 =====
    deform_events = [d for d in frame_data if d["ar_change"] is not None and abs(d["ar_change"]) > 15]
    if deform_events:
        md += "\n## ⚡ 检测到的形变事件 (宽高比突变 >15%) 🆕\n\n"
        for e in deform_events:
            md += f"- **帧 {e['frame']:03d}**：宽高比变化 {e['ar_change']:+.1f}%，光流分类 = {e['flow_pattern']}\n"

    # ===== 运动趋势 =====
    if frame_data:
        avg_flow_dy = np.mean([d["flow_dy"] for d in frame_data])
        avg_flow_dx = np.mean([d["flow_dx"] for d in frame_data])
        max_flow = max(frame_data, key=lambda d: d["flow_mag"])

        md += "\n## 📊 运动趋势汇总\n\n"
        md += f"- 全局平均光流方向：ΔX={avg_flow_dx:+.1f}px/帧，ΔY={avg_flow_dy:+.1f}px/帧\n"
        md += f"- 运动最剧烈的帧：帧 {max_flow['frame']:03d}（光流幅度 {max_flow['flow_mag']:.1f}）\n"
        
        areas = [(d["main_w"] * d["main_h"]) for d in frame_data if d["main_w"] > 0]
        if areas:
            md += f"- 主体面积范围：最小 {min(areas)}px² → 最大 {max(areas)}px²（比值 {max(areas)/max(min(areas),1):.2f}x）\n"

    # ===== v3: AI 动效行为预判 =====
    candidates = predict_motion_behavior(frame_data)
    if candidates:
        md += "\n## 🤖 动效行为预判 (AI Motion Pattern Classification) 🆕\n\n"
        md += "根据光流方向分类、宽高比变化趋势和运动模糊方向，预判动效类型：\n\n"
        md += "| 候选排序 | 动效类型 | 置信度 | 依据 |\n"
        md += "|---------|---------|--------|------|\n"
        for rank, (name, confidence, reasons) in enumerate(candidates, 1):
            md += f"| #{rank} | {name} | {confidence}% | {', '.join(reasons)} |\n"
        md += "\n> ⚠️ 请结合用户提供的自然语言描述（Step 0）和关键帧图片综合判定。\n"
        md += "> 优先级：**用户描述 > AI 预判 > 纯视觉推断**\n"

    with open(out_file, "w") as f:
        f.write(md)

    print(f"✅ 追踪矩阵 v3 已写入: {out_file}")

if __name__ == "__main__":
    run()
