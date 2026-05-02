package com.bitflow.pdfconverter.feature.utility.engine

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.utility.contract.FormField
import com.bitflow.pdfconverter.feature.utility.contract.FormFieldType
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FormBuilder @Inject constructor(
    private val fileManager: FileManager
) {
    /**
     * Overlays form field values on top of the rendered PDF pages.
     * For proper interactive form fields (AcroForms), PdfBox's PDTextField/PDCheckBox APIs
     * would be used instead of bitmap rendering.
     */
    fun applyFormFields(inputFile: File, fields: List<FormField>): File {
        val outputFile = fileManager.newOutputFile("${inputFile.nameWithoutExtension}_form.pdf")
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val pageCount = renderer.pageCount
        val doc = PdfDocument()

        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.BLACK
            textSize = 14f
            typeface = Typeface.MONOSPACE
        }
        val boxPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.BLACK
            style = Paint.Style.STROKE
            strokeWidth = 1.5f
        }
        val checkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.BLACK
            strokeWidth = 2f
            style = Paint.Style.STROKE
        }

        for (pageIdx in 0 until pageCount) {
            val page = renderer.openPage(pageIdx)
            val bmp = android.graphics.Bitmap.createBitmap(page.width, page.height, android.graphics.Bitmap.Config.ARGB_8888)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            page.close()

            val canvas = Canvas(bmp)
            val pageFields = fields.filter { it.pageIndex == pageIdx }
            pageFields.forEach { field ->
                when (field.type) {
                    FormFieldType.TEXT -> {
                        // Draw label
                        canvas.drawText(field.label, field.x, field.y - 4f, textPaint)
                        // Draw text box
                        canvas.drawRect(field.x, field.y, field.x + 160f, field.y + 20f, boxPaint)
                        // Draw value
                        canvas.drawText(field.value, field.x + 4f, field.y + 14f, textPaint)
                    }
                    FormFieldType.CHECKBOX -> {
                        canvas.drawRect(field.x, field.y, field.x + 16f, field.y + 16f, boxPaint)
                        if (field.value == "true") {
                            canvas.drawLine(field.x + 2f, field.y + 8f, field.x + 6f, field.y + 13f, checkPaint)
                            canvas.drawLine(field.x + 6f, field.y + 13f, field.x + 14f, field.y + 3f, checkPaint)
                        }
                        canvas.drawText(field.label, field.x + 20f, field.y + 12f, textPaint)
                    }
                    FormFieldType.SIGNATURE -> {
                        canvas.drawText("Signature:", field.x, field.y - 4f, textPaint)
                        canvas.drawRect(field.x, field.y, field.x + 200f, field.y + 40f, boxPaint)
                        if (field.value.isNotBlank()) {
                            val sigPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                color = Color.BLUE
                                textSize = 18f
                                typeface = Typeface.create("cursive", Typeface.ITALIC)
                            }
                            canvas.drawText(field.value, field.x + 8f, field.y + 28f, sigPaint)
                        }
                    }
                }
            }

            val pageInfo = PdfDocument.PageInfo.Builder(bmp.width, bmp.height, pageIdx + 1).create()
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
