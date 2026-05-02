package com.bitflow.pdfconverter.feature.converter.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.pdfconverter.core.ui.components.*
import com.bitflow.pdfconverter.feature.converter.contract.*
import com.bitflow.pdfconverter.feature.converter.viewmodel.ConverterViewModel

@Composable
fun OfficeToPdfScreen(
    onNavigateBack: () -> Unit,
    viewModel: ConverterViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    var sourceUri by remember { mutableStateOf<Uri?>(null) }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is ConverterSideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
                else -> Unit
            }
        }
    }

    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { sourceUri = it }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Office to PDF", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                Icons.Default.Description,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.primary
            )

            Text(
                "Convert Word, Excel or PowerPoint files to PDF",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            OutlinedButton(
                onClick = { filePicker.launch("*/*") },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.FileOpen, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (sourceUri != null) sourceUri!!.lastPathSegment ?: "File selected" else "Select .docx / .xlsx / .pptx")
            }

            if (sourceUri != null) {
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Note", style = MaterialTheme.typography.titleSmall)
                        Text(
                            "Full Office-to-PDF conversion requires the Apache POI library which is not yet " +
                            "included in this build. This feature will be enabled in a future update. " +
                            "In the meantime you can open the file in a third-party app and use its " +
                            "\"Print to PDF\" option.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Button(
                    onClick = {
                        sourceUri?.let { uri ->
                            viewModel.onIntent(ConverterIntent.ConvertOfficeToPdf(uri, "converted"))
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !state.isConverting
                ) {
                    Text("Convert to PDF")
                }
            }

            if (state.isConverting) {
                PdfLoadingOverlay("Converting…")
            }
        }
    }
}
