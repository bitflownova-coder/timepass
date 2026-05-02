package com.bitflow.pdfconverter.feature.optimization.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.bitflow.pdfconverter.core.ui.components.PdfErrorState
import com.bitflow.pdfconverter.core.ui.components.PdfLoadingOverlay
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.optimization.contract.OptimizationIntent
import com.bitflow.pdfconverter.feature.optimization.contract.OptimizationSideEffect
import com.bitflow.pdfconverter.feature.optimization.contract.TargetDpi
import com.bitflow.pdfconverter.feature.optimization.viewmodel.OptimizationViewModel
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OptimizationScreen(
    onNavigateBack: () -> Unit,
    fileUri: String = "",
    viewModel: OptimizationViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Auto-load file if URI was passed via navigation arg
    LaunchedEffect(fileUri) {
        if (fileUri.isNotBlank()) {
            viewModel.onIntent(OptimizationIntent.LoadFile(android.net.Uri.parse(fileUri)))
        }
    }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is OptimizationSideEffect.CompressionComplete -> {
                    val savedKb = effect.savedBytes / 1024
                    snackbarHostState.showSnackbar("Saved! Reduced by ${savedKb}KB")
                }
                is OptimizationSideEffect.BatchComplete ->
                    snackbarHostState.showSnackbar("Batch complete: ${effect.outputPaths.size} files compressed")
                is OptimizationSideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { viewModel.onIntent(OptimizationIntent.LoadFile(it)) }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Optimize PDF", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // File selection card
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("Input PDF", style = MaterialTheme.typography.titleSmall)
                        if (state.fileUri != null) {
                            Text(state.fileName, style = MaterialTheme.typography.bodyMedium)
                            Text(
                                "Original size: ${state.originalSizeBytes / 1024}KB",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            if (state.compressedSizeBytes > 0) {
                                Text(
                                    "Compressed size: ${state.compressedSizeBytes / 1024}KB",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.primary,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                        } else {
                            Text(
                                "No file selected",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        OutlinedButton(
                            onClick = { filePicker.launch("application/pdf") },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.FileOpen, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("Select PDF")
                        }
                    }
                }

                // DPI selector
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("Image Resolution", style = MaterialTheme.typography.titleSmall)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TargetDpi.entries.forEach { dpi ->
                                FilterChip(
                                    selected = state.selectedDpi == dpi.value,
                                    onClick = { viewModel.onIntent(OptimizationIntent.DpiSelected(dpi.value)) },
                                    label = { Text(dpi.label, style = MaterialTheme.typography.labelSmall) }
                                )
                            }
                        }
                    }
                }

                // Quality slider
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("JPEG Quality", style = MaterialTheme.typography.titleSmall)
                            Text("${state.qualityPercent}%", style = MaterialTheme.typography.bodyMedium)
                        }
                        Slider(
                            value = state.qualityPercent.toFloat(),
                            onValueChange = { viewModel.onIntent(OptimizationIntent.QualityChanged(it.toInt())) },
                            valueRange = 10f..95f,
                            steps = 16
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Smaller file", style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("Better quality", style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }

                // Progress if processing
                if (state.isProcessing) {
                    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(state.progressLabel, style = MaterialTheme.typography.bodySmall)
                            LinearProgressIndicator(
                                progress = { state.progress },
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }

                // Error
                state.errorMessage?.let { msg ->
                    PdfErrorState(
                        message = msg,
                        onRetry = { viewModel.onIntent(OptimizationIntent.DismissError) }
                    )
                }

                // Action button
                Button(
                    onClick = { viewModel.onIntent(OptimizationIntent.Compress) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = state.fileUri != null && !state.isProcessing
                ) {
                    Icon(Icons.Default.Tune, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Compress PDF")
                }
            }

            if (state.isProcessing) {
                PdfLoadingOverlay(message = state.progressLabel.ifEmpty { "Compressing…" })
            }
        }
    }
}
