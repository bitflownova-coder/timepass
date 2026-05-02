package com.bitflow.pdfconverter.feature.scanner.contract

import android.graphics.Bitmap
import android.graphics.PointF
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

// ── State ────────────────────────────────────────────────────────────────────

data class ScannerState(
    val pages: List<ScannedPage> = emptyList(),
    val currentFilter: ImageFilter = ImageFilter.ENHANCED,
    val isProcessing: Boolean = false,
    val isCameraReady: Boolean = false,
    val showCropView: Boolean = false,
    val errorMessage: String? = null
) : MviState

data class ScannedPage(
    val id: String,
    val originalBitmap: Bitmap,
    val processedBitmap: Bitmap,
    val cropCorners: List<PointF>,          // 4 corners: TL, TR, BR, BL
    val appliedFilter: ImageFilter
)

enum class ImageFilter { ORIGINAL, ENHANCED, BLACK_WHITE, GRAYSCALE }

// ── Intents (user actions) ───────────────────────────────────────────────────

sealed interface ScannerIntent : MviIntent {
    data object CameraReady : ScannerIntent
    data class PhotoCaptured(val bitmap: Bitmap) : ScannerIntent
    data class CornersAdjusted(val pageId: String, val corners: List<PointF>) : ScannerIntent
    data class ApplyCrop(val pageId: String) : ScannerIntent
    data class FilterChanged(val filter: ImageFilter) : ScannerIntent
    data class ApplyFilterToPage(val pageId: String, val filter: ImageFilter) : ScannerIntent
    data class DeletePage(val pageId: String) : ScannerIntent
    data class ReorderPages(val from: Int, val to: Int) : ScannerIntent
    data class ExportToPdf(val outputName: String) : ScannerIntent
    data class ImportPhotosFromGallery(val bitmaps: List<Bitmap>) : ScannerIntent
    data object HideCropView : ScannerIntent
    data object DismissError : ScannerIntent
}

// ── Side Effects (one-shot events) ───────────────────────────────────────────

sealed interface ScannerSideEffect : MviSideEffect {
    data class NavigateToCrop(val pageId: String) : ScannerSideEffect
    data class PdfExported(val filePath: String) : ScannerSideEffect
    data class ShowError(val message: String) : ScannerSideEffect
    data object NavigateBack : ScannerSideEffect
}
