package com.bitflow.finance.ui.screens.dev_tools

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ColorConverterScreen(
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    
    var hexInput by remember { mutableStateOf("") }
    var redValue by remember { mutableStateOf(128f) }
    var greenValue by remember { mutableStateOf(128f) }
    var blueValue by remember { mutableStateOf(128f) }
    var alphaValue by remember { mutableStateOf(255f) }
    
    // Update from RGB sliders
    val currentColor = Color(
        red = redValue.toInt(),
        green = greenValue.toInt(),
        blue = blueValue.toInt(),
        alpha = alphaValue.toInt()
    )
    
    // Format values
    val hexString = String.format("#%02X%02X%02X", redValue.toInt(), greenValue.toInt(), blueValue.toInt())
    val hexWithAlpha = String.format("#%02X%02X%02X%02X", alphaValue.toInt(), redValue.toInt(), greenValue.toInt(), blueValue.toInt())
    val rgbString = "rgb(${redValue.toInt()}, ${greenValue.toInt()}, ${blueValue.toInt()})"
    val rgbaString = "rgba(${redValue.toInt()}, ${greenValue.toInt()}, ${blueValue.toInt()}, ${String.format("%.2f", alphaValue / 255f)})"
    val composeColor = "Color(0x${hexWithAlpha.removePrefix("#")})"
    val composeColorRgb = "Color(${redValue.toInt()}, ${greenValue.toInt()}, ${blueValue.toInt()})"
    
    // HSL calculation
    val hsl = rgbToHsl(redValue.toInt(), greenValue.toInt(), blueValue.toInt())
    val hslString = "hsl(${hsl.first.roundToInt()}, ${(hsl.second * 100).roundToInt()}%, ${(hsl.third * 100).roundToInt()}%)"
    
    // Complementary color
    val complementaryHue = (hsl.first + 180) % 360
    val complementaryRgb = hslToRgb(complementaryHue, hsl.second, hsl.third)
    val complementaryColor = Color(complementaryRgb[0], complementaryRgb[1], complementaryRgb[2])
    
    // Contrast checker (against white and black)
    val luminance = calculateLuminance(redValue.toInt(), greenValue.toInt(), blueValue.toInt())
    val contrastWithWhite = calculateContrast(luminance, 1.0)
    val contrastWithBlack = calculateContrast(luminance, 0.0)
    
    fun updateFromHex(hex: String) {
        val cleanHex = hex.removePrefix("#").uppercase()
        if (cleanHex.length == 6) {
            try {
                val r = cleanHex.substring(0, 2).toInt(16)
                val g = cleanHex.substring(2, 4).toInt(16)
                val b = cleanHex.substring(4, 6).toInt(16)
                redValue = r.toFloat()
                greenValue = g.toFloat()
                blueValue = b.toFloat()
            } catch (e: Exception) { }
        } else if (cleanHex.length == 8) {
            try {
                val a = cleanHex.substring(0, 2).toInt(16)
                val r = cleanHex.substring(2, 4).toInt(16)
                val g = cleanHex.substring(4, 6).toInt(16)
                val b = cleanHex.substring(6, 8).toInt(16)
                alphaValue = a.toFloat()
                redValue = r.toFloat()
                greenValue = g.toFloat()
                blueValue = b.toFloat()
            } catch (e: Exception) { }
        }
    }
    
    fun copyToClipboard(text: String) {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("Color", text)
        clipboard.setPrimaryClip(clip)
        Toast.makeText(context, "Copied: $text", Toast.LENGTH_SHORT).show()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Color Converter", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Color Preview
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = currentColor
                    )
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(120.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = hexString,
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            color = if (luminance > 0.5) Color.Black else Color.White
                        )
                    }
                }
            }
            
            // HEX Input
            item {
                OutlinedTextField(
                    value = hexInput,
                    onValueChange = {
                        hexInput = it
                        updateFromHex(it)
                    },
                    label = { Text("Enter HEX (#RRGGBB or #AARRGGBB)") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    leadingIcon = { Text("#", fontFamily = FontFamily.Monospace) },
                    trailingIcon = {
                        IconButton(onClick = { updateFromHex(hexInput) }) {
                            Icon(Icons.Default.Refresh, "Apply")
                        }
                    }
                )
            }
            
            // RGB Sliders
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("RGB Sliders", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        ColorSlider(
                            label = "Red",
                            value = redValue,
                            onValueChange = { redValue = it },
                            color = Color.Red
                        )
                        
                        ColorSlider(
                            label = "Green",
                            value = greenValue,
                            onValueChange = { greenValue = it },
                            color = Color.Green
                        )
                        
                        ColorSlider(
                            label = "Blue",
                            value = blueValue,
                            onValueChange = { blueValue = it },
                            color = Color.Blue
                        )
                        
                        ColorSlider(
                            label = "Alpha",
                            value = alphaValue,
                            onValueChange = { alphaValue = it },
                            color = Color.Gray
                        )
                    }
                }
            }
            
            // Color Formats
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("Color Formats", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        ColorFormatRow("HEX", hexString) { copyToClipboard(hexString) }
                        ColorFormatRow("HEX (with Alpha)", hexWithAlpha) { copyToClipboard(hexWithAlpha) }
                        ColorFormatRow("RGB", rgbString) { copyToClipboard(rgbString) }
                        ColorFormatRow("RGBA", rgbaString) { copyToClipboard(rgbaString) }
                        ColorFormatRow("HSL", hslString) { copyToClipboard(hslString) }
                        ColorFormatRow("Compose", composeColor) { copyToClipboard(composeColor) }
                        ColorFormatRow("Compose RGB", composeColorRgb) { copyToClipboard(composeColorRgb) }
                    }
                }
            }
            
            // Complementary Color
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Complementary Color", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            Column(
                                modifier = Modifier.weight(1f),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(60.dp)
                                        .clip(CircleShape)
                                        .background(currentColor)
                                        .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape)
                                )
                                Text("Original", style = MaterialTheme.typography.labelSmall)
                            }
                            
                            Column(
                                modifier = Modifier.weight(1f),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(60.dp)
                                        .clip(CircleShape)
                                        .background(complementaryColor)
                                        .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape)
                                        .clickable {
                                            val compHex = String.format("#%02X%02X%02X", complementaryRgb[0], complementaryRgb[1], complementaryRgb[2])
                                            copyToClipboard(compHex)
                                        }
                                )
                                Text("Complementary", style = MaterialTheme.typography.labelSmall)
                            }
                        }
                    }
                }
            }
            
            // Contrast Checker
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Contrast Checker (WCAG)", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        ContrastRow(
                            label = "With White",
                            ratio = contrastWithWhite,
                            backgroundColor = currentColor,
                            textColor = Color.White
                        )
                        
                        ContrastRow(
                            label = "With Black",
                            ratio = contrastWithBlack,
                            backgroundColor = currentColor,
                            textColor = Color.Black
                        )
                    }
                }
            }
            
            // Material Colors Palette
            item {
                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("Material Colors", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(materialColors) { (name, color) ->
                                Column(
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    modifier = Modifier.clickable {
                                        val argb = color.toArgb()
                                        redValue = ((argb shr 16) and 0xFF).toFloat()
                                        greenValue = ((argb shr 8) and 0xFF).toFloat()
                                        blueValue = (argb and 0xFF).toFloat()
                                    }
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(48.dp)
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(color)
                                    )
                                    Text(
                                        text = name,
                                        style = MaterialTheme.typography.labelSmall,
                                        maxLines = 1
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ColorSlider(
    label: String,
    value: Float,
    onValueChange: (Float) -> Unit,
    color: Color
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.width(50.dp)
        )
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = 0f..255f,
            modifier = Modifier.weight(1f),
            colors = SliderDefaults.colors(
                thumbColor = color,
                activeTrackColor = color
            )
        )
        Text(
            text = value.toInt().toString(),
            style = MaterialTheme.typography.bodyMedium,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.width(36.dp)
        )
    }
}

@Composable
private fun ColorFormatRow(
    label: String,
    value: String,
    onCopy: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onCopy() }
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium,
                fontFamily = FontFamily.Monospace
            )
            Icon(
                Icons.Default.ContentCopy,
                contentDescription = "Copy",
                modifier = Modifier.size(16.dp),
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
private fun ContrastRow(
    label: String,
    ratio: Double,
    backgroundColor: Color,
    textColor: Color
) {
    val passesAA = ratio >= 4.5
    val passesAAA = ratio >= 7.0
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(backgroundColor),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "Aa",
                    color = textColor,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
            }
            Column {
                Text(label, style = MaterialTheme.typography.bodyMedium)
                Text(
                    String.format("%.2f:1", ratio),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        }
        
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Surface(
                color = if (passesAA) Color(0xFF10B981) else Color(0xFFEF4444),
                shape = RoundedCornerShape(4.dp)
            ) {
                Text(
                    text = if (passesAA) "AA ✓" else "AA ✗",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
            Surface(
                color = if (passesAAA) Color(0xFF10B981) else Color(0xFFEF4444),
                shape = RoundedCornerShape(4.dp)
            ) {
                Text(
                    text = if (passesAAA) "AAA ✓" else "AAA ✗",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color.White,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

// Color conversion functions
private fun rgbToHsl(r: Int, g: Int, b: Int): Triple<Float, Float, Float> {
    val rf = r / 255f
    val gf = g / 255f
    val bf = b / 255f
    
    val max = maxOf(rf, gf, bf)
    val min = minOf(rf, gf, bf)
    val l = (max + min) / 2
    
    if (max == min) {
        return Triple(0f, 0f, l)
    }
    
    val d = max - min
    val s = if (l > 0.5f) d / (2 - max - min) else d / (max + min)
    
    val h = when (max) {
        rf -> ((gf - bf) / d + (if (gf < bf) 6 else 0)) * 60
        gf -> ((bf - rf) / d + 2) * 60
        else -> ((rf - gf) / d + 4) * 60
    }
    
    return Triple(h, s, l)
}

private fun hslToRgb(h: Float, s: Float, l: Float): IntArray {
    if (s == 0f) {
        val v = (l * 255).toInt()
        return intArrayOf(v, v, v)
    }
    
    val q = if (l < 0.5f) l * (1 + s) else l + s - l * s
    val p = 2 * l - q
    
    fun hueToRgb(p: Float, q: Float, t: Float): Float {
        var tt = t
        if (tt < 0) tt += 1
        if (tt > 1) tt -= 1
        return when {
            tt < 1f/6 -> p + (q - p) * 6 * tt
            tt < 1f/2 -> q
            tt < 2f/3 -> p + (q - p) * (2f/3 - tt) * 6
            else -> p
        }
    }
    
    val hNorm = h / 360f
    val r = (hueToRgb(p, q, hNorm + 1f/3) * 255).toInt()
    val g = (hueToRgb(p, q, hNorm) * 255).toInt()
    val b = (hueToRgb(p, q, hNorm - 1f/3) * 255).toInt()
    
    return intArrayOf(r, g, b)
}

private fun calculateLuminance(r: Int, g: Int, b: Int): Double {
    fun adjust(c: Int): Double {
        val s = c / 255.0
        return if (s <= 0.03928) s / 12.92 else Math.pow((s + 0.055) / 1.055, 2.4)
    }
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
}

private fun calculateContrast(l1: Double, l2: Double): Double {
    val lighter = maxOf(l1, l2)
    val darker = minOf(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
}

private val materialColors = listOf(
    "Red" to Color(0xFFF44336),
    "Pink" to Color(0xFFE91E63),
    "Purple" to Color(0xFF9C27B0),
    "Indigo" to Color(0xFF3F51B5),
    "Blue" to Color(0xFF2196F3),
    "Cyan" to Color(0xFF00BCD4),
    "Teal" to Color(0xFF009688),
    "Green" to Color(0xFF4CAF50),
    "Lime" to Color(0xFFCDDC39),
    "Yellow" to Color(0xFFFFEB3B),
    "Amber" to Color(0xFFFFC107),
    "Orange" to Color(0xFFFF9800),
    "Brown" to Color(0xFF795548),
    "Grey" to Color(0xFF9E9E9E)
)
