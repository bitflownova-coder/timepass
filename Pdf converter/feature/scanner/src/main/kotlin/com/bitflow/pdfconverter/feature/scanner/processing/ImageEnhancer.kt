package com.bitflow.pdfconverter.feature.scanner.processing

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorMatrix
import android.graphics.ColorMatrixColorFilter
import android.graphics.Paint
import com.bitflow.pdfconverter.feature.scanner.contract.ImageFilter

/**
 * Applies post-scan image enhancement filters to a [Bitmap].
 *
 * Filters:
 *  - [ImageFilter.ORIGINAL]    — returns source unchanged
 *  - [ImageFilter.ENHANCED]    — increase contrast + mild sharpening
 *  - [ImageFilter.BLACK_WHITE] — high-contrast B&W (adaptive-like threshold)
 *  - [ImageFilter.GRAYSCALE]   — simple desaturation
 */
object ImageEnhancer {

    fun apply(source: Bitmap, filter: ImageFilter): Bitmap = when (filter) {
        ImageFilter.ORIGINAL    -> source
        ImageFilter.GRAYSCALE   -> applyGrayscale(source)
        ImageFilter.ENHANCED    -> applyEnhanced(source)
        ImageFilter.BLACK_WHITE -> applyBlackWhite(source)
    }

    // ── Grayscale (desaturate) ───────────────────────────────────────────────

    private fun applyGrayscale(src: Bitmap): Bitmap {
        val matrix = ColorMatrix().apply { setSaturation(0f) }
        return applyColorMatrix(src, matrix)
    }

    // ── Enhanced (contrast +60%, brightness +10) ─────────────────────────────

    private fun applyEnhanced(src: Bitmap): Bitmap {
        val contrast = 1.6f
        val brightness = 10f
        val translate = (-(255 * contrast) / 2f) + brightness + (255f / 2f)
        val cm = ColorMatrix(floatArrayOf(
            contrast, 0f, 0f, 0f, translate,
            0f, contrast, 0f, 0f, translate,
            0f, 0f, contrast, 0f, translate,
            0f, 0f, 0f, 1f, 0f
        ))
        return applyColorMatrix(src, cm)
    }

    // ── Black & White (threshold at gray ~128) ───────────────────────────────

    private fun applyBlackWhite(src: Bitmap): Bitmap {
        // First desaturate
        val gray = applyGrayscale(src)
        // Then apply high-contrast matrix to push pixels to pure black/white
        val scale = 10f
        val translate = -1274f   // pulls mid-grays to extremes
        val cm = ColorMatrix(floatArrayOf(
            scale, 0f, 0f, 0f, translate,
            0f, scale, 0f, 0f, translate,
            0f, 0f, scale, 0f, translate,
            0f, 0f, 0f, 1f, 0f
        ))
        return applyColorMatrix(gray, cm)
    }

    // ── Helper ───────────────────────────────────────────────────────────────

    private fun applyColorMatrix(src: Bitmap, matrix: ColorMatrix): Bitmap {
        val result = Bitmap.createBitmap(src.width, src.height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(result)
        val paint  = Paint().apply { colorFilter = ColorMatrixColorFilter(matrix) }
        canvas.drawBitmap(src, 0f, 0f, paint)
        return result
    }
}
