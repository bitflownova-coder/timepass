package com.bitflow.pdfconverter.feature.utility.viewmodel

import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.utility.contract.PdfDownloaderIntent
import com.bitflow.pdfconverter.feature.utility.contract.PdfDownloaderSideEffect
import com.bitflow.pdfconverter.feature.utility.contract.PdfDownloaderState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedInputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import javax.inject.Inject

@HiltViewModel
class PdfDownloaderViewModel @Inject constructor(
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<PdfDownloaderState, PdfDownloaderIntent, PdfDownloaderSideEffect>(
    PdfDownloaderState()
) {
    override suspend fun handleIntent(intent: PdfDownloaderIntent) {
        when (intent) {
            is PdfDownloaderIntent.UrlChanged ->
                updateState { copy(url = intent.url, errorMessage = null) }

            is PdfDownloaderIntent.FileNameChanged ->
                updateState { copy(fileName = intent.name) }

            PdfDownloaderIntent.DismissError ->
                updateState { copy(errorMessage = null) }

            PdfDownloaderIntent.Download -> downloadPdf()
        }
    }

    private suspend fun downloadPdf() {
        val rawUrl = currentState.url.trim()
        if (rawUrl.isBlank()) {
            updateState { copy(errorMessage = "Please enter a URL") }
            return
        }
        // Validate URL scheme — only allow https/http to prevent SSRF to internal hosts
        if (!rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
            updateState { copy(errorMessage = "URL must start with http:// or https://") }
            return
        }

        val name = currentState.fileName.trim().ifBlank { "downloaded" }
            .replace(Regex("[^a-zA-Z0-9._\\- ]"), "_")

        updateState { copy(isDownloading = true, progress = -1, errorMessage = null) }

        val result = withContext(Dispatchers.IO) {
            runCatching {
                val connection = URL(rawUrl).openConnection() as HttpURLConnection
                connection.connectTimeout = 15_000
                connection.readTimeout = 60_000
                connection.setRequestProperty("User-Agent", "PdfConverterApp/1.0")
                connection.connect()

                val responseCode = connection.responseCode
                if (responseCode != HttpURLConnection.HTTP_OK) {
                    error("Server returned HTTP $responseCode")
                }

                val contentType = connection.contentType?.lowercase() ?: ""
                val totalBytes = connection.contentLengthLong

                val outFile = fileManager.newOutputFile("$name.pdf")
                val buf = ByteArray(8192)
                var downloaded = 0L

                BufferedInputStream(connection.inputStream).use { input ->
                    outFile.outputStream().use { output ->
                        var bytes = input.read(buf)
                        while (bytes > 0) {
                            output.write(buf, 0, bytes)
                            downloaded += bytes
                            if (totalBytes > 0) {
                                val pct = (downloaded * 100 / totalBytes).toInt()
                                updateState { copy(progress = pct) }
                            }
                            bytes = input.read(buf)
                        }
                    }
                }
                connection.disconnect()

                // If the content-type isn't PDF, delete file and report error
                if (!contentType.contains("pdf") && !contentType.contains("octet-stream") && !contentType.contains("application")) {
                    outFile.delete()
                    error("URL did not return a PDF (content-type: $contentType)")
                }

                outFile.absolutePath
            }
        }

        result
            .onSuccess { path ->
                val srcFile = java.io.File(path)
                fileManager.publishToDownloads(srcFile, "Download")
                val now = System.currentTimeMillis()
                val pageCount = runCatching {
                    android.graphics.pdf.PdfRenderer(
                        android.os.ParcelFileDescriptor.open(srcFile, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
                    ).use { it.pageCount }
                }.getOrDefault(1)
                repository.saveDocument(
                    PdfDocument(
                        name       = srcFile.nameWithoutExtension,
                        filePath   = path,
                        sizeBytes  = srcFile.length(),
                        pageCount  = pageCount,
                        createdAt  = now,
                        modifiedAt = now
                    )
                )
                updateState { copy(isDownloading = false, progress = 100) }
                sendEffect(PdfDownloaderSideEffect.DownloadComplete(path))
            }
            .onFailure { e ->
                val msg = e.message ?: "Download failed"
                updateState { copy(isDownloading = false, progress = 0, errorMessage = msg) }
                sendEffect(PdfDownloaderSideEffect.ShowError(msg))
            }
    }
}
