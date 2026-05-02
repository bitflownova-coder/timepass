package com.bitflow.pdfconverter.feature.scanner.processing

import android.graphics.Bitmap
import android.graphics.pdf.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import java.io.File
import javax.inject.Inject

/**
 * Combines a list of processed [Bitmap]s into a single PDF file using Android's
 * built-in [PdfDocument] API (no third-party library required for basic creation).
 *
 * Each bitmap is rendered at 72 DPI (screen resolution); increase [dpi] for print quality.
 */
class ScanToPdfExporter @Inject constructor(
    private val fileManager: FileManager
) {
    /**
     * Writes [pages] to a PDF and returns the output [File].
     *
     * @param pages         List of bitmaps (one per scanned page)
     * @param outputName    Desired file name (without extension — .pdf appended automatically)
     * @param dpi           Target DPI. Default 150 gives ~A4 at reasonable size.
     */
    fun export(pages: List<Bitmap>, outputName: String, dpi: Int = 150): File {
        require(pages.isNotEmpty()) { "Cannot export an empty page list" }

        val scale = dpi / 72f
        val pdfDoc = PdfDocument()

        pages.forEachIndexed { index, bitmap ->
            val pageWidth  = (bitmap.width  / scale).toInt()
            val pageHeight = (bitmap.height / scale).toInt()

            val pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, index + 1).create()
            val page     = pdfDoc.startPage(pageInfo)

            val canvas = page.canvas
            canvas.scale(1f / scale, 1f / scale)
            canvas.drawBitmap(bitmap, 0f, 0f, null)

            pdfDoc.finishPage(page)
        }

        val outputFile = fileManager.newOutputFile("$outputName.pdf")
        outputFile.outputStream().use { pdfDoc.writeTo(it) }
        pdfDoc.close()

        return outputFile
    }
}
