package com.bitflow.pdfconverter.core.filesystem

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Manages all storage paths for the app.
 * PDFs go to external app storage (Android/data/<pkg>/files/PDFs) so they are
 * visible in the device Files app. Falls back to internal storage on devices
 * without an SD card or when external storage is unavailable.
 */
@Singleton
class FileManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    /**
     * Permanent storage for user-created PDFs.
     * Prefers external app-specific storage (no permission required on API 28+)
     * so the user can browse files in the Android Files app.
     */
    val outputDir: File
        get() {
            val ext = context.getExternalFilesDir("PDFs")
            return if (ext != null && (ext.exists() || ext.mkdirs())) ext
            else context.filesDir.resolve("pdfs").also { it.mkdirs() }
        }

    /** Scratch space for in-progress operations; cleared on startup. */
    val tempDir: File get() = context.cacheDir.resolve("tmp").also { it.mkdirs() }

    /** Directory for page thumbnail bitmaps. */
    val thumbnailDir: File get() = context.cacheDir.resolve("thumbnails").also { it.mkdirs() }

    /** Returns a new unique file inside [outputDir] with the given name. */
    fun newOutputFile(name: String): File {
        val sanitized = name.replace(Regex("[^a-zA-Z0-9._\\- ]"), "_")
        var file = outputDir.resolve(sanitized)
        var counter = 1
        while (file.exists()) {
            val stem = sanitized.substringBeforeLast(".")
            val ext  = sanitized.substringAfterLast(".", "pdf")
            file = outputDir.resolve("${stem}_$counter.$ext")
            counter++
        }
        return file
    }

    /** Returns a new temp file with the given extension. */
    fun newTempFile(extension: String = "pdf"): File =
        File.createTempFile("pdf_tmp_", ".$extension", tempDir)

    /** Deletes all files in [tempDir]. Safe to call on app start. */
    fun clearTempDir() {
        tempDir.listFiles()?.forEach { it.deleteRecursively() }
    }

    /** Moves [file] into [outputDir] with the given name and returns the destination. */
    fun moveToOutput(file: File, name: String): File {
        val dest = newOutputFile(name)
        file.copyTo(dest, overwrite = true)
        file.delete()
        return dest
    }

    /** Formats bytes into a human-readable string (e.g. "1.4 MB"). */
    fun formatFileSize(bytes: Long): String = when {
        bytes < 1_024           -> "$bytes B"
        bytes < 1_048_576       -> "%.1f KB".format(bytes / 1_024f)
        bytes < 1_073_741_824   -> "%.1f MB".format(bytes / 1_048_576f)
        else                    -> "%.2f GB".format(bytes / 1_073_741_824f)
    }

    /**
     * Copies [sourceFile] into the public `Download/PDF Converter/` folder, naming it
     * "[featureName] 01.pdf", "[featureName] 02.pdf", etc.
     * The source file is kept in the app folder so "My PDFs" can still access it.
     */
    fun publishToDownloads(sourceFile: File, featureName: String) {
        val base = featureName.trim()
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val nextNum = queryNextNumber(base)
                val name = "$base %02d.pdf".format(nextNum)
                val values = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, name)
                    put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf")
                    put(MediaStore.MediaColumns.RELATIVE_PATH, "Download/PDF Converter/")
                }
                val uri = context.contentResolver.insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI, values
                ) ?: return
                context.contentResolver.openOutputStream(uri)?.use { out ->
                    sourceFile.inputStream().use { it.copyTo(out) }
                }
            } else {
                val downloadsDir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS
                )
                val pdfDir = File(downloadsDir, "PDF Converter").also { it.mkdirs() }
                var counter = 1
                var dest: File
                do {
                    dest = File(pdfDir, "$base %02d.pdf".format(counter))
                    counter++
                } while (dest.exists())
                sourceFile.copyTo(dest)
            }
        } catch (_: Exception) {
            // Best-effort; the source file in the app folder is untouched
        }
    }

    /** Queries MediaStore Downloads to find the next available sequential number for [featureName]. */
    private fun queryNextNumber(featureName: String): Int {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return 1
        val projection = arrayOf(MediaStore.MediaColumns.DISPLAY_NAME)
        val selection  = "${MediaStore.MediaColumns.RELATIVE_PATH} LIKE ? AND " +
                         "${MediaStore.MediaColumns.DISPLAY_NAME} LIKE ?"
        val args = arrayOf("%PDF Converter%", "$featureName %.pdf")
        val regex = Regex("""^${Regex.escape(featureName)} (\d+)\.pdf$""", RegexOption.IGNORE_CASE)
        var max = 0
        context.contentResolver.query(
            MediaStore.Downloads.EXTERNAL_CONTENT_URI, projection, selection, args, null
        )?.use { cursor ->
            val col = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DISPLAY_NAME)
            while (cursor.moveToNext()) {
                val num = regex.find(cursor.getString(col) ?: continue)
                    ?.groupValues?.get(1)?.toIntOrNull() ?: continue
                if (num > max) max = num
            }
        }
        return max + 1
    }
}
