package com.bitflow.pdfconverter.feature.utility.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.bitflow.pdfconverter.core.ui.components.PdfLoadingOverlay
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.utility.contract.FormField
import com.bitflow.pdfconverter.feature.utility.contract.FormFieldType
import com.bitflow.pdfconverter.feature.utility.contract.StampColor
import com.bitflow.pdfconverter.feature.utility.contract.UtilityIntent
import com.bitflow.pdfconverter.feature.utility.contract.UtilitySideEffect
import com.bitflow.pdfconverter.feature.utility.contract.UtilitySection
import com.bitflow.pdfconverter.feature.utility.viewmodel.UtilityViewModel
import kotlinx.coroutines.flow.collectLatest
import java.util.UUID
import androidx.compose.runtime.collectAsState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UtilityScreen(
    onNavigateBack: () -> Unit,
    initialSection: String = "",
    viewModel: UtilityViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Auto-select section if specified
    LaunchedEffect(initialSection) {
        if (initialSection.isNotBlank()) {
            val section = UtilitySection.entries.find { it.name == initialSection }
            if (section != null) {
                viewModel.onIntent(UtilityIntent.SectionSelected(section))
            }
        }
    }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is UtilitySideEffect.OperationComplete ->
                    snackbarHostState.showSnackbar(effect.message)
                is UtilitySideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Utilities", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            Column(Modifier.fillMaxSize()) {
                TabRow(selectedTabIndex = UtilitySection.entries.indexOf(state.activeSection)) {
                    UtilitySection.entries.forEach { section ->
                        Tab(
                            selected = state.activeSection == section,
                            onClick = { viewModel.onIntent(UtilityIntent.SectionSelected(section)) },
                            text = { Text(section.name.lowercase().replaceFirstChar { it.uppercase() }) }
                        )
                    }
                }

                when (state.activeSection) {
                    UtilitySection.STAMP -> StampTab(
                        fileUri = state.stampSourceUri,
                        stampText = state.stampText,
                        stampColor = state.stampColor,
                        isProcessing = state.isProcessing,
                        onLoadFile = { viewModel.onIntent(UtilityIntent.StampLoadFile(it)) },
                        onTextChange = { viewModel.onIntent(UtilityIntent.StampTextChanged(it)) },
                        onColorChange = { viewModel.onIntent(UtilityIntent.StampColorChanged(it)) },
                        onApply = { viewModel.onIntent(UtilityIntent.ApplyStamp) }
                    )
                    UtilitySection.FORM -> FormTab(
                        fileUri = state.formSourceUri,
                        formFields = state.formFields,
                        isProcessing = state.isProcessing,
                        onLoadFile = { viewModel.onIntent(UtilityIntent.FormLoadFile(it)) },
                        onAddField = { viewModel.onIntent(UtilityIntent.AddFormField(it)) },
                        onUpdateField = { id, value -> viewModel.onIntent(UtilityIntent.UpdateFormField(id, value)) },
                        onRemoveField = { viewModel.onIntent(UtilityIntent.RemoveFormField(it)) },
                        onSave = { viewModel.onIntent(UtilityIntent.SaveForm) }
                    )
                }
            }

            if (state.isProcessing) PdfLoadingOverlay(message = "Processing…")
        }
    }
}

// ─── Stamp Tab ────────────────────────────────────────────────────────────────

@Composable
private fun StampTab(
    fileUri: Uri?,
    stampText: String,
    stampColor: StampColor,
    isProcessing: Boolean,
    onLoadFile: (Uri) -> Unit,
    onTextChange: (String) -> Unit,
    onColorChange: (StampColor) -> Unit,
    onApply: () -> Unit
) {
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let(onLoadFile)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        OutlinedButton(
            onClick = { filePicker.launch("application/pdf") },
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Default.FileOpen, null)
            Spacer(Modifier.width(8.dp))
            Text(if (fileUri != null) "PDF loaded" else "Select PDF")
        }

        OutlinedTextField(
            value = stampText,
            onValueChange = onTextChange,
            label = { Text("Stamp Text") },
            modifier = Modifier.fillMaxWidth()
        )

        Text("Stamp Color", style = MaterialTheme.typography.labelMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StampColor.entries.forEach { color ->
                FilterChip(
                    selected = stampColor == color,
                    onClick = { onColorChange(color) },
                    label = { Text(color.label) }
                )
            }
        }

        Button(
            onClick = onApply,
            modifier = Modifier.fillMaxWidth(),
            enabled = fileUri != null && stampText.isNotBlank() && !isProcessing
        ) {
            Icon(Icons.Default.Edit, null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text("Apply Stamp")
        }
    }
}

