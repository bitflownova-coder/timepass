package com.bitflow.pdfconverter.feature.utility.engine

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.utility.contract.StampColor
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class StampPlacer @Inject constructor(
    private val fileManager: FileManager
) {
    /**
     * Places a bordered text stamp on each page within [pageIndices] (0-based, empty = all pages).
     */
    fun applyStamp(
        inputFile: File,
        stampText: String,
        stampColor: StampColor,
        pageIndices: List<Int>
    ): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_stamped.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val pageCount = renderer.pageCount
        val doc = PdfDocument()

        val color = when (stampColor) {
            StampColor.RED -> Color.RED
            StampColor.GREEN -> Color.GREEN
            StampColor.BLUE -> Color.BLUE
            StampColor.BLACK -> Color.BLACK
        }

        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = color
            textSize = 48f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = color
            style = Paint.Style.STROKE
            strokeWidth = 4f
        }

        val targetPages = if (pageIndices.isEmpty()) (0 until pageCount).toList() else pageIndices

        for (i in 0 until pageCount) {
            val page = renderer.openPage(i)
            val bmp = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()

            if (i in targetPages) {
                val canvas = Canvas(bmp)
                val textWidth = textPaint.measureText(stampText)
                val padding = 12f
                val left = bmp.width - textWidth - padding * 3
                val top = bmp.height - textPaint.textSize - padding * 3
                val right = bmp.width - padding
                val bottom = bmp.height.toFloat() - padding

                // Draw rotated stamp
                canvas.save()
                canvas.rotate(-30f, (left + right) / 2f, (top + bottom) / 2f)
                canvas.drawRoundRect(RectF(left, top, right, bottom), 8f, 8f, borderPaint)
                canvas.drawText(stampText, left + padding, bottom - padding, textPaint)
                canvas.restore()
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
