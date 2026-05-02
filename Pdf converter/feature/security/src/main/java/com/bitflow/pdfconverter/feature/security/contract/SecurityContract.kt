package com.bitflow.pdfconverter.feature.security.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

data class SecurityState(
    val fileUri: Uri? = null,
    val fileName: String = "",
    val isPasswordProtected: Boolean = false,
    val isProcessing: Boolean = false,
    val activeSection: SecuritySection = SecuritySection.PASSWORD,
    val watermarkText: String = "",
    val watermarkOpacity: Float = 0.3f,
    val watermarkPosition: WatermarkPosition = WatermarkPosition.CENTER,
    val errorMessage: String? = null
) : MviState

enum class SecuritySection { PASSWORD, WATERMARK, REDACT }

enum class WatermarkPosition { CENTER, TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, DIAGONAL }

sealed interface SecurityIntent : MviIntent {
    data class LoadFile(val uri: Uri) : SecurityIntent
    data class SectionSelected(val section: SecuritySection) : SecurityIntent
    // Password
    data class EncryptPdf(val userPassword: String, val ownerPassword: String) : SecurityIntent
    data class DecryptPdf(val password: String) : SecurityIntent
    // Watermark
    data class WatermarkTextChanged(val text: String) : SecurityIntent
    data class WatermarkOpacityChanged(val opacity: Float) : SecurityIntent
    data class WatermarkPositionChanged(val position: WatermarkPosition) : SecurityIntent
    data object ApplyWatermark : SecurityIntent
    // Redaction
    data class RedactPages(val pageIndices: List<Int>, val redactText: String) : SecurityIntent
    data object DismissError : SecurityIntent
}

sealed interface SecuritySideEffect : MviSideEffect {
    data class OperationComplete(val outputPath: String, val message: String) : SecuritySideEffect
    data class ShowError(val message: String) : SecuritySideEffect
    data object NavigateToPasswordInput : SecuritySideEffect
}