// ─── Form Tab ─────────────────────────────────────────────────────────────────

@Composable
private fun FormTab(
    fileUri: Uri?,
    formFields: List<FormField>,
    isProcessing: Boolean,
    onLoadFile: (Uri) -> Unit,
    onAddField: (FormField) -> Unit,
    onUpdateField: (String, String) -> Unit,
    onRemoveField: (String) -> Unit,
    onSave: () -> Unit
) {
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let(onLoadFile)
    }
    var showAddDialog by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = { filePicker.launch("application/pdf") },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.FileOpen, null)
                Spacer(Modifier.width(8.dp))
                Text(if (fileUri != null) "PDF loaded" else "Select PDF")
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = { showAddDialog = true },
                    modifier = Modifier.weight(1f),
                    enabled = fileUri != null
                ) {
                    Icon(Icons.Default.Add, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Add Field")
                }
                Button(
                    onClick = onSave,
                    modifier = Modifier.weight(1f),
                    enabled = fileUri != null && formFields.isNotEmpty() && !isProcessing
                ) {
                    Icon(Icons.Default.Save, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Save Form")
                }
            }
        }

        LazyColumn(
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(formFields, key = { it.id }) { field ->
                FormFieldCard(
                    field = field,
                    onValueChange = { onUpdateField(field.id, it) },
                    onRemove = { onRemoveField(field.id) }
                )
            }
        }
    }

    if (showAddDialog) {
        AddFieldDialog(
            onConfirm = { label, type ->
                onAddField(
                    FormField(
                        id = UUID.randomUUID().toString(),
                        label = label,
                        type = type,
                        pageIndex = 0
                    )
                )
                showAddDialog = false
            },
            onDismiss = { showAddDialog = false }
        )
    }
}

@Composable
private fun FormFieldCard(
    field: FormField,
    onValueChange: (String) -> Unit,
    onRemove: () -> Unit
) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(
                    "${field.label} (${field.type.name.lowercase()})",
                    style = MaterialTheme.typography.labelMedium
                )
                when (field.type) {
                    FormFieldType.TEXT, FormFieldType.SIGNATURE -> OutlinedTextField(
                        value = field.value,
                        onValueChange = onValueChange,
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        placeholder = { Text(if (field.type == FormFieldType.SIGNATURE) "Sign here…" else "Enter value…") }
                    )
                    FormFieldType.CHECKBOX -> Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                        Checkbox(
                            checked = field.value == "true",
                            onCheckedChange = { onValueChange(it.toString()) }
                        )
                        Text(field.label, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
            IconButton(onClick = onRemove) {
                Icon(Icons.Default.Delete, "Remove field", tint = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun AddFieldDialog(onConfirm: (String, FormFieldType) -> Unit, onDismiss: () -> Unit) {
    var label by remember { mutableStateOf("") }
    var type by remember { mutableStateOf(FormFieldType.TEXT) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Form Field") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = label,
                    onValueChange = { label = it },
                    label = { Text("Field Label") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Text("Field Type", style = MaterialTheme.typography.labelMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FormFieldType.entries.forEach { fieldType ->
                        FilterChip(
                            selected = type == fieldType,
                            onClick = { type = fieldType },
                            label = { Text(fieldType.name.lowercase().replaceFirstChar { it.uppercase() }) }
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { if (label.isNotBlank()) onConfirm(label, type) },
                enabled = label.isNotBlank()
            ) { Text("Add") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
