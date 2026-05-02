package com.bitflow.pdfconverter.feature.converter.engine

import android.content.Context
import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import com.bitflow.pdfconverter.core.filesystem.FileManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import javax.inject.Inject

/**
 * Merges multiple PDF files into one using [PdfDocument] page-copying via [PdfRenderer].
 *
 * NOTE: Android's [PdfRenderer] is read-only, so we render each page to a [Bitmap]
 * and then re-encode it into the merged PDF. For lossless merging in production,
 * consider PdfBox-Android's `PDFMergerUtility`.
 */
class PdfMerger @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    fun merge(
        uris: List<Uri>,
        outputName: String,
        dpi: Int = 150,
        onProgress: (Int, Int) -> Unit = { _, _ -> }
    ): File {
        require(uris.size >= 2) { "Need at least 2 PDFs to merge" }

        val pdfDoc = android.graphics.pdf.PdfDocument()
        var globalPageIndex = 0

        uris.forEachIndexed { fileIndex, uri ->
            onProgress(fileIndex + 1, uris.size)
            val tmpFile = fileManager.newTempFile("pdf")
            context.contentResolver.openInputStream(uri)?.use { it.copyTo(tmpFile.outputStream()) }

            PdfRenderer(android.os.ParcelFileDescriptor.open(tmpFile, android.os.ParcelFileDescriptor.MODE_READ_ONLY)).use { renderer ->
                for (pageNum in 0 until renderer.pageCount) {
                    renderer.openPage(pageNum).use { srcPage ->
                        val scale  = dpi / 72f
                        val width  = (srcPage.width  * scale).toInt()
                        val height = (srcPage.height * scale).toInt()

                        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(android.graphics.Color.WHITE)
                        srcPage.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_PRINT)

                        globalPageIndex++
                        val pageInfo = android.graphics.pdf.PdfDocument.PageInfo.Builder(
                            srcPage.width, srcPage.height, globalPageIndex
                        ).create()
                        val outPage = pdfDoc.startPage(pageInfo)
                        val matrix = android.graphics.Matrix().apply { setScale(1f / scale, 1f / scale) }
                        outPage.canvas.drawBitmap(bitmap, matrix, null)
                        pdfDoc.finishPage(outPage)
                        bitmap.recycle()
                    }
                }
            }
            tmpFile.delete()
        }

        val outFile = fileManager.newOutputFile("$outputName.pdf")
        outFile.outputStream().use { pdfDoc.writeTo(it) }
        pdfDoc.close()
        return outFile
    }
}
