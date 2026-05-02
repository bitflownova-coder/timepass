package com.bitflow.pdfconverter.feature.smarttools.viewmodel

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.net.Uri
import androidx.lifecycle.viewModelScope
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.*
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import com.bitflow.pdfconverter.feature.smarttools.contract.SearchMatch
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartToolsIntent
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartToolsSideEffect
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartToolsState
import com.bitflow.pdfconverter.feature.smarttools.engine.OcrProcessor
import com.bitflow.pdfconverter.feature.smarttools.engine.QrEngine
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class SmartToolsViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val ocrProcessor: OcrProcessor,
    private val qrEngine: QrEngine,
    private val fileManager: FileManager,
    private val safHelper: SafHelper
) : MviViewModel<SmartToolsState, SmartToolsIntent, SmartToolsSideEffect>(SmartToolsState()) {

    override suspend fun handleIntent(intent: SmartToolsIntent) {
        when (intent) {
            is SmartToolsIntent.SectionSelected -> updateState { copy(activeSection = intent.section) }
            // OCR
            is SmartToolsIntent.OcrLoadFile -> updateState { copy(ocrSourceUri = intent.uri) }
            is SmartToolsIntent.OcrPageChanged -> updateState { copy(ocrPageIndex = intent.pageIndex) }
            SmartToolsIntent.RunOcr -> runOcr()
            SmartToolsIntent.CopyOcrText -> copyOcrText()
            SmartToolsIntent.SaveOcrAsTxt -> saveOcrAsTxt()
            // QR scanner results are handled by the screen composable and forwarded
            SmartToolsIntent.StartQrScan -> updateState { copy(qrScanActive = true) }
            is SmartToolsIntent.QrScanned -> {
                updateState { copy(qrResult = intent.rawValue, qrScanActive = false) }
                sendEffect(SmartToolsSideEffect.QrDetected(intent.rawValue))
            }
            // QR Generator
            is SmartToolsIntent.QrTextChanged -> updateState { copy(qrInputText = intent.text) }
            SmartToolsIntent.GenerateQr -> generateQr()
            SmartToolsIntent.SaveQrImage -> saveQrImage()
            // PDF Search
            is SmartToolsIntent.SearchLoadFile -> updateState { copy(searchPdfUri = intent.uri) }
            is SmartToolsIntent.SearchQueryChanged -> updateState { copy(searchQuery = intent.query) }
            SmartToolsIntent.RunSearch -> runSearch()
            SmartToolsIntent.DismissError -> updateState { copy(errorMessage = null) }
        }
    }

    private fun runOcr() {
        val uri = state.value.ocrSourceUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isOcrProcessing = true, ocrResult = "", errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "ocr_input.pdf", null)!!
                ocrProcessor.extractText(tempFile, state.value.ocrPageIndex)
            }
            updateState { copy(isOcrProcessing = false) }
            result.fold(
                onSuccess = { text ->
                    updateState { copy(ocrResult = text) }
                    sendEffect(SmartToolsSideEffect.OcrComplete(text))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SmartToolsSideEffect.ShowError(e.message ?: "OCR failed"))
                }
            )
        }
    }

    private fun copyOcrText() {
        val text = state.value.ocrResult
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("OCR Result", text))
        sendEffect(SmartToolsSideEffect.CopyToClipboard)
    }

    private fun saveOcrAsTxt() {
        viewModelScope.launch(Dispatchers.IO) {
            val result = runCatchingPdf {
                val file = fileManager.newOutputFile("ocr_result.txt")
                file.writeText(state.value.ocrResult)
                file.absolutePath
            }
            result.fold(
                onSuccess = { path -> sendEffect(SmartToolsSideEffect.TxtFileSaved(path)) },
                onFailure = { e -> sendEffect(SmartToolsSideEffect.ShowError(e.message ?: "Save failed")) }
            )
        }
    }

    private fun generateQr() {
        val text = state.value.qrInputText
        if (text.isBlank()) return
        viewModelScope.launch(Dispatchers.IO) {
            val result = runCatchingPdf { qrEngine.generateQr(text) }
            result.fold(
                onSuccess = { bitmap ->
                    val file = fileManager.newOutputFile("qr_${System.currentTimeMillis()}.png")
                    qrEngine.saveBitmap(bitmap, file)
                    bitmap.recycle()
                    updateState { copy(qrBitmapPath = file.absolutePath) }
                },
                onFailure = { e -> sendEffect(SmartToolsSideEffect.ShowError(e.message ?: "QR generation failed")) }
            )
        }
    }

    private fun saveQrImage() {
        val path = state.value.qrBitmapPath ?: return
        sendEffect(SmartToolsSideEffect.QrImageSaved(path))
    }

    private fun runSearch() {
        val uri = state.value.searchPdfUri ?: return
        val query = state.value.searchQuery
        if (query.isBlank()) return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isSearching = true, searchResults = emptyList(), errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "search_input.pdf", null)!!
                val fullText = ocrProcessor.extractAllText(tempFile)
                findMatches(fullText, query)
            }
            updateState { copy(isSearching = false) }
            result.fold(
                onSuccess = { matches -> updateState { copy(searchResults = matches) } },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SmartToolsSideEffect.ShowError(e.message ?: "Search failed"))
                }
            )
        }
    }

    private fun findMatches(fullText: String, query: String): List<SearchMatch> {
        val results = mutableListOf<SearchMatch>()
        val lines = fullText.lines()
        var pageIndex = -1
        lines.forEach { line ->
            if (line.startsWith("--- Page ")) {
                pageIndex++
                return@forEach
            }
            var start = line.indexOf(query, ignoreCase = true)
            while (start >= 0) {
                val end = start + query.length
                val snippetStart = (start - 30).coerceAtLeast(0)
                val snippetEnd = (end + 30).coerceAtMost(line.length)
                results += SearchMatch(
                    pageIndex = pageIndex,
                    snippet = line.substring(snippetStart, snippetEnd),
                    matchStart = start - snippetStart,
                    matchEnd = end - snippetStart
                )
                start = line.indexOf(query, end, ignoreCase = true)
            }
        }
        return results
    }
}
