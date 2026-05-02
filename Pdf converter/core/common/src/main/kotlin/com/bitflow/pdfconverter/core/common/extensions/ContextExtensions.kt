package com.bitflow.pdfconverter.core.common.extensions

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import android.widget.Toast
import java.io.File

fun Context.showToast(message: String, duration: Int = Toast.LENGTH_SHORT) {
    Toast.makeText(this, message, duration).show()
}

/** Returns the display name of a content URI (e.g. "document.pdf"). */
fun Context.getFileNameFromUri(uri: Uri): String? {
    return contentResolver.query(uri, null, null, null, null)?.use { cursor ->
        val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        cursor.moveToFirst()
        if (nameIndex >= 0) cursor.getString(nameIndex) else null
    }
}

/** Returns the size in bytes of a content URI resource. */
fun Context.getFileSizeFromUri(uri: Uri): Long {
    return contentResolver.query(uri, null, null, null, null)?.use { cursor ->
        val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
        cursor.moveToFirst()
        if (sizeIndex >= 0 && !cursor.isNull(sizeIndex)) cursor.getLong(sizeIndex) else 0L
    } ?: 0L
}

/** Copies a content URI to a temp [File] and returns the file. */
fun Context.copyUriToTempFile(uri: Uri, fileName: String): File {
    val tmpDir = cacheDir.resolve("tmp").also { it.mkdirs() }
    val dest = File(tmpDir, fileName)
    contentResolver.openInputStream(uri)?.use { input ->
        dest.outputStream().use { output -> input.copyTo(output) }
    }
    return dest
}
