package com.bitflow.pdfconverter.feature.converter.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

// ── Shared enums ─────────────────────────────────────────────────────────────

enum class PageSize { A4, LETTER, FIT_TO_IMAGE }

data class ConversionProgress(val current: Int, val total: Int) {
    val fraction: Float get() = if (total == 0) 0f else current.toFloat() / total
    val percent: Int get() = (fraction * 100).toInt()
}

// ── State ────────────────────────────────────────────────────────────────────

data class ConverterState(
    val selectedUris: List<Uri> = emptyList(),
    val pageSize: PageSize = PageSize.A4,
    val progress: ConversionProgress? = null,
    val isConverting: Boolean = false,
    val errorMessage: String? = null
) : MviState

// ── Intents ──────────────────────────────────────────────────────────────────

sealed interface ConverterIntent : MviIntent {
    data class ImagesSelected(val uris: List<Uri>) : ConverterIntent
    data class FilesSelected(val uris: List<Uri>) : ConverterIntent
    data class PageSizeChanged(val size: PageSize) : ConverterIntent
    data class ReorderFiles(val from: Int, val to: Int) : ConverterIntent
    data class RemoveFile(val index: Int) : ConverterIntent
    data class ConvertImagesToPdf(val outputName: String) : ConverterIntent
    data class ConvertOfficeToPdf(val uri: Uri, val outputName: String) : ConverterIntent
    data class MergePdfs(val uris: List<Uri>, val outputName: String) : ConverterIntent
    data class SplitPdf(val uri: Uri, val pageRange: IntRange, val outputName: String) : ConverterIntent
    data object DismissError : ConverterIntent
}

// ── Side Effects ─────────────────────────────────────────────────────────────

sealed interface ConverterSideEffect : MviSideEffect {
    data class ConversionComplete(val filePath: String) : ConverterSideEffect
    data class ShowError(val message: String) : ConverterSideEffect
    data object NavigateBack : ConverterSideEffect
}
