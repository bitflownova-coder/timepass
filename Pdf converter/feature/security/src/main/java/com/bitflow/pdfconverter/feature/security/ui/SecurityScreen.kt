package com.bitflow.pdfconverter.feature.security.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.LockOpen
import androidx.compose.material.icons.filled.TextFields
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.bitflow.pdfconverter.core.ui.components.PdfLoadingOverlay
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.security.contract.SecurityIntent
import com.bitflow.pdfconverter.feature.security.contract.SecuritySection
import com.bitflow.pdfconverter.feature.security.contract.SecuritySideEffect
import com.bitflow.pdfconverter.feature.security.contract.WatermarkPosition
import com.bitflow.pdfconverter.feature.security.viewmodel.SecurityViewModel
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SecurityScreen(
    onNavigateBack: () -> Unit,
    fileUri: String = "",
    initialSection: String = "",
    viewModel: SecurityViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Auto-select section if specified
    LaunchedEffect(initialSection) {
        if (initialSection.isNotBlank()) {
            val section = SecuritySection.entries.find { it.name == initialSection }
            if (section != null) {
                viewModel.onIntent(SecurityIntent.SectionSelected(section))
            }
        }
    }

    // Auto-load file if URI was passed via navigation arg
    LaunchedEffect(fileUri) {
        if (fileUri.isNotBlank()) {
            viewModel.onIntent(SecurityIntent.LoadFile(android.net.Uri.parse(fileUri)))
        }
    }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is SecuritySideEffect.OperationComplete ->
                    snackbarHostState.showSnackbar(effect.message)
                is SecuritySideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
                SecuritySideEffect.NavigateToPasswordInput -> Unit
            }
        }
    }

    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { viewModel.onIntent(SecurityIntent.LoadFile(it)) }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Security", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // File picker
                OutlinedButton(
                    onClick = { filePicker.launch("application/pdf") },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.FileOpen, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text(if (state.fileUri != null) state.fileName else "Select PDF")
                }

                // Section tabs
                TabRow(selectedTabIndex = SecuritySection.entries.indexOf(state.activeSection)) {
                    SecuritySection.entries.forEach { section ->
                        Tab(
                            selected = state.activeSection == section,
                            onClick = { viewModel.onIntent(SecurityIntent.SectionSelected(section)) },
                            text = { Text(section.name.lowercase().replaceFirstChar { it.uppercase() }) }
                        )
                    }
                }

                when (state.activeSection) {
                    SecuritySection.PASSWORD -> PasswordSection(
                        enabled = state.fileUri != null && !state.isProcessing,
                        onEncrypt = { user, owner ->
                            viewModel.onIntent(SecurityIntent.EncryptPdf(user, owner))
                        },
                        onDecrypt = { pass ->
                            viewModel.onIntent(SecurityIntent.DecryptPdf(pass))
                        }
                    )
                    SecuritySection.WATERMARK -> WatermarkSection(
                        text = state.watermarkText,
                        opacity = state.watermarkOpacity,
                        position = state.watermarkPosition,
                        enabled = state.fileUri != null && !state.isProcessing,
                        onTextChange = { viewModel.onIntent(SecurityIntent.WatermarkTextChanged(it)) },
                        onOpacityChange = { viewModel.onIntent(SecurityIntent.WatermarkOpacityChanged(it)) },
                        onPositionChange = { viewModel.onIntent(SecurityIntent.WatermarkPositionChanged(it)) },
                        onApply = { viewModel.onIntent(SecurityIntent.ApplyWatermark) }
                    )
                    SecuritySection.REDACT -> RedactSection(
                        enabled = state.fileUri != null && !state.isProcessing,
                        onRedact = { pages ->
                            viewModel.onIntent(SecurityIntent.RedactPages(pages, ""))
                        }
                    )
                }

                state.errorMessage?.let {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                        Text(
                            text = it,
                            modifier = Modifier.padding(12.dp),
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }
            }

            if (state.isProcessing) {
                PdfLoadingOverlay(message = "Processing…")
            }
        }
    }
}

