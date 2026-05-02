package com.bitflow.pdfconverter.feature.security.engine

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.security.contract.WatermarkPosition
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.sqrt

@Singleton
class WatermarkApplier @Inject constructor(
    private val fileManager: FileManager
) {
    fun apply(
        inputFile: File,
        text: String,
        opacity: Float,
        position: WatermarkPosition
    ): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_watermarked.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val doc = PdfDocument()

        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.argb((opacity * 255).toInt(), 128, 128, 128)
            textSize = 48f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            xfermode = PorterDuffXfermode(PorterDuff.Mode.MULTIPLY)
        }

        for (i in 0 until renderer.pageCount) {
            val page = renderer.openPage(i)
            val bmp = Bitmap.createBitmap(page.width, page.height, Bitmap.Config.ARGB_8888)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()

            val canvas = Canvas(bmp)
            drawWatermark(canvas, text, paint, position, bmp.width, bmp.height)

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

    private fun drawWatermark(
        canvas: Canvas,
        text: String,
        paint: Paint,
        position: WatermarkPosition,
        width: Int,
        height: Int
    ) {
        val textWidth = paint.measureText(text)
        val textHeight = paint.textSize

        when (position) {
            WatermarkPosition.CENTER -> {
                canvas.drawText(text, (width - textWidth) / 2f, (height + textHeight) / 2f, paint)
            }
            WatermarkPosition.DIAGONAL -> {
                canvas.save()
                val angle = -Math.toDegrees(
                    Math.atan2(height.toDouble(), width.toDouble())
                ).toFloat()
                canvas.rotate(angle, width / 2f, height / 2f)
                canvas.drawText(text, (width - textWidth) / 2f, (height + textHeight) / 2f, paint)
                canvas.restore()
            }
            WatermarkPosition.TOP_LEFT ->
                canvas.drawText(text, 16f, textHeight + 16f, paint)
            WatermarkPosition.TOP_RIGHT ->
                canvas.drawText(text, width - textWidth - 16f, textHeight + 16f, paint)
            WatermarkPosition.BOTTOM_LEFT ->
                canvas.drawText(text, 16f, height - 16f, paint)
            WatermarkPosition.BOTTOM_RIGHT ->
                canvas.drawText(text, width - textWidth - 16f, height - 16f, paint)
        }
    }
}
