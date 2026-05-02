package com.bitflow.pdfconverter.feature.scanner.processing

import android.graphics.Bitmap
import android.graphics.PointF
import android.graphics.RectF

/**
 * Lightweight document-edge detector that works entirely with Android framework APIs
 * (no OpenCV dependency required for basic scanning).
 *
 * Strategy:
 *  1. Convert to grayscale pixel array
 *  2. Apply Sobel-like edge magnitude map
 *  3. Find the dominant axis-aligned bounding rectangle of strong edges
 *  4. Return it as 4 corner points (TL, TR, BR, BL)
 *
 * For high-accuracy production use, replace [detectEdges] with an OpenCV-based
 * implementation using `Imgproc.findContours` + `approxPolyDP`.
 */
object EdgeDetector {

    private const val EDGE_THRESHOLD = 60

    /**
     * Detects the document boundary in [bitmap] and returns 4 corner [PointF]s
     * in order: Top-Left, Top-Right, Bottom-Right, Bottom-Left.
     *
     * Falls back to full-image corners if detection fails.
     */
    fun detectEdges(bitmap: Bitmap): List<PointF> {
        val w = bitmap.width
        val h = bitmap.height

        val pixels = IntArray(w * h)
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h)

        val gray = IntArray(w * h) { i ->
            val p = pixels[i]
            val r = (p shr 16) and 0xFF
            val g = (p shr 8)  and 0xFF
            val b = p and 0xFF
            (0.299 * r + 0.587 * g + 0.114 * b).toInt()
        }

        var minX = w; var maxX = 0
        var minY = h; var maxY = 0

        for (y in 1 until h - 1) {
            for (x in 1 until w - 1) {
                val gx = -gray[(y - 1) * w + (x - 1)] - 2 * gray[y * w + (x - 1)] - gray[(y + 1) * w + (x - 1)] +
                          gray[(y - 1) * w + (x + 1)] + 2 * gray[y * w + (x + 1)] + gray[(y + 1) * w + (x + 1)]
                val gy = -gray[(y - 1) * w + (x - 1)] - 2 * gray[(y - 1) * w + x] - gray[(y - 1) * w + (x + 1)] +
                          gray[(y + 1) * w + (x - 1)] + 2 * gray[(y + 1) * w + x] + gray[(y + 1) * w + (x + 1)]
                val mag = Math.sqrt((gx * gx + gy * gy).toDouble()).toInt()
                if (mag > EDGE_THRESHOLD) {
                    if (x < minX) minX = x
                    if (x > maxX) maxX = x
                    if (y < minY) minY = y
                    if (y > maxY) maxY = y
                }
            }
        }

        // Fallback to full image if edges are too close to border (poor detection)
        val marginFraction = 0.05f
        val marginX = (w * marginFraction).toInt()
        val marginY = (h * marginFraction).toInt()
        if (maxX - minX < w * 0.3 || maxY - minY < h * 0.3) {
            return fullImageCorners(w.toFloat(), h.toFloat(), marginX.toFloat(), marginY.toFloat())
        }

        return listOf(
            PointF(minX.toFloat(), minY.toFloat()), // TL
            PointF(maxX.toFloat(), minY.toFloat()), // TR
            PointF(maxX.toFloat(), maxY.toFloat()), // BR
            PointF(minX.toFloat(), maxY.toFloat())  // BL
        )
    }

    private fun fullImageCorners(w: Float, h: Float, margin: Float, marginY: Float) = listOf(
        PointF(margin, marginY),
        PointF(w - margin, marginY),
        PointF(w - margin, h - marginY),
        PointF(margin, h - marginY)
    )
}
