package com.bitflow.pdfconverter.feature.smarttools.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

data class SmartToolsState(
    val activeSection: SmartSection = SmartSection.OCR,
    // OCR
    val ocrSourceUri: Uri? = null,
    val ocrPageIndex: Int = 0,
    val ocrResult: String = "",
    val isOcrProcessing: Boolean = false,
    // QR Scanner
    val qrResult: String = "",
    val qrScanActive: Boolean = false,
    // QR Generator
    val qrInputText: String = "",
    val qrBitmapPath: String? = null,
    // PDF Search
    val searchPdfUri: Uri? = null,
    val searchQuery: String = "",
    val searchResults: List<SearchMatch> = emptyList(),
    val isSearching: Boolean = false,
    val errorMessage: String? = null
) : MviState

enum class SmartSection { OCR, QR_SCAN, QR_GEN, PDF_SEARCH }

data class SearchMatch(
    val pageIndex: Int,
    val snippet: String,
    val matchStart: Int,
    val matchEnd: Int
)

sealed interface SmartToolsIntent : MviIntent {
    data class SectionSelected(val section: SmartSection) : SmartToolsIntent
    // OCR
    data class OcrLoadFile(val uri: Uri) : SmartToolsIntent
    data class OcrPageChanged(val pageIndex: Int) : SmartToolsIntent
    data object RunOcr : SmartToolsIntent
    data object CopyOcrText : SmartToolsIntent
    data object SaveOcrAsTxt : SmartToolsIntent
    // QR Scanner
    data object StartQrScan : SmartToolsIntent
    data class QrScanned(val rawValue: String) : SmartToolsIntent
    // QR Generator
    data class QrTextChanged(val text: String) : SmartToolsIntent
    data object GenerateQr : SmartToolsIntent
    data object SaveQrImage : SmartToolsIntent
    // PDF Search
    data class SearchLoadFile(val uri: Uri) : SmartToolsIntent
    data class SearchQueryChanged(val query: String) : SmartToolsIntent
    data object RunSearch : SmartToolsIntent
    data object DismissError : SmartToolsIntent
}

sealed interface SmartToolsSideEffect : MviSideEffect {
    data class OcrComplete(val text: String) : SmartToolsSideEffect
    data class QrDetected(val value: String) : SmartToolsSideEffect
    data class QrImageSaved(val path: String) : SmartToolsSideEffect
    data class TxtFileSaved(val path: String) : SmartToolsSideEffect
    data class ShowError(val message: String) : SmartToolsSideEffect
    data object CopyToClipboard : SmartToolsSideEffect
}
