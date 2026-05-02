package com.bitflow.pdfconverter.feature.utility.viewmodel

import android.net.Uri
import androidx.lifecycle.viewModelScope
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.*
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import com.bitflow.pdfconverter.feature.utility.contract.FormField
import com.bitflow.pdfconverter.feature.utility.contract.UtilityIntent
import com.bitflow.pdfconverter.feature.utility.contract.UtilitySideEffect
import com.bitflow.pdfconverter.feature.utility.contract.UtilityState
import com.bitflow.pdfconverter.feature.utility.engine.FormBuilder
import com.bitflow.pdfconverter.feature.utility.engine.StampPlacer
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class UtilityViewModel @Inject constructor(
    private val stampPlacer: StampPlacer,
    private val formBuilder: FormBuilder,
    private val safHelper: SafHelper,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<UtilityState, UtilityIntent, UtilitySideEffect>(UtilityState()) {

    override suspend fun handleIntent(intent: UtilityIntent) {
        when (intent) {
            is UtilityIntent.SectionSelected -> updateState { copy(activeSection = intent.section) }
            // Stamp
            is UtilityIntent.StampLoadFile -> loadStampFile(intent.uri)
            is UtilityIntent.StampTextChanged -> updateState { copy(stampText = intent.text) }
            is UtilityIntent.StampColorChanged -> updateState { copy(stampColor = intent.color) }
            is UtilityIntent.StampPagesChanged -> updateState { copy(stampPageIndices = intent.pageIndices) }
            UtilityIntent.ApplyStamp -> applyStamp()
            // Form
            is UtilityIntent.FormLoadFile -> loadFormFile(intent.uri)
            is UtilityIntent.AddFormField -> updateState { copy(formFields = formFields + intent.field) }
            is UtilityIntent.UpdateFormField -> updateFormField(intent.fieldId, intent.value)
            is UtilityIntent.RemoveFormField -> updateState {
                copy(formFields = formFields.filter { it.id != intent.fieldId })
            }
            UtilityIntent.SaveForm -> saveForm()
            UtilityIntent.DismissError -> updateState { copy(errorMessage = null) }
        }
    }

    private fun loadStampFile(uri: Uri) {
        updateState { copy(stampSourceUri = uri) }
    }

    private fun loadFormFile(uri: Uri) {
        updateState { copy(formSourceUri = uri, formFields = emptyList()) }
    }

    private fun applyStamp() {
        val uri = state.value.stampSourceUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "stamp_input.pdf", null)!!
                stampPlacer.applyStamp(
                    inputFile = tempFile,
                    stampText = state.value.stampText,
                    stampColor = state.value.stampColor,
                    pageIndices = state.value.stampPageIndices
                )
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Stamp")
                    registerInMyPdfs(file)
                    sendEffect(UtilitySideEffect.OperationComplete(file.absolutePath, "Stamp applied"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(UtilitySideEffect.ShowError(e.message ?: "Stamp failed"))
                }
            )
        }
    }

    private fun updateFormField(fieldId: String, value: String) {
        val updated = state.value.formFields.map { field ->
            if (field.id == fieldId) field.copy(value = value) else field
        }
        updateState { copy(formFields = updated) }
    }

    private fun saveForm() {
        val uri = state.value.formSourceUri ?: return
        viewModelScope.launch(Dispatchers.IO) {
            updateState { copy(isProcessing = true, errorMessage = null) }
            val result = runCatchingPdf {
                val tempFile = safHelper.copyToTemp(uri, "form_input.pdf", null)!!
                formBuilder.applyFormFields(tempFile, state.value.formFields)
            }
            updateState { copy(isProcessing = false) }
            result.fold(
                onSuccess = { file ->
                    fileManager.publishToDownloads(file, "Form")
                    registerInMyPdfs(file)
                    sendEffect(UtilitySideEffect.OperationComplete(file.absolutePath, "Form saved"))
                },
                onFailure = { e ->
                    updateState { copy(errorMessage = e.message) }
                    sendEffect(UtilitySideEffect.ShowError(e.message ?: "Save failed"))
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
