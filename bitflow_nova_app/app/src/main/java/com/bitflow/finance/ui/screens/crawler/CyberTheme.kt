package com.bitflow.finance.ui.screens.crawler

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.Canvas

// ─────────────────────────────────────────────────────────────
//  Cyber color palette
// ─────────────────────────────────────────────────────────────
object Cyber {

    // Backgrounds
    val Bg             = Color(0xFF0D1117)   // GitHub-dark style background
    val BgCard         = Color(0xFF161B22)   // Card surface
    val BgElevated     = Color(0xFF21262D)   // Elevated / dialog surface

    // Neon accents
    val Green          = Color(0xFF39FF2A)   // Matrix / neon green (active, success)
    val GreenMuted     = Color(0xFF1A7A12)   // Darker green for backgrounds
    val GreenDim       = Color(0xFF39FF2A).copy(alpha = 0.12f)

    val Cyan           = Color(0xFF00D4FF)   // Info / running state
    val CyanDim        = Color(0xFF00D4FF).copy(alpha = 0.12f)

    val Red            = Color(0xFFFF2D55)   // Critical / error
    val RedDim         = Color(0xFFFF2D55).copy(alpha = 0.12f)

    val Orange         = Color(0xFFFF6B35)   // High severity
    val OrangeDim      = Color(0xFFFF6B35).copy(alpha = 0.12f)

    val Yellow         = Color(0xFFFFD600)   // Medium severity / warning
    val YellowDim      = Color(0xFFFFD600).copy(alpha = 0.12f)

    val Blue           = Color(0xFF4493F8)   // Information / primary
    val BlueDim        = Color(0xFF4493F8).copy(alpha = 0.12f)

    val Purple         = Color(0xFFBC8CFF)   // OSINT / passive recon
    val PurpleDim      = Color(0xFFBC8CFF).copy(alpha = 0.12f)

    // Text
    val TextPrimary    = Color(0xFFE6EDF3)
    val TextSecondary  = Color(0xFF8B949E)
    val TextMuted      = Color(0xFF484F58)
    val TextCode       = Color(0xFF79C0FF)   // Monospace / code snippets

    // Borders
    val Border         = Color(0xFF30363D)
    val BorderActive   = Green.copy(alpha = 0.5f)
    val BorderDanger   = Red.copy(alpha = 0.5f)

    // Severity
    fun severityColor(severity: String): Color = when (severity.lowercase()) {
        "critical"  -> Red
        "high"      -> Orange
        "medium"    -> Yellow
        "low"       -> Cyan
        "info"      -> Blue
        else        -> TextSecondary
    }

    fun severityDim(severity: String): Color = when (severity.lowercase()) {
        "critical"  -> RedDim
        "high"      -> OrangeDim
        "medium"    -> YellowDim
        "low"       -> CyanDim
        "info"      -> BlueDim
        else        -> TextMuted.copy(alpha = 0.12f)
    }

    // Grade → colour
    fun gradeColor(grade: String): Color = when (grade.uppercase()) {
        "A+", "A" -> Green
        "B"       -> Cyan
        "C"       -> Yellow
        "D"       -> Orange
        "F"       -> Red
        else       -> TextSecondary
    }
}

// ─────────────────────────────────────────────────────────────
//  Typography helpers
// ─────────────────────────────────────────────────────────────

/** Monospace terminal-style text */
@Composable
fun TerminalText(
    text: String,
    color: Color = Cyber.TextCode,
    fontSize: TextUnit = 12.sp,
    fontWeight: FontWeight = FontWeight.Normal,
    modifier: Modifier = Modifier
) {
    Text(
        text = text,
        style = TextStyle(
            fontFamily = FontFamily.Monospace,
            fontSize = fontSize,
            fontWeight = fontWeight,
            color = color
        ),
        modifier = modifier
    )
}

/** Neon heading — used for card titles / section headers */
@Composable
fun NeonLabel(
    text: String,
    color: Color = Cyber.Green,
    fontSize: TextUnit = 11.sp,
    modifier: Modifier = Modifier
) {
    Text(
        text = text.uppercase(),
        style = TextStyle(
            fontFamily = FontFamily.Monospace,
            fontSize = fontSize,
            fontWeight = FontWeight.Bold,
            color = color,
            letterSpacing = 1.5.sp
        ),
        modifier = modifier
    )
}

// ─────────────────────────────────────────────────────────────
//  Layout composables
// ─────────────────────────────────────────────────────────────

/**
 * Dark card with an optional left neon border accent and top glow.
 */
@Composable
fun CyberCard(
    modifier: Modifier = Modifier,
    accent: Color = Cyber.Green,
    glowIntensity: Float = 0.3f,
    leftBorderWidth: Dp = 3.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    val glowColor = accent.copy(alpha = glowIntensity)
    Card(
        modifier = modifier
            .drawBehind {
                // Subtle top-edge glow
                drawRect(
                    brush = Brush.verticalGradient(
                        colors = listOf(glowColor, Color.Transparent),
                        startY = 0f,
                        endY = 60f
                    )
                )
            }
            .border(
                width = 1.dp,
                color = Cyber.Border,
                shape = RoundedCornerShape(12.dp)
            ),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Cyber.BgCard),
        elevation = CardDefaults.cardElevation(0.dp)
    ) {
        Row {
            // Left accent bar
            if (leftBorderWidth > 0.dp) {
                Box(
                    modifier = Modifier
                        .width(leftBorderWidth)
                        .fillMaxHeight()
                        .background(
                            brush = Brush.verticalGradient(
                                colors = listOf(accent, accent.copy(alpha = 0.3f))
                            )
                        )
                )
            }
            Column(content = content)
        }
    }
}

