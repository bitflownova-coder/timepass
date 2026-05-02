package com.bitflow.pdfconverter.feature.utility.contract

import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

data class PdfDownloaderState(
    val url: String = "",
    val fileName: String = "downloaded",
    val isDownloading: Boolean = false,
    val progress: Int = 0,          // 0–100, or -1 for indeterminate
    val errorMessage: String? = null
) : MviState

sealed interface PdfDownloaderIntent : MviIntent {
    data class UrlChanged(val url: String) : PdfDownloaderIntent
    data class FileNameChanged(val name: String) : PdfDownloaderIntent
    data object Download : PdfDownloaderIntent
    data object DismissError : PdfDownloaderIntent
}

sealed interface PdfDownloaderSideEffect : MviSideEffect {
    data class DownloadComplete(val filePath: String) : PdfDownloaderSideEffect
    data class ShowError(val message: String) : PdfDownloaderSideEffect
}
