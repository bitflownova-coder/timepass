package com.bitflow.pdfconverter.core.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary            = TealBright,
    onPrimary          = NavyDark,
    primaryContainer   = NavyMuted,
    onPrimaryContainer = TealLight,
    secondary          = TealMuted,
    onSecondary        = NavyDark,
    tertiary           = TealLight,
    background         = NavyDark,
    onBackground       = Color(0xFFE2E8F0),
    surface            = Navy,
    onSurface          = Color(0xFFE2E8F0),
    surfaceVariant     = NavyLight,
    onSurfaceVariant   = Color(0xFFB0BEC5),
    error              = ErrorRed,
)

private val LightColorScheme = lightColorScheme(
    primary            = TealDark,
    onPrimary          = Color.White,
    primaryContainer   = Color(0xFFD6F2F4),
    onPrimaryContainer = Color(0xFF0D3D40),
    secondary          = NavyMuted,
    onSecondary        = Color.White,
    tertiary           = TealMuted,
    background         = Surface,
    onBackground       = OnSurface,
    surface            = Surface,
    onSurface          = OnSurface,
    surfaceVariant     = SurfaceVariant,
    onSurfaceVariant   = Color(0xFF49454F),
    error              = ErrorRedLight,
)

@Composable
fun PdfConverterTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else      -> LightColorScheme
    }

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.surface.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography  = PdfConverterTypography,
        content     = content
    )
}
