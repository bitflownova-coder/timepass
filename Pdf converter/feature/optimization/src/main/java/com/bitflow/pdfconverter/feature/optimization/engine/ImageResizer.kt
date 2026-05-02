package com.bitflow.pdfconverter.feature.optimization.engine

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import java.io.ByteArrayOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ImageResizer @Inject constructor() {
    /**
     * Downscales [source] to [targetDpi] assuming it was originally captured at [sourceDpi].
     * Returns the same bitmap if no downscale is needed.
     */
    fun resize(source: Bitmap, sourceDpi: Int, targetDpi: Int): Bitmap {
        if (targetDpi >= sourceDpi) return source
        val scale = targetDpi.toFloat() / sourceDpi.toFloat()
        val newWidth = (source.width * scale).toInt().coerceAtLeast(1)
        val newHeight = (source.height * scale).toInt().coerceAtLeast(1)
        return Bitmap.createScaledBitmap(source, newWidth, newHeight, true)
    }

    /**
     * Re-encodes [bitmap] as JPEG at [quality] (0–100) and returns the byte array.
     */
    fun encodeJpeg(bitmap: Bitmap, quality: Int): ByteArray {
        val baos = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, baos)
        return baos.toByteArray()
    }

    /**
     * Decodes a JPEG byte array back into a Bitmap.
     */
    fun decodeBytes(bytes: ByteArray): Bitmap =
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
}
