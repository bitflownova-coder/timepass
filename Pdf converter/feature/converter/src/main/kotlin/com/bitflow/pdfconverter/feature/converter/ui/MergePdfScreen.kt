package com.bitflow.pdfconverter.feature.converter.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.pdfconverter.core.ui.components.*
import com.bitflow.pdfconverter.feature.converter.contract.*
import com.bitflow.pdfconverter.feature.converter.viewmodel.ConverterViewModel
import timber.log.Timber

@Composable
fun MergePdfScreen(
    onNavigateBack: () -> Unit,
    onMergeComplete: (String) -> Unit,
    viewModel: ConverterViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is ConverterSideEffect.ConversionComplete -> onMergeComplete(effect.filePath)
                is ConverterSideEffect.ShowError -> {
                    Timber.e(effect.message)
                    snackbarHostState.showSnackbar(effect.message)
                }
                else -> Unit
            }
        }
    }

    val pdfPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.GetMultipleContents()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) viewModel.onIntent(ConverterIntent.FilesSelected(
            state.selectedUris + uris
        ))
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Merge PDFs", onNavigateBack = onNavigateBack) },
        floatingActionButton = {
            FloatingActionButton(onClick = { pdfPicker.launch("application/pdf") }) {
                Icon(Icons.Default.Add, contentDescription = "Add PDF")
            }
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            if (state.selectedUris.isEmpty()) {
                PdfEmptyState("Tap + to add PDF files to merge")
            } else {
                Text(
                    "${state.selectedUris.size} file(s) — will be merged in this order",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    itemsIndexed(state.selectedUris) { index, uri ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "${index + 1}. ${uri.lastPathSegment ?: "file.pdf"}",
                                    style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.weight(1f)
                                )
                                IconButton(onClick = {
                                    viewModel.onIntent(ConverterIntent.RemoveFile(index))
                                }) {
                                    Icon(Icons.Default.Delete, "Remove", tint = MaterialTheme.colorScheme.error)
                                }
                            }
                        }
                    }
                }

                Button(
                    onClick = {
                        viewModel.onIntent(ConverterIntent.MergePdfs(
                            uris = state.selectedUris,
                            outputName = "Merged_${System.currentTimeMillis()}"
                        ))
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = state.selectedUris.size >= 2 && !state.isConverting
                ) {
                    Text("Merge ${state.selectedUris.size} PDFs")
                }
            }

            if (state.isConverting) {
                val prog = state.progress
                if (prog != null) {
                    PdfProgressScreen(progress = prog.fraction, message = "Merging… ${prog.percent}%")
                } else {
                    PdfLoadingOverlay("Merging PDFs…")
                }
            }
        }
    }
}