@Composable
private fun PasswordSection(
    enabled: Boolean,
    onEncrypt: (String, String) -> Unit,
    onDecrypt: (String) -> Unit
) {
    var userPassword by remember { mutableStateOf("") }
    var ownerPassword by remember { mutableStateOf("") }
    var decryptPassword by remember { mutableStateOf("") }

    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Encrypt PDF", style = MaterialTheme.typography.titleSmall)
            OutlinedTextField(
                value = userPassword,
                onValueChange = { userPassword = it },
                label = { Text("User Password") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                value = ownerPassword,
                onValueChange = { ownerPassword = it },
                label = { Text("Owner Password") },
                modifier = Modifier.fillMaxWidth()
            )
            Button(
                onClick = { onEncrypt(userPassword, ownerPassword) },
                modifier = Modifier.fillMaxWidth(),
                enabled = enabled && userPassword.isNotBlank()
            ) {
                Icon(Icons.Default.Lock, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Lock PDF")
            }

            HorizontalDivider()

            Text("Remove Password", style = MaterialTheme.typography.titleSmall)
            OutlinedTextField(
                value = decryptPassword,
                onValueChange = { decryptPassword = it },
                label = { Text("Current Password") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedButton(
                onClick = { onDecrypt(decryptPassword) },
                modifier = Modifier.fillMaxWidth(),
                enabled = enabled && decryptPassword.isNotBlank()
            ) {
                Icon(Icons.Default.LockOpen, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Unlock PDF")
            }
        }
    }
}

@Composable
private fun WatermarkSection(
    text: String,
    opacity: Float,
    position: WatermarkPosition,
    enabled: Boolean,
    onTextChange: (String) -> Unit,
    onOpacityChange: (Float) -> Unit,
    onPositionChange: (WatermarkPosition) -> Unit,
    onApply: () -> Unit
) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                label = { Text("Watermark Text") },
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = { Icon(Icons.Default.TextFields, null) }
            )

            Text("Opacity: ${(opacity * 100).toInt()}%", style = MaterialTheme.typography.bodySmall)
            Slider(
                value = opacity,
                onValueChange = onOpacityChange,
                valueRange = 0.05f..0.9f
            )

            Text("Position", style = MaterialTheme.typography.labelMedium)
            // Two rows of position chips
            val positions = WatermarkPosition.entries
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                positions.take(3).forEach { pos ->
                    FilterChip(
                        selected = position == pos,
                        onClick = { onPositionChange(pos) },
                        label = { Text(pos.name.lowercase().replace('_', ' '), style = MaterialTheme.typography.labelSmall) }
                    )
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                positions.drop(3).forEach { pos ->
                    FilterChip(
                        selected = position == pos,
                        onClick = { onPositionChange(pos) },
                        label = { Text(pos.name.lowercase().replace('_', ' '), style = MaterialTheme.typography.labelSmall) }
                    )
                }
            }

            Button(
                onClick = onApply,
                modifier = Modifier.fillMaxWidth(),
                enabled = enabled && text.isNotBlank()
            ) {
                Text("Apply Watermark")
            }
        }
    }
}

@Composable
private fun RedactSection(
    enabled: Boolean,
    onRedact: (List<Int>) -> Unit
) {
    var pageInput by remember { mutableStateOf("") }

    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Redact Pages", style = MaterialTheme.typography.titleSmall)
            Text(
                "Enter comma-separated page numbers to redact (e.g. 1,3,5)",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            OutlinedTextField(
                value = pageInput,
                onValueChange = { pageInput = it },
                label = { Text("Page Numbers") },
                modifier = Modifier.fillMaxWidth()
            )
            Button(
                onClick = {
                    val pages = pageInput.split(",")
                        .mapNotNull { it.trim().toIntOrNull()?.minus(1) }
                        .filter { it >= 0 }
                    onRedact(pages)
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = enabled && pageInput.isNotBlank()
            ) {
                Icon(Icons.Default.VisibilityOff, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Redact Selected Pages")
            }
        }
    }
}