/**
 * Simple dark surface card – no left border, just dark bg + border.
 */
@Composable
fun CyberSurface(
    modifier: Modifier = Modifier,
    borderColor: Color = Cyber.Border,
    content: @Composable BoxScope.() -> Unit
) {
    Box(
        modifier = modifier
            .background(Cyber.BgCard, RoundedCornerShape(12.dp))
            .border(1.dp, borderColor, RoundedCornerShape(12.dp)),
        content = content
    )
}

/**
 * Horizontal divider matching the cyber separator style.
 */
@Composable
fun CyberDivider(
    modifier: Modifier = Modifier,
    color: Color = Cyber.Border
) {
    Divider(modifier = modifier, thickness = 1.dp, color = color)
}

// ─────────────────────────────────────────────────────────────
//  Animated composables
// ─────────────────────────────────────────────────────────────

/**
 * A pulsing neon dot — used to indicate active scanning.
 * Optional: set [rings] = true for a radar-ring pulse effect.
 */
@Composable
fun ScannerPulse(
    color: Color = Cyber.Green,
    dotSize: Dp = 10.dp,
    rings: Boolean = false,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(900, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_alpha"
    )
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.4f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = EaseOutCirc),
            repeatMode = RepeatMode.Restart
        ),
        label = "ring_scale"
    )

    Box(modifier = modifier.size(dotSize * 3), contentAlignment = Alignment.Center) {
        if (rings) {
            Canvas(modifier = Modifier.size(dotSize * 3)) {
                val r = (dotSize * 1.5f).toPx() * scale
                drawCircle(
                    color = color.copy(alpha = (1f - scale / 1.5f).coerceAtLeast(0f) * 0.4f),
                    radius = r,
                    style = Stroke(width = 1.5.dp.toPx())
                )
            }
        }
        Box(
            modifier = Modifier
                .size(dotSize)
                .background(color.copy(alpha = alpha), shape = androidx.compose.foundation.shape.CircleShape)
        )
    }
}

/**
 * Severity badge — coloured rounded chip for Critical/High/Medium/Low/Info.
 */
@Composable
fun SeverityBadge(severity: String, modifier: Modifier = Modifier) {
    val color = Cyber.severityColor(severity)
    val bg    = Cyber.severityDim(severity)
    Surface(
        modifier = modifier,
        color = bg,
        shape = RoundedCornerShape(4.dp)
    ) {
        Text(
            text = severity.uppercase(),
            style = TextStyle(
                fontFamily = FontFamily.Monospace,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = color,
                letterSpacing = 0.8.sp
            ),
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 3.dp)
        )
    }
}

/**
 * Stat cell for the "command center" header area.
 */
@Composable
fun CyberStatCell(
    value: String,
    label: String,
    color: Color = Cyber.Green,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = value,
            style = TextStyle(
                fontFamily = FontFamily.Monospace,
                fontSize = 22.sp,
                fontWeight = FontWeight.Black,
                color = color
            )
        )
        Text(
            text = label.uppercase(),
            style = TextStyle(
                fontFamily = FontFamily.Monospace,
                fontSize = 9.sp,
                fontWeight = FontWeight.Normal,
                color = Cyber.TextSecondary,
                letterSpacing = 1.sp
            )
        )
    }
}

/**
 * A reusable section header bar: "// SECTION_TITLE"
 */
@Composable
fun CyberSectionHeader(
    title: String,
    color: Color = Cyber.Green,
    modifier: Modifier = Modifier,
    action: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "// ",
                style = TextStyle(
                    fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            )
            Text(
                text = title.uppercase(),
                style = TextStyle(
                    fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary,
                    letterSpacing = 1.sp
                )
            )
        }
        action?.invoke()
    }
}

/**
 * A threat-level indicator bar (used in session cards etc.).
 * Renders a series of colored segments (like an EQ meter).
 */
@Composable
fun ThreatBar(
    threatLevel: Int,       // 0-100
    modifier: Modifier = Modifier,
    segments: Int = 10
) {
    val filled = (threatLevel / 100f * segments).toInt().coerceIn(0, segments)
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        repeat(segments) { i ->
            val active = i < filled
            val segColor = when {
                i < segments * 0.4  -> Cyber.Green
                i < segments * 0.7  -> Cyber.Yellow
                i < segments * 0.9  -> Cyber.Orange
                else                 -> Cyber.Red
            }
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height(6.dp)
                    .background(
                        color = if (active) segColor else Cyber.Border,
                        shape = RoundedCornerShape(2.dp)
                    )
            )
        }
    }
}
