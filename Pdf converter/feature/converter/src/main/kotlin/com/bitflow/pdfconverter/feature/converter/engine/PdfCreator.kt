package com.bitflow.pdfconverter.feature.converter.engine

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfDocument
import android.net.Uri
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.converter.contract.PageSize
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import javax.inject.Inject

/**
 * Creates a PDF from one or more image [Uri]s using the Android [PdfDocument] API.
 *
 * Page dimensions:
 *  - [PageSize.A4]           → 595 × 842 pt (72 DPI)
 *  - [PageSize.LETTER]       → 612 × 792 pt (72 DPI)
 *  - [PageSize.FIT_TO_IMAGE] → bitmap's natural dimensions in points
 */
class PdfCreator @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    fun createFromImages(
        uris: List<Uri>,
        outputName: String,
        pageSize: PageSize,
        onProgress: (current: Int, total: Int) -> Unit = { _, _ -> }
    ): File {
        require(uris.isNotEmpty()) { "No images supplied" }

        val pdfDoc = PdfDocument()

        uris.forEachIndexed { index, uri ->
            onProgress(index + 1, uris.size)

            val bitmap = loadBitmap(uri) ?: return@forEachIndexed
            val (pageW, pageH) = pageDimensions(pageSize, bitmap)

            val pageInfo = PdfDocument.PageInfo.Builder(pageW, pageH, index + 1).create()
            val page     = pdfDoc.startPage(pageInfo)

            // Scale bitmap to fill page maintaining aspect ratio
            val scaleX  = pageW.toFloat() / bitmap.width
            val scaleY  = pageH.toFloat() / bitmap.height
            val scale   = minOf(scaleX, scaleY)
            val scaledW = (bitmap.width  * scale).toInt()
            val scaledH = (bitmap.height * scale).toInt()
            val left    = ((pageW - scaledW) / 2).toFloat()
            val top     = ((pageH - scaledH) / 2).toFloat()

            val matrix = android.graphics.Matrix().apply { setScale(scale, scale) }
            page.canvas.translate(left, top)
            page.canvas.drawBitmap(bitmap, matrix, null)
            bitmap.recycle()

            pdfDoc.finishPage(page)
        }

        val outFile = fileManager.newOutputFile("$outputName.pdf")
        outFile.outputStream().use { pdfDoc.writeTo(it) }
        pdfDoc.close()
        return outFile
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private fun loadBitmap(uri: Uri): Bitmap? = runCatching {
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
    }.getOrNull()

    private fun pageDimensions(size: PageSize, bitmap: Bitmap): Pair<Int, Int> = when (size) {
        PageSize.A4           -> 595 to 842
        PageSize.LETTER       -> 612 to 792
        PageSize.FIT_TO_IMAGE -> bitmap.width to bitmap.height
    }
}
