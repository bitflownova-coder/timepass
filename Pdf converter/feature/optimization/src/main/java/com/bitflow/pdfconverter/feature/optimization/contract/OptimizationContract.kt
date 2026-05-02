package com.bitflow.pdfconverter.feature.optimization.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

data class OptimizationState(
    val fileUri: Uri? = null,
    val fileName: String = "",
    val originalSizeBytes: Long = 0L,
    val compressedSizeBytes: Long = 0L,
    val selectedDpi: Int = 150,
    val qualityPercent: Int = 80,
    val maxTargetSizeKb: Long = 0L, // 0 = no limit
    val isProcessing: Boolean = false,
    val progress: Float = 0f,
    val progressLabel: String = "",
    val errorMessage: String? = null,
    val batchFiles: List<BatchFile> = emptyList()
) : MviState

data class BatchFile(
    val uri: Uri,
    val name: String,
    val originalSizeBytes: Long,
    val compressedPath: String? = null,
    val status: BatchStatus = BatchStatus.PENDING
)

enum class BatchStatus { PENDING, PROCESSING, DONE, FAILED }

enum class TargetDpi(val value: Int, val label: String) {
    SCREEN(72, "Screen (72 DPI)"),
    STANDARD(150, "Standard (150 DPI)"),
    PRINT(300, "Print (300 DPI)")
}

sealed interface OptimizationIntent : MviIntent {
    data class LoadFile(val uri: Uri) : OptimizationIntent
    data class DpiSelected(val dpi: Int) : OptimizationIntent
    data class QualityChanged(val quality: Int) : OptimizationIntent
    data class MaxSizeSet(val sizeKb: Long) : OptimizationIntent
    data object Compress : OptimizationIntent
    data class LoadBatch(val uris: List<Uri>) : OptimizationIntent
    data object CompressBatch : OptimizationIntent
    data object DismissError : OptimizationIntent
    data object ClearFile : OptimizationIntent
}

sealed interface OptimizationSideEffect : MviSideEffect {
    data class CompressionComplete(val outputPath: String, val savedBytes: Long) : OptimizationSideEffect
    data class BatchComplete(val outputPaths: List<String>) : OptimizationSideEffect
    data class ShowError(val message: String) : OptimizationSideEffect
}
