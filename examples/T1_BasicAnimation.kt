import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.Application
import androidx.compose.ui.window.singleWindowApplication

@Composable
fun BasicAnimationExample() {
    var scale by remember { mutableStateOf(1f) }
    var rotation by remember { mutableStateOf(0f) }
    var offsetX by remember { mutableStateOf(0f) }
    var offsetY by remember { mutableStateOf(0f) }
    
    val scaleAnim = remember { Animatable(scale) }
    val rotationAnim = remember { Animatable(rotation) }
    val offsetXAnim = remember { Animatable(offsetX) }
    val offsetYAnim = remember { Animatable(offsetY) }

    LaunchedEffect(Unit) {
        scaleAnim.animateTo(
            targetValue = 1.5f,
            animationSpec = spring(dampingRatio = 0.5f)
        )
        scaleAnim.animateTo(1f, animationSpec = spring())
        rotationAnim.animateTo(360f, animationSpec = tween(durationMillis = 2000))
        offsetXAnim.animateTo(100f, animationSpec = tween(durationMillis = 1000))
        offsetYAnim.animateTo(100f, animationSpec = tween(durationMillis = 1000))
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.LightGray),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .size(100.dp)
                .background(Color.Blue)
                .graphicsLayer(
                    scaleX = scaleAnim.value,
                    scaleY = scaleAnim.value,
                    translationX = offsetXAnim.value,
                    translationY = offsetYAnim.value,
                    rotationZ = rotationAnim.value
                )
        )
    }
}

fun main() = singleWindowApplication {
    BasicAnimationExample()
}