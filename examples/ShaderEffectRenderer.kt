package com.example.motion.shader

import android.graphics.RenderEffect
import android.graphics.RuntimeShader
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer

/* ================================================================ */
/* 🎛️ 动效配置面板 (Tier 3 Config Panel)                            */
/* ================================================================ */
data class ShaderEffectConfig(
    val animDurationMs: Int = 800,
    val intensity: Float = 0.4f,      // 效果强度
    val centerX: Float = 0.5f,        // 效果中心 X（归一化）
    val centerY: Float = 0.5f,        // 效果中心 Y（归一化）
    val radius: Float = 0.6f          // 效果半径（归一化）
)

/* ================================================================ */
/* AGSL 着色器源码（Android Graphics Shading Language）               */
/* 等价于 WebGL 的 Fragment Shader，在 GPU 上逐像素运行               */
/* ================================================================ */

// 鱼眼/径向膨胀着色器
val FISHEYE_SHADER_SRC = """
    uniform shader content;      // 输入内容（当前视图）
    uniform float2 resolution;   // 视口分辨率
    uniform float intensity;     // 形变强度 [0, 1]
    uniform float2 center;       // 形变中心（像素坐标）
    uniform float radius;        // 形变半径（像素）
    
    half4 main(float2 coord) {
        float2 uv = coord / resolution;
        float2 c = center / resolution;
        
        float2 delta = uv - c;
        float dist = length(delta);
        float normR = radius / max(resolution.x, resolution.y);
        
        if (dist < normR) {
            // 二次方径向膨胀：越靠近中心推力越大
            float ratio = dist / normR;
            float distortion = ratio * ratio;
            float2 displaced = c + delta * (distortion / max(ratio, 0.001));
            
            // 混合原始坐标与畸变坐标
            float2 finalUV = mix(uv, displaced, intensity);
            return content.eval(finalUV * resolution);
        }
        
        return content.eval(coord);
    }
""".trimIndent()

// 波纹扭曲着色器
val RIPPLE_SHADER_SRC = """
    uniform shader content;
    uniform float2 resolution;
    uniform float time;          // 动画时间 [0, 1]
    uniform float intensity;
    uniform float2 center;
    
    half4 main(float2 coord) {
        float2 uv = coord / resolution;
        float2 c = center / resolution;
        
        float dist = distance(uv, c);
        float wave = sin(dist * 30.0 - time * 6.28) * intensity * 0.02;
        float falloff = max(0.0, 1.0 - dist * 2.0);
        
        float2 offset = normalize(uv - c) * wave * falloff;
        return content.eval((uv + offset) * resolution);
    }
""".trimIndent()

/* ================================================================ */
/* Compose 集成层                                                    */
/* ================================================================ */

/**
 * 将 AGSL 鱼眼着色器应用到任意 Compose 视图上。
 *
 * 使用方法：
 * ```kotlin
 * Box(modifier = Modifier.fisheyeEffect(progress = animValue)) {
 *     // 你的 UI 内容
 * }
 * ```
 */
@RequiresApi(Build.VERSION_CODES.TIRAMISU) // API 33 for RuntimeShader in Compose
fun Modifier.fisheyeEffect(
    progress: Float,
    config: ShaderEffectConfig = ShaderEffectConfig()
): Modifier {
    if (progress <= 0.001f) return this
    
    val shader = RuntimeShader(FISHEYE_SHADER_SRC)
    
    return this.graphicsLayer {
        shader.setFloatUniform("resolution", size.width, size.height)
        shader.setFloatUniform("intensity", config.intensity * progress)
        shader.setFloatUniform("center",
            size.width * config.centerX,
            size.height * config.centerY
        )
        shader.setFloatUniform("radius",
            maxOf(size.width, size.height) * config.radius
        )
        
        renderEffect = RenderEffect
            .createRuntimeShaderEffect(shader, "content")
            .asComposeRenderEffect()
    }
}

/**
 * 波纹扭曲效果。
 */
@RequiresApi(Build.VERSION_CODES.TIRAMISU)
fun Modifier.rippleDistortion(
    time: Float,
    config: ShaderEffectConfig = ShaderEffectConfig()
): Modifier {
    if (config.intensity <= 0.001f) return this
    
    val shader = RuntimeShader(RIPPLE_SHADER_SRC)
    
    return this.graphicsLayer {
        shader.setFloatUniform("resolution", size.width, size.height)
        shader.setFloatUniform("time", time)
        shader.setFloatUniform("intensity", config.intensity)
        shader.setFloatUniform("center",
            size.width * config.centerX,
            size.height * config.centerY
        )
        
        renderEffect = RenderEffect
            .createRuntimeShaderEffect(shader, "content")
            .asComposeRenderEffect()
    }
}
