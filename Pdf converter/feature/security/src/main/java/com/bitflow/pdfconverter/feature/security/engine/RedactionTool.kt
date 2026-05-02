package com.bitflow.pdfconverter.feature.security.engine

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RedactionTool @Inject constructor(
    private val fileManager: FileManager
) {
    /**
     * Blacks out entire pages specified in [pageIndices] (0-based).
     * For region-based redaction, expand the [Rect] parameter list.
     */
    fun redactPages(inputFile: File, pageIndices: List<Int>): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_redacted.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val doc = PdfDocument()

        val blackPaint = Paint().apply { color = Color.BLACK }

        for (i in 0 until renderer.pageCount) {
            val page = renderer.openPage(i)
            val bmp = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()

            if (i in pageIndices) {
                // Redact entire page with black rectangle
                val canvas = Canvas(bmp)
                canvas.drawRect(Rect(0, 0, bmp.width, bmp.height), blackPaint)
            }

            val pageInfo = PdfDocument.PageInfo.Builder(bmp.width, bmp.height, i + 1).create()
            val pdfPage = doc.startPage(pageInfo)
            pdfPage.canvas.drawBitmap(bmp, 0f, 0f, null)
            bmp.recycle()
            doc.finishPage(pdfPage)
        }

        renderer.close()
        parcelFd.close()
        FileOutputStream(outputFile).use { doc.writeTo(it) }
        doc.close()
        return outputFile
    }
}
