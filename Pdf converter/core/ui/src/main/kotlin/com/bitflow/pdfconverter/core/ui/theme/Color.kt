package com.bitflow.pdfconverter.core.ui.theme

import androidx.compose.ui.graphics.Color

// ── Brand palette (from BitFlow Nova logo) ──────────────────────────────────
// Dark navy background shades
val NavyDark        = Color(0xFF0F1923)   // deepest background
val Navy            = Color(0xFF1B2838)   // primary dark surface
val NavyLight       = Color(0xFF253545)   // elevated dark surface
val NavyMuted       = Color(0xFF324A5E)   // card / container on dark

// Teal / cyan accent shades (logo text color)
val TealLight       = Color(0xFFA8D8DC)   // light-mode primary
val TealBright      = Color(0xFF8ECFD4)   // dark-mode primary
val TealMuted       = Color(0xFF6BB8BE)   // secondary accent
val TealDark        = Color(0xFF3A8F96)   // pressed / on-primary variant

// ── Legacy aliases (keep for backward-compat) ───────────────────────────────
val PdfBlue80       = TealBright
val PdfBlueGrey80   = Color(0xFFBBC7DB)
val PdfTeal80       = TealLight

val PdfBlue40       = TealDark
val PdfBlueGrey40   = NavyMuted
val PdfTeal40       = TealMuted

// ── Semantic colours ────────────────────────────────────────────────────────
val ErrorRed        = Color(0xFFCF6679)
val ErrorRedLight   = Color(0xFFB00020)
val SuccessGreen    = Color(0xFF2E7D32)
val WarningAmber    = Color(0xFFF57C00)

// ── Neutral ─────────────────────────────────────────────────────────────────
val Surface         = Color(0xFFF5F7FA)
val OnSurface       = Color(0xFF1C1B1F)
val SurfaceVariant  = Color(0xFFE2E8F0)
