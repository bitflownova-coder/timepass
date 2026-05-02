package com.bitflow.pdfconverter.feature.converter.viewmodel

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.runCatchingPdf
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.converter.contract.*
import com.bitflow.pdfconverter.feature.converter.engine.PdfCreator
import com.bitflow.pdfconverter.feature.converter.engine.PdfMerger
import com.bitflow.pdfconverter.feature.converter.engine.PdfSplitter
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import javax.inject.Inject

@HiltViewModel
class ConverterViewModel @Inject constructor(
    private val pdfCreator: PdfCreator,
    private val pdfMerger: PdfMerger,
    private val pdfSplitter: PdfSplitter,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<ConverterState, ConverterIntent, ConverterSideEffect>(ConverterState()) {

    override suspend fun handleIntent(intent: ConverterIntent) {
        when (intent) {
            is ConverterIntent.ImagesSelected   -> updateState { copy(selectedUris = intent.uris) }
            is ConverterIntent.FilesSelected    -> updateState { copy(selectedUris = intent.uris) }
            is ConverterIntent.PageSizeChanged  -> updateState { copy(pageSize = intent.size) }
            is ConverterIntent.RemoveFile       -> updateState {
                copy(selectedUris = selectedUris.toMutableList().also { it.removeAt(intent.index) })
            }
            is ConverterIntent.ReorderFiles     -> reorder(intent.from, intent.to)
            is ConverterIntent.ConvertImagesToPdf -> convertImages(intent.outputName)
            is ConverterIntent.MergePdfs        -> mergePdfs(intent.uris, intent.outputName)
            is ConverterIntent.SplitPdf         -> splitPdf(intent.uri, intent.pageRange, intent.outputName)
            is ConverterIntent.ConvertOfficeToPdf -> sendEffect(ConverterSideEffect.ShowError("Office conversion requires Apache POI integration"))
            ConverterIntent.DismissError        -> updateState { copy(errorMessage = null) }
        }
    }

    private fun reorder(from: Int, to: Int) {
        val list = currentState.selectedUris.toMutableList()
        if (from !in list.indices || to !in list.indices) return
        val item = list.removeAt(from)
        list.add(to, item)
        updateState { copy(selectedUris = list) }
    }

    private suspend fun convertImages(name: String) {
        if (currentState.selectedUris.isEmpty()) {
            sendEffect(ConverterSideEffect.ShowError("No images selected"))
            return
        }
        updateState { copy(isConverting = true) }
        val result = withContext(Dispatchers.IO) {
            runCatchingPdf {
                pdfCreator.createFromImages(
                    uris       = currentState.selectedUris,
                    outputName = name,
                    pageSize   = currentState.pageSize
                ) { cur, total -> updateState { copy(progress = ConversionProgress(cur, total)) } }
            }
        }
        result
            .onSuccess { file ->
                registerDocument(file, currentState.selectedUris.size, "Convert")
                updateState { copy(isConverting = false, progress = null) }
                sendEffect(ConverterSideEffect.ConversionComplete(file.absolutePath))
            }
            .onError { msg, _ ->
                updateState { copy(isConverting = false, progress = null, errorMessage = msg) }
                sendEffect(ConverterSideEffect.ShowError(msg))
            }
    }

    private suspend fun mergePdfs(uris: List<Uri>, name: String) {
        updateState { copy(isConverting = true) }
        val result = withContext(Dispatchers.IO) {
            runCatchingPdf {
                pdfMerger.merge(uris, name) { cur, total ->
                    updateState { copy(progress = ConversionProgress(cur, total)) }
                }
            }
        }
        result
            .onSuccess { file ->
                registerDocument(file, countPages(file), "Merge")
                updateState { copy(isConverting = false, progress = null) }
                sendEffect(ConverterSideEffect.ConversionComplete(file.absolutePath))
            }
            .onError { msg, _ ->
                updateState { copy(isConverting = false, progress = null, errorMessage = msg) }
                sendEffect(ConverterSideEffect.ShowError(msg))
            }
    }

    private suspend fun splitPdf(uri: Uri, range: IntRange, name: String) {
        updateState { copy(isConverting = true) }
        val result = withContext(Dispatchers.IO) {
            runCatchingPdf { pdfSplitter.split(uri, range, name) }
        }
        result
            .onSuccess { file ->
                registerDocument(file, range.last - range.first + 1, "Split")
                updateState { copy(isConverting = false) }
                sendEffect(ConverterSideEffect.ConversionComplete(file.absolutePath))
            }
            .onError { msg, _ ->
                updateState { copy(isConverting = false, errorMessage = msg) }
                sendEffect(ConverterSideEffect.ShowError(msg))
            }
    }

    private suspend fun registerDocument(file: File, pageCount: Int, featureName: String) {
        fileManager.publishToDownloads(file, featureName)
        val now = System.currentTimeMillis()
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

    private fun countPages(file: File): Int = runCatching {
        android.graphics.pdf.PdfRenderer(
            android.os.ParcelFileDescriptor.open(file, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
        ).use { it.pageCount }
    }.getOrDefault(1)
}
