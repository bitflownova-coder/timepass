package com.bitflow.pdfconverter.feature.scanner.processing

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.Matrix
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Applies a perspective correction transform to flatten a scanned document.
 *
 * The four source [corners] represent (in order): Top-Left, Top-Right, Bottom-Right, Bottom-Left.
 * The output is a new [Bitmap] with aspect ratio derived from the detected quad dimensions.
 */
object PerspectiveCorrector {

    /**
     * Returns a perspective-corrected bitmap for the given [corners] on [source].
     * Falls back to the original bitmap if the computation fails (e.g. degenerate quad).
     */
    fun correct(source: Bitmap, corners: List<PointF>): Bitmap {
        require(corners.size == 4) { "Expected exactly 4 corners" }
        val (tl, tr, br, bl) = corners

        val widthA  = distance(br, bl)
        val widthB  = distance(tr, tl)
        val maxWidth = max(widthA, widthB).toInt().coerceAtLeast(1)

        val heightA = distance(tr, br)
        val heightB = distance(tl, bl)
        val maxHeight = max(heightA, heightB).toInt().coerceAtLeast(1)

        // Build a 3x3 perspective matrix using Android's Matrix polyToPoly
        val src = floatArrayOf(
            tl.x, tl.y,
            tr.x, tr.y,
            br.x, br.y,
            bl.x, bl.y
        )
        val dst = floatArrayOf(
            0f, 0f,
            maxWidth.toFloat(), 0f,
            maxWidth.toFloat(), maxHeight.toFloat(),
            0f, maxHeight.toFloat()
        )

        val matrix = Matrix()
        val success = matrix.setPolyToPoly(src, 0, dst, 0, 4)
        if (!success) return source

        return Bitmap.createBitmap(source, 0, 0, source.width, source.height, matrix, true)
            .let { raw ->
                // Crop to exact target dimensions
                if (raw.width >= maxWidth && raw.height >= maxHeight) {
                    Bitmap.createBitmap(raw, 0, 0, maxWidth, maxHeight)
                } else raw
            }
    }

    private fun distance(a: PointF, b: PointF): Float {
        val dx = (a.x - b.x)
        val dy = (a.y - b.y)
        return sqrt(dx * dx + dy * dy)
    }
}
