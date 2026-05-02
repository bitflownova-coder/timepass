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
fun ImageToPdfScreen(
    onNavigateBack: () -> Unit,
    onConversionComplete: (String) -> Unit,
    viewModel: ConverterViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is ConverterSideEffect.ConversionComplete -> onConversionComplete(effect.filePath)
                is ConverterSideEffect.ShowError          -> Timber.e(effect.message)
                else                                      -> Unit
            }
        }
    }

    val imagePicker = rememberLauncherForActivityResult(
        ActivityResultContracts.GetMultipleContents()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) viewModel.onIntent(ConverterIntent.ImagesSelected(uris))
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Images to PDF", onNavigateBack = onNavigateBack) },
        floatingActionButton = {
            FloatingActionButton(onClick = { imagePicker.launch("image/*") }) {
                Icon(Icons.Default.Add, contentDescription = "Add images")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Page size selector
            Text("Page Size", style = MaterialTheme.typography.titleSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                PageSize.entries.forEach { size ->
                    FilterChip(
                        selected = state.pageSize == size,
                        onClick  = { viewModel.onIntent(ConverterIntent.PageSizeChanged(size)) },
                        label    = { Text(size.name.replace('_', ' ')) }
                    )
                }
            }

            // Image list
            if (state.selectedUris.isEmpty()) {
                PdfEmptyState("Tap + to select images")
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    itemsIndexed(state.selectedUris) { index, uri ->
                        ImageListItem(
                            uri     = uri,
                            index   = index,
                            onRemove = { viewModel.onIntent(ConverterIntent.RemoveFile(index)) }
                        )
                    }
                }

                Button(
                    onClick  = { viewModel.onIntent(ConverterIntent.ConvertImagesToPdf("Images_${System.currentTimeMillis()}")) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled  = !state.isConverting
                ) {
                    Text("Convert ${state.selectedUris.size} image(s) to PDF")
                }
            }

            // Progress overlay
            if (state.isConverting) {
                val prog = state.progress
                if (prog != null) {
                    PdfProgressScreen(
                        progress = prog.fraction,
                        message  = "Converting… ${prog.percent}%"
                    )
                } else {
                    PdfLoadingOverlay("Preparing…")
                }
            }
        }
    }
}

@Composable
private fun ImageListItem(uri: Uri, index: Int, onRemove: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "Image ${index + 1}",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = uri.lastPathSegment ?: "file",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(2f)
            )
            IconButton(onClick = onRemove) {
                Icon(Icons.Default.Delete, contentDescription = "Remove", tint = MaterialTheme.colorScheme.error)
            }
        }
    }
}
