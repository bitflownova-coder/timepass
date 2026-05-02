package com.bitflow.pdfconverter.feature.optimization.viewmodel

import android.net.Uri
import androidx.lifecycle.viewModelScope
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.*
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import com.bitflow.pdfconverter.feature.optimization.contract.BatchFile
import com.bitflow.pdfconverter.feature.optimization.contract.BatchStatus
import com.bitflow.pdfconverter.feature.optimization.contract.OptimizationIntent
import com.bitflow.pdfconverter.feature.optimization.contract.OptimizationSideEffect
import com.bitflow.pdfconverter.feature.optimization.contract.OptimizationState
import com.bitflow.pdfconverter.feature.optimization.engine.FileSizeOptimizer
import com.bitflow.pdfconverter.feature.optimization.engine.PdfCompressor
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class OptimizationViewModel @Inject constructor(
    private val compressor: PdfCompressor,
    private val fileSizeOptimizer: FileSizeOptimizer,
    private val safHelper: SafHelper,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<OptimizationState, OptimizationIntent, OptimizationSideEffect>(OptimizationState()) {

    override suspend fun handleIntent(intent: OptimizationIntent) {
        when (intent) {
            is OptimizationIntent.LoadFile -> loadFile(intent.uri)
            is OptimizationIntent.DpiSelected -> updateState { copy(selectedDpi = intent.dpi) }
            is OptimizationIntent.QualityChanged -> updateState { copy(qualityPercent = intent.quality) }
            is OptimizationIntent.MaxSizeSet -> updateState { copy(maxTargetSizeKb = intent.sizeKb) }
            OptimizationIntent.Compress -> compress()
            is OptimizationIntent.LoadBatch -> loadBatch(intent.uris)
            OptimizationIntent.CompressBatch -> compressBatch()
            OptimizationIntent.DismissError -> updateState { copy(errorMessage = null) }
            OptimizationIntent.ClearFile -> updateState { OptimizationState() }
        }
    }

    private fun loadFile(uri: Uri) {
        viewModelScope.launch(Dispatchers.IO) {
            val tempFile = runCatchingPdf { safHelper.copyToTemp(uri, "opt_input.pdf", null) }
                .getOrElse {
                    updateState { copy(errorMessage = it.message) }
                    return@launch
                }
            updateState {
                copy(
                    fileUri = uri,
                    fileName = tempFile?.name ?: "file.pdf",
                    originalSizeBytes = tempFile?.length() ?: 0L,
                    compressedSizeBytes = 0L
                )
            }
        }
    }

    private fun compress() {
        val uri = state.value.fileUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, progress = 0f, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "opt_input.pdf", null)!!
                val dpi = state.value.selectedDpi
                val quality = state.value.qualityPercent
                val maxKb = state.value.maxTargetSizeKb

                val outputFile = if (maxKb > 0) {
                    fileSizeOptimizer.optimizeToSize(
                        inputFile = tempFile,
                        dpi = dpi,
                        maxSizeBytes = maxKb * 1024L,
                        onProgress = { label -> updateState { copy(progressLabel = label) } }
                    )
                } else {
                    compressor.compress(
                        inputFile = tempFile,
                        dpi = dpi,
                        qualityPercent = quality,
                        onProgressPage = { cur, total ->
                            updateState { copy(progress = cur.toFloat() / total, progressLabel = "Page $cur / $total") }
                        }
                    )
                }
                val saved = tempFile.length() - outputFile.length()
                updateState { copy(compressedSizeBytes = outputFile.length()) }
                outputFile to saved
            }

            updateState { copy(isProcessing = false, progress = 1f) }
            result.fold(
                onSuccess = { (file, saved) ->
                    fileManager.publishToDownloads(file, "Compress")
                    registerInMyPdfs(file)
                    sendEffect(OptimizationSideEffect.CompressionComplete(file.absolutePath, saved))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message ?: "Compression failed") }
                    sendEffect(OptimizationSideEffect.ShowError(e.message ?: "Compression failed"))
                }
            )
        }
    }

    private fun loadBatch(uris: List<Uri>) {
        viewModelScope.launch(Dispatchers.IO) {
            val files = uris.map { uri ->
                val name = uri.lastPathSegment ?: "file.pdf"
                val tempFile = runCatching { safHelper.copyToTemp(uri, name, null) }.getOrNull()
                BatchFile(uri = uri, name = name, originalSizeBytes = tempFile?.length() ?: 0L)
            }
            updateState { copy(batchFiles = files) }
        }
    }

    private fun compressBatch() {
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true) }
            val results = mutableListOf<String>()
            val files = state.value.batchFiles.toMutableList()

            files.forEachIndexed { idx, batchFile ->
                updateState {
                    val updated = batchFiles.toMutableList()
                    updated[idx] = batchFile.copy(status = BatchStatus.PROCESSING)
                    copy(
                        batchFiles = updated,
                        progress = idx.toFloat() / files.size,
                        progressLabel = "Compressing ${batchFile.name}…"
                    )
                }
                val result = runCatching {
                    val tempFile = safHelper.copyToTemp(batchFile.uri, batchFile.name, null)!!
                    compressor.compress(tempFile, state.value.selectedDpi, state.value.qualityPercent)
                }
                val updatedBatch = state.value.batchFiles.toMutableList()
                if (result.isSuccess) {
                    val outFile = result.getOrThrow()
                    fileManager.publishToDownloads(outFile, "Compress")
                    registerInMyPdfs(outFile)
                    results += outFile.absolutePath
                    updatedBatch[idx] = batchFile.copy(status = BatchStatus.DONE, compressedPath = outFile.absolutePath)
                } else {
                    updatedBatch[idx] = batchFile.copy(status = BatchStatus.FAILED)
                }
                updateState { copy(batchFiles = updatedBatch) }
            }

            updateState { copy(isProcessing = false, progress = 1f, progressLabel = "") }
            sendEffect(OptimizationSideEffect.BatchComplete(results))
        }
    }

    private suspend fun registerInMyPdfs(file: java.io.File) {
        val now = System.currentTimeMillis()
        val pageCount = runCatching {
            android.graphics.pdf.PdfRenderer(
                android.os.ParcelFileDescriptor.open(file, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
            ).use { it.pageCount }
        }.getOrDefault(1)
        repository.saveDocument(
            PdfDocument(
                name       = file.nameWithoutExtension,
                filePath   = file.absolutePath,
                sizeBytes  = file.length(),
                pageCount  = pageCount,
                createdAt  = now,
                modifiedAt = now
            )
        )
    }
}
