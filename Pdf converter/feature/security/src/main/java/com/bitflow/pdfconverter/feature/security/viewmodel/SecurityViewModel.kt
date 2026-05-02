package com.bitflow.pdfconverter.feature.security.viewmodel

import android.net.Uri
import androidx.lifecycle.viewModelScope
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.*
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import com.bitflow.pdfconverter.feature.security.contract.SecurityIntent
import com.bitflow.pdfconverter.feature.security.contract.SecuritySideEffect
import com.bitflow.pdfconverter.feature.security.contract.SecurityState
import com.bitflow.pdfconverter.feature.security.engine.PdfEncryptor
import com.bitflow.pdfconverter.feature.security.engine.RedactionTool
import com.bitflow.pdfconverter.feature.security.engine.WatermarkApplier
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SecurityViewModel @Inject constructor(
    private val encryptor: PdfEncryptor,
    private val watermarkApplier: WatermarkApplier,
    private val redactionTool: RedactionTool,
    private val safHelper: SafHelper,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<SecurityState, SecurityIntent, SecuritySideEffect>(SecurityState()) {

    override suspend fun handleIntent(intent: SecurityIntent) {
        when (intent) {
            is SecurityIntent.LoadFile -> loadFile(intent.uri)
            is SecurityIntent.SectionSelected -> updateState { copy(activeSection = intent.section) }
            is SecurityIntent.EncryptPdf -> encryptPdf(intent.userPassword, intent.ownerPassword)
            is SecurityIntent.DecryptPdf -> decryptPdf(intent.password)
            is SecurityIntent.WatermarkTextChanged -> updateState { copy(watermarkText = intent.text) }
            is SecurityIntent.WatermarkOpacityChanged -> updateState { copy(watermarkOpacity = intent.opacity) }
            is SecurityIntent.WatermarkPositionChanged -> updateState { copy(watermarkPosition = intent.position) }
            SecurityIntent.ApplyWatermark -> applyWatermark()
            is SecurityIntent.RedactPages -> redactPages(intent.pageIndices, intent.redactText)
            SecurityIntent.DismissError -> updateState { copy(errorMessage = null) }
        }
    }

    private fun loadFile(uri: Uri) {
        viewModelScope.launch(Dispatchers.IO) {
            val tempFile = runCatching { safHelper.copyToTemp(uri, "sec_input.pdf", null) }.getOrNull()
            updateState {
                copy(
                    fileUri = uri,
                    fileName = tempFile?.name ?: "file.pdf"
                )
            }
        }
    }

    private fun encryptPdf(userPassword: String, ownerPassword: String) {
        val uri = state.value.fileUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "sec_input.pdf", null)!!
                encryptor.encrypt(tempFile, userPassword, ownerPassword)
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Encrypt")
                    registerInMyPdfs(file)
                    sendEffect(SecuritySideEffect.OperationComplete(file.absolutePath, "PDF locked successfully"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SecuritySideEffect.ShowError(e.message ?: "Encryption failed"))
                }
            )
        }
    }

    private fun decryptPdf(password: String) {
        val uri = state.value.fileUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "sec_input.pdf", null)!!
                encryptor.decrypt(tempFile, password)
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Decrypt")
                    registerInMyPdfs(file)
                    sendEffect(SecuritySideEffect.OperationComplete(file.absolutePath, "PDF unlocked successfully"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SecuritySideEffect.ShowError(e.message ?: "Decryption failed"))
                }
            )
        }
    }

    private fun applyWatermark() {
        val uri = state.value.fileUri ?: return
        val text = state.value.watermarkText
        if (text.isBlank()) {
            updateState { copy(errorMessage = "Watermark text cannot be empty") }
            return
        }
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "sec_input.pdf", null)!!
                watermarkApplier.apply(
                    inputFile = tempFile,
                    text = text,
                    opacity = state.value.watermarkOpacity,
                    position = state.value.watermarkPosition
                )
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Watermark")
                    registerInMyPdfs(file)
                    sendEffect(SecuritySideEffect.OperationComplete(file.absolutePath, "Watermark applied"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SecuritySideEffect.ShowError(e.message ?: "Watermark failed"))
                }
            )
        }
    }

    private fun redactPages(pageIndices: List<Int>, redactText: String) {
        val uri = state.value.fileUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "sec_input.pdf", null)!!
                redactionTool.redactPages(tempFile, pageIndices)
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Redact")
                    registerInMyPdfs(file)
                    sendEffect(SecuritySideEffect.OperationComplete(file.absolutePath, "Pages redacted"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(SecuritySideEffect.ShowError(e.message ?: "Redaction failed"))
                }
            )
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
