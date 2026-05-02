package com.bitflow.pdfconverter.core.filesystem

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Helpers for Storage Access Framework (SAF) and FileProvider sharing.
 */
@Singleton
class SafHelper @Inject constructor(
    @ApplicationContext private val context: Context,
    private val fileManager: FileManager
) {
    companion object {
        private const val FILE_PROVIDER_AUTHORITY = "com.bitflow.pdfconverter.fileprovider"
    }

    /** Returns a content URI for [file] via FileProvider (safe for sharing). */
    fun getShareUri(file: File): Uri =
        FileProvider.getUriForFile(context, FILE_PROVIDER_AUTHORITY, file)

    /** Builds a share [Intent] for a PDF file. */
    fun buildShareIntent(file: File): Intent {
        val uri = getShareUri(file)
        return Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    /** Opens an [InputStream] from a content or file [Uri]. Returns null on failure. */
    fun openInputStream(uri: Uri) = runCatching {
        context.contentResolver.openInputStream(uri)
    }.getOrNull()

    /** Opens an [OutputStream] to a content or file [Uri]. Returns null on failure. */
    fun openOutputStream(uri: Uri) = runCatching {
        context.contentResolver.openOutputStream(uri)
    }.getOrNull()

    /** Copies a content [Uri] to a local temp [File] and returns it.
     *  Uses [fileManager.tempDir] when [tempDir] is null.
     */
    fun copyToTemp(uri: Uri, fileName: String, tempDir: File? = null): File {
        val dir = tempDir ?: fileManager.tempDir
        val dest = File(dir, fileName)
        openInputStream(uri)?.use { input ->
            dest.outputStream().use { output -> input.copyTo(output) }
        }
        return dest
    }
}
