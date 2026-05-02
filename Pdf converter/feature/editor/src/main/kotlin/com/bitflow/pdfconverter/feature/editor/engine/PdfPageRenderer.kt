package com.bitflow.pdfconverter.feature.editor.engine

import android.content.Context
import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import com.bitflow.pdfconverter.core.filesystem.FileManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import java.io.InputStream
import javax.inject.Inject

/**
 * Renders PDF pages to [Bitmap]s using Android's built-in [PdfRenderer].
 * Each page is rendered at [dpi] resolution.
 */
class PdfPageRenderer @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    /**
     * Opens an [InputStream] for a URI that may be a content://, file://, or raw file path.
     * Bypasses the ContentResolver for file-system paths so that internal app files work
     * without requiring a FileProvider.
     */
    private fun openInputStream(uri: Uri): InputStream? {
        return when (uri.scheme) {
            "content" -> context.contentResolver.openInputStream(uri)
            "file"    -> uri.path?.let { File(it).inputStream() }
            else      -> File(uri.toString()).takeIf { it.exists() }?.inputStream()
        }
    }

    /**
     * Renders all pages in the PDF at the given URI.
     * Returns a list of bitmaps (one per page) and the temp file path.
     */
    fun renderAllPages(uri: Uri, dpi: Int = 150): Pair<List<Bitmap>, String> {
        val tmpFile = fileManager.newTempFile("pdf")
        openInputStream(uri)?.use { it.copyTo(tmpFile.outputStream()) }

        val bitmaps = mutableListOf<Bitmap>()
        PdfRenderer(
            ParcelFileDescriptor.open(tmpFile, ParcelFileDescriptor.MODE_READ_ONLY)
        ).use { renderer ->
            for (i in 0 until renderer.pageCount) {
                renderer.openPage(i).use { page ->
                    val scale  = dpi / 72f
                    val w = (page.width  * scale).toInt()
                    val h = (page.height * scale).toInt()
                    val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
                    bmp.eraseColor(android.graphics.Color.WHITE)
                    page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    bitmaps.add(bmp)
                }
            }
        }
        return bitmaps to tmpFile.absolutePath
    }

    /** Renders a single page by [pageIndex] at the given URI. */
    fun renderPage(uri: Uri, pageIndex: Int, dpi: Int = 150): Bitmap? {
        val tmpFile = fileManager.newTempFile("pdf")
        openInputStream(uri)?.use { it.copyTo(tmpFile.outputStream()) }

        return PdfRenderer(
            ParcelFileDescriptor.open(tmpFile, ParcelFileDescriptor.MODE_READ_ONLY)
        ).use { renderer ->
            if (pageIndex !in 0 until renderer.pageCount) return null
            renderer.openPage(pageIndex).use { page ->
                val scale = dpi / 72f
                val bmp = Bitmap.createBitmap(
                    (page.width * scale).toInt(),
                    (page.height * scale).toInt(),
                    Bitmap.Config.ARGB_8888
                )
                bmp.eraseColor(android.graphics.Color.WHITE)
                page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                bmp
            }
        }
    }
}
