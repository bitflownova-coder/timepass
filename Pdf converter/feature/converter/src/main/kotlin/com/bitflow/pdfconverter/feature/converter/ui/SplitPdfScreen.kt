package com.bitflow.pdfconverter.feature.converter.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.pdfconverter.core.ui.components.*
import com.bitflow.pdfconverter.feature.converter.contract.*
import com.bitflow.pdfconverter.feature.converter.viewmodel.ConverterViewModel
import timber.log.Timber

@Composable
fun SplitPdfScreen(
    onNavigateBack: () -> Unit,
    onSplitComplete: (String) -> Unit,
    viewModel: ConverterViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    var sourceUri by remember { mutableStateOf<Uri?>(null) }
    var fromPage by remember { mutableStateOf("1") }
    var toPage by remember { mutableStateOf("1") }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is ConverterSideEffect.ConversionComplete -> onSplitComplete(effect.filePath)
                is ConverterSideEffect.ShowError -> {
                    Timber.e(effect.message)
                    snackbarHostState.showSnackbar(effect.message)
                }
                else -> Unit
            }
        }
    }

    val pdfPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { sourceUri = it }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Split PDF", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedButton(
                onClick = { pdfPicker.launch("application/pdf") },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.FileOpen, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (sourceUri != null) sourceUri!!.lastPathSegment ?: "PDF selected" else "Select PDF to split")
            }

            if (sourceUri != null) {
                Text("Page Range to Extract", style = MaterialTheme.typography.titleSmall)
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(
                        value = fromPage,
                        onValueChange = { fromPage = it.filter { c -> c.isDigit() } },
                        label = { Text("From page") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = toPage,
                        onValueChange = { toPage = it.filter { c -> c.isDigit() } },
                        label = { Text("To page") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                val from = fromPage.toIntOrNull() ?: 1
                val to = toPage.toIntOrNull() ?: 1
                val validRange = from >= 1 && to >= from

                if (!validRange && fromPage.isNotBlank() && toPage.isNotBlank()) {
                    Text(
                        "\"To\" page must be ≥ \"From\" page",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error
                    )
                }

                Button(
                    onClick = {
                        sourceUri?.let { uri ->
                            viewModel.onIntent(ConverterIntent.SplitPdf(
                                uri = uri,
                                pageRange = (from - 1) until to, // 0-based range
                                outputName = "Split_p${from}_${to}_${System.currentTimeMillis()}"
                            ))
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = validRange && !state.isConverting
                ) {
                    Text("Extract pages $from – $to")
                }
            }

            if (state.isConverting) {
                PdfLoadingOverlay("Splitting PDF…")
            }
        }
    }
}
