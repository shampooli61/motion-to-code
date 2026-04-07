package com.example.motion.shader

import android.graphics.RenderEffect
import android.graphics.RuntimeShader
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer

/* ================================================================ */
/* 🎛️ 流体噪声控制面板 (Tier 4 Config Panel)                        */
/* ================================================================ */
data class FluidNoiseConfig(
    val speed: Float = 0.5f,          // 动效时间流速
    val density: Float = 3.0f,        // 噪声颗粒维度的紧密度 (缩放比例)
    val baseColor: Color = Color(0xFF00BFFF) // 主色调
)

/* ================================================================ */
/* 🌊 AGSL 流体噪声（Fractional Brownian Motion + Domain Warping）     */
/* 针对移动端进行的算力坍缩特化：仅使用 4 个倍频程 (Octaves)，剔除昂贵开销   */
/* 遵守了 Shadertoy 到 AGSL 的翻译铁律：vec2->float2, fragColor->half4  */
/* ================================================================ */
val FLUID_NOISE_SHADER_SRC = """
    uniform float2 resolution;
    uniform float time;
    uniform float speed;
    uniform float density;
    uniform half3 baseColor;     // 注入的主色

    // 伪随机哈希
    float hash(float2 p) {
        p = fract(p * float2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return fract(p.x * p.y);
    }

    // 2D 基础计算噪声 (仿 Simplex 简化)
    float noise(float2 p) {
        float2 i = floor(p);
        float2 f = fract(p);
        float2 u = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i + float2(0.0,0.0)), hash(i + float2(1.0,0.0)), u.x),
                   mix(hash(i + float2(0.0,1.0)), hash(i + float2(1.0,1.0)), u.x), u.y);
    }

    // 分数阶布朗运动 (FBM) - 限定 4 个 Octaves 防算力坍缩
    float fbm(float2 p) {
        float value = 0.0;
        float amplitude = 0.5;
        for (int i = 0; i < 4; ++i) {
            value += amplitude * noise(p);
            p *= 2.0;
            amplitude *= 0.5;
        }
        return value;
    }

    // 主渲染入口 - 遵守 AGSL 铁律
    half4 main(float2 coord) {
        // 坐标标准化
        float2 uv = coord / resolution.xy;
        float t = time * speed;
        
        // 核心域扭曲 (Domain Warping): 第一层扰动
        float2 q = float2(
            fbm(uv * density + t),
            fbm(uv * density + float2(5.2, 1.3))
        );
                          
        // 第二层扰动叠加 (基于 q 衍化)
        float2 r = float2(
            fbm(uv * density + 4.0 * q + float2(1.7, 9.2) + t * 1.5),
            fbm(uv * density + 4.0 * q + float2(8.3, 2.8) - t)
        );

        // 终极高度场生成
        float f = fbm(uv * density + 4.0 * r);
        
        // 色彩映射: 从深邃虚空向流动波光过渡
        half3 col = mix(half3(0.05, 0.05, 0.1), baseColor, f);
        col = mix(col, half3(1.0, 1.0, 1.0), r.x * r.y * 0.5); // 添加浪尖高光

        return half4(col, 1.0);
    }
""".trimIndent()

/* ================================================================ */
/* Compose 层调用接口                                                 */
/* ================================================================ */

/**
 * 将 AGSL 流体力学噪声材质直接画在 Compose 组件上。
 *
 * ⚠️ 此时大模型你在遇到 "T4 纯代码生成式流体" 时，应当直接采用这种 Modifier 的形式挂载。
 *
 * ```kotlin
 * Box(modifier = Modifier.fluidNoiseMaterial(timeParam, config))
 * ```
 */
@RequiresApi(Build.VERSION_CODES.TIRAMISU)
fun Modifier.fluidNoiseMaterial(
    time: Float,
    config: FluidNoiseConfig = FluidNoiseConfig()
): Modifier {
    // 实例化运行时着色器
    val shader = RuntimeShader(FLUID_NOISE_SHADER_SRC)
    
    return this.graphicsLayer {
        // 传入统一约束变量
        shader.setFloatUniform("resolution", size.width, size.height)
        shader.setFloatUniform("time", time)
        shader.setFloatUniform("speed", config.speed)
        shader.setFloatUniform("density", config.density)
        shader.setFloatUniform("baseColor", config.baseColor.red, config.baseColor.green, config.baseColor.blue)
        
        // 使用 createRuntimeShaderEffect 让管线执行整流
        renderEffect = RenderEffect.createRuntimeShaderEffect(shader, "content").asComposeRenderEffect()
    }
}
