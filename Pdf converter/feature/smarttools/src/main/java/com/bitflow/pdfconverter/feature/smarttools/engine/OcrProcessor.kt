package com.bitflow.pdfconverter.feature.smarttools.engine

import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

@Singleton
class OcrProcessor @Inject constructor() {
    private val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    /**
     * Renders the given page of [inputFile] and extracts text using ML Kit.
     */
    suspend fun extractText(inputFile: File, pageIndex: Int): String {
        val bitmap = renderPage(inputFile, pageIndex)
        return recognizeText(bitmap).also { bitmap.recycle() }
    }

    /**
     * Runs OCR on all pages of [inputFile], concatenating results page by page.
     */
    suspend fun extractAllText(inputFile: File, onPageDone: (Int, Int) -> Unit = { _, _ -> }): String {
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val pageCount = renderer.pageCount
        renderer.close()
        parcelFd.close()

        val sb = StringBuilder()
        for (i in 0 until pageCount) {
            val text = extractText(inputFile, i)
            sb.appendLine("--- Page ${i + 1} ---")
            sb.appendLine(text)
            onPageDone(i + 1, pageCount)
        }
        return sb.toString()
    }

    private fun renderPage(inputFile: File, pageIndex: Int): Bitmap {
        val parcelFd = ParcelFileDescriptor.open(inputFile, ParcelFileDescriptor.MODE_READ_ONLY)
        val renderer = PdfRenderer(parcelFd)
        val page = renderer.openPage(pageIndex)
        val scale = 2f // 144 DPI for better OCR accuracy
        val bitmap = Bitmap.createBitmap(
            (page.width * scale).toInt(),
            (page.height * scale).toInt(),
            Bitmap.Config.ARGB_8888
        )
        page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
        page.close()
        renderer.close()
        parcelFd.close()
        return bitmap
    }

    private suspend fun recognizeText(bitmap: Bitmap): String =
        suspendCancellableCoroutine { cont ->
            val image = InputImage.fromBitmap(bitmap, 0)
            recognizer.process(image)
                .addOnSuccessListener { result -> cont.resume(result.text) }
                .addOnFailureListener { e -> cont.resumeWithException(e) }
        }
}
