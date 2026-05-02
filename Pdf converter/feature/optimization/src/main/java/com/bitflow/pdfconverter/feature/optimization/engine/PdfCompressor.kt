package com.bitflow.pdfconverter.feature.optimization.engine

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PdfCompressor @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    /**
     * Compresses a PDF by re-rendering each page as a JPEG at [qualityPercent]
     * and re-encoding into a new PDF document at [dpi].
     */
    suspend fun compress(
        inputFile: File,
        dpi: Int,
        qualityPercent: Int,
        onProgressPage: (current: Int, total: Int) -> Unit = { _, _ -> }
    ): File {
        val outputFile = fileManager.newOutputFile("compressed_${inputFile.nameWithoutExtension}.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val pageCount = renderer.pageCount

        val pdfDocument = android.graphics.pdf.PdfDocument()
        val scale = dpi / 72f

        for (i in 0 until pageCount) {
            onProgressPage(i + 1, pageCount)
            val page = renderer.openPage(i)
            val width = (page.width * scale).toInt().coerceAtLeast(1)
            val height = (page.height * scale).toInt().coerceAtLeast(1)

            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()

            // Re-compress via JPEG to reduce size
            val compressedBitmap = recompressViaJpeg(bitmap, qualityPercent)
            bitmap.recycle()

            val pageInfo = android.graphics.pdf.PdfDocument.PageInfo.Builder(width, height, i + 1).create()
            val pdfPage = pdfDocument.startPage(pageInfo)
            pdfPage.canvas.drawBitmap(compressedBitmap, 0f, 0f, null)
            compressedBitmap.recycle()
            pdfDocument.finishPage(pdfPage)
        }

        renderer.close()
        parcelFd.close()

        FileOutputStream(outputFile).use { pdfDocument.writeTo(it) }
        pdfDocument.close()
        return outputFile
    }

    private fun recompressViaJpeg(source: Bitmap, quality: Int): Bitmap {
        val baos = ByteArrayOutputStream()
        source.compress(Bitmap.CompressFormat.JPEG, quality, baos)
        val bytes = baos.toByteArray()
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    }
}
