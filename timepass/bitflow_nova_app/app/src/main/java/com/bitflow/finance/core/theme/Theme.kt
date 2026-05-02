package com.bitflow.finance.core.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = StitchPrimary,
    onPrimary = StitchTextPrimaryDark,
    primaryContainer = Color(0xFF1E3A8A), // Darker Blue
    onPrimaryContainer = StitchTextPrimaryDark,
    secondary = StitchEmerald,
    onSecondary = StitchBackgroundDark,
    secondaryContainer = Color(0xFF064E3B), // Dark Emerald
    onSecondaryContainer = StitchTextPrimaryDark,
    tertiary = Color(0xFF8B5CF6), // Purple remains as accent
    onTertiary = StitchTextPrimaryDark,
    tertiaryContainer = Color(0xFF4C1D95),
    onTertiaryContainer = StitchTextPrimaryDark,
    error = ErrorRed,
    onError = StitchTextPrimaryDark,
    errorContainer = Color(0xFF7F1D1D),
    onErrorContainer = StitchTextPrimaryDark,
    background = StitchBackgroundDark,
    onBackground = StitchTextPrimaryDark,
    surface = StitchSurfaceDark,
    onSurface = StitchTextPrimaryDark,
    surfaceVariant = StitchSurfaceDark,
    onSurfaceVariant = StitchTextSecondaryDark,
    outline = StitchBorderDark,
    outlineVariant = Color(0xFF2D3748),
    scrim = Color.Black,
    inverseSurface = StitchBackgroundLight,
    inverseOnSurface = StitchBackgroundDark,
    inversePrimary = StitchPrimary,
    surfaceTint = StitchPrimary
)

private val LightColorScheme = lightColorScheme(
    primary = StitchPrimary,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDBEAFE),
    onPrimaryContainer = Color(0xFF1E40AF),
    secondary = StitchEmerald,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFD1FAE5),
    onSecondaryContainer = Color(0xFF065F46),
    tertiary = Color(0xFF7C3AED),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFEDE9FE),
    onTertiaryContainer = Color(0xFF5B21B6),
    error = ErrorRed,
    onError = Color.White,
    errorContainer = Color(0xFFFEE2E2),
    onErrorContainer = Color(0xFF991B1B),
    background = StitchBackgroundLight,
    onBackground = StitchTextPrimaryLight,
    surface = StitchSurfaceLight,
    onSurface = StitchTextPrimaryLight,
    surfaceVariant = Color(0xFFF1F5F9),
    onSurfaceVariant = StitchTextSecondaryLight,
    outline = StitchBorderLight,
    outlineVariant = Color(0xFFCBD5E1),
    scrim = Color(0x99000000),
    inverseSurface = StitchBackgroundDark,
    inverseOnSurface = StitchTextPrimaryDark,
    inversePrimary = StitchPrimary,
    surfaceTint = StitchPrimary
)

@Composable
fun FinanceAppTheme(
    darkTheme: Boolean = true, // Default to Dark Mode as requested
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false, // Disable dynamic color to enforce the custom theme
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb() // Match background for OLED look
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
