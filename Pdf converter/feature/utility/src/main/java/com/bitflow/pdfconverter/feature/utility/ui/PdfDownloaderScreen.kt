package com.bitflow.pdfconverter.feature.utility.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Link
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.utility.contract.PdfDownloaderIntent
import com.bitflow.pdfconverter.feature.utility.contract.PdfDownloaderSideEffect
import com.bitflow.pdfconverter.feature.utility.viewmodel.PdfDownloaderViewModel
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PdfDownloaderScreen(
    onNavigateBack: () -> Unit,
    onDownloadComplete: (String) -> Unit,
    viewModel: PdfDownloaderViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val keyboard = LocalSoftwareKeyboardController.current

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is PdfDownloaderSideEffect.DownloadComplete -> {
                    keyboard?.hide()
                    onDownloadComplete(effect.filePath)
                }
                is PdfDownloaderSideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Download PDF from Web", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header icon + description
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(
                    Icons.Default.Link,
                    contentDescription = null,
                    modifier = Modifier.size(40.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                Column {
                    Text("Web PDF Downloader", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    Text(
                        "Paste a direct link to a PDF file and download it to your app.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            HorizontalDivider()

            // URL field
            OutlinedTextField(
                value = state.url,
                onValueChange = { viewModel.onIntent(PdfDownloaderIntent.UrlChanged(it)) },
                label = { Text("PDF URL") },
                placeholder = { Text("https://example.com/document.pdf") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Uri,
                    imeAction = ImeAction.Next
                ),
                leadingIcon = { Icon(Icons.Default.Link, contentDescription = null) },
                isError = state.errorMessage != null,
                supportingText = state.errorMessage?.let { { Text(it, color = MaterialTheme.colorScheme.error) } }
            )

            // File name field
            OutlinedTextField(
                value = state.fileName,
                onValueChange = { viewModel.onIntent(PdfDownloaderIntent.FileNameChanged(it)) },
                label = { Text("Save as (file name)") },
                placeholder = { Text("downloaded") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = {
                    keyboard?.hide()
                    if (!state.isDownloading) viewModel.onIntent(PdfDownloaderIntent.Download)
                }),
                suffix = { Text(".pdf") }
            )

            // Progress
            if (state.isDownloading) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            if (state.progress < 0) "Connecting…" else "Downloading… ${state.progress}%",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        if (state.progress < 0) {
                            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                        } else {
                            LinearProgressIndicator(
                                progress = { state.progress / 100f },
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }

            // Download button
            Button(
                onClick = {
                    keyboard?.hide()
                    viewModel.onIntent(PdfDownloaderIntent.Download)
                },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                enabled = !state.isDownloading && state.url.isNotBlank()
            ) {
                Icon(Icons.Default.Download, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (state.isDownloading) "Downloading…" else "Download PDF", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
