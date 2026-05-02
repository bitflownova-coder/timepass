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
 * Splits a PDF into a new PDF containing only the pages in [pageRange] (0-based, inclusive).
 */
class PdfSplitter @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    fun split(uri: Uri, pageRange: IntRange, outputName: String, dpi: Int = 150): File {
        val tmpFile = fileManager.newTempFile("pdf")
        context.contentResolver.openInputStream(uri)?.use { it.copyTo(tmpFile.outputStream()) }

        val pdfDoc = android.graphics.pdf.PdfDocument()
        PdfRenderer(
            android.os.ParcelFileDescriptor.open(tmpFile, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
        ).use { renderer ->
            val validRange = pageRange.coerceIn(0, renderer.pageCount - 1)
            validRange.forEachIndexed { outIndex, pageNum ->
                renderer.openPage(pageNum).use { srcPage ->
                    val scale  = dpi / 72f
                    val width  = (srcPage.width  * scale).toInt()
                    val height = (srcPage.height * scale).toInt()
                    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                    bitmap.eraseColor(android.graphics.Color.WHITE)
                    srcPage.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_PRINT)

                    val pageInfo = android.graphics.pdf.PdfDocument.PageInfo.Builder(
                        srcPage.width, srcPage.height, outIndex + 1
                    ).create()
                    val outPage = pdfDoc.startPage(pageInfo)
                    val matrix = android.graphics.Matrix().apply { setScale(1f / scale, 1f / scale) }
                    outPage.canvas.drawBitmap(bitmap, matrix, null)
                    pdfDoc.finishPage(outPage)
                    bitmap.recycle()
                }
            }
        }

        val outFile = fileManager.newOutputFile("$outputName.pdf")
        outFile.outputStream().use { pdfDoc.writeTo(it) }
        pdfDoc.close()
        tmpFile.delete()
        return outFile
    }

    private fun IntRange.coerceIn(min: Int, max: Int) = (first.coerceAtLeast(min))..(last.coerceAtMost(max))
}
