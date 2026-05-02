package com.bitflow.pdfconverter.feature.utility.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

data class UtilityState(
    val activeSection: UtilitySection = UtilitySection.STAMP,
    // Stamp
    val stampSourceUri: Uri? = null,
    val stampText: String = "APPROVED",
    val stampColor: StampColor = StampColor.RED,
    val stampPageIndices: List<Int> = emptyList(),
    // Form
    val formSourceUri: Uri? = null,
    val formFields: List<FormField> = emptyList(),
    // General
    val isProcessing: Boolean = false,
    val errorMessage: String? = null
) : MviState

enum class UtilitySection { STAMP, FORM }

enum class StampColor(val label: String) {
    RED("Red"), GREEN("Green"), BLUE("Blue"), BLACK("Black")
}

data class FormField(
    val id: String,
    val label: String,
    val type: FormFieldType,
    val value: String = "",
    val pageIndex: Int = 0,
    val x: Float = 72f,
    val y: Float = 72f
)

enum class FormFieldType { TEXT, CHECKBOX, SIGNATURE }

sealed interface UtilityIntent : MviIntent {
    data class SectionSelected(val section: UtilitySection) : UtilityIntent
    // Stamp
    data class StampLoadFile(val uri: Uri) : UtilityIntent
    data class StampTextChanged(val text: String) : UtilityIntent
    data class StampColorChanged(val color: StampColor) : UtilityIntent
    data class StampPagesChanged(val pageIndices: List<Int>) : UtilityIntent
    data object ApplyStamp : UtilityIntent
    // Form
    data class FormLoadFile(val uri: Uri) : UtilityIntent
    data class AddFormField(val field: FormField) : UtilityIntent
    data class UpdateFormField(val fieldId: String, val value: String) : UtilityIntent
    data class RemoveFormField(val fieldId: String) : UtilityIntent
    data object SaveForm : UtilityIntent
    data object DismissError : UtilityIntent
}

sealed interface UtilitySideEffect : MviSideEffect {
    data class OperationComplete(val outputPath: String, val message: String) : UtilitySideEffect
    data class ShowError(val message: String) : UtilitySideEffect
}
