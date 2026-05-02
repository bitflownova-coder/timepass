package com.bitflow.pdfconverter.feature.smarttools.ui

import android.Manifest
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.FileOpen
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.TextFields
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.bitflow.pdfconverter.core.ui.components.PdfEmptyState
import com.bitflow.pdfconverter.core.ui.components.PdfLoadingOverlay
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.smarttools.contract.SearchMatch
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartSection
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartToolsIntent
import com.bitflow.pdfconverter.feature.smarttools.contract.SmartToolsSideEffect
import com.bitflow.pdfconverter.feature.smarttools.viewmodel.SmartToolsViewModel
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmartToolsScreen(
    onNavigateBack: () -> Unit,
    initialSection: String = "",
    viewModel: SmartToolsViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Auto-select section if specified
    LaunchedEffect(initialSection) {
        if (initialSection.isNotBlank()) {
            val section = SmartSection.entries.find { it.name == initialSection }
            if (section != null) {
                viewModel.onIntent(SmartToolsIntent.SectionSelected(section))
            }
        }
    }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is SmartToolsSideEffect.OcrComplete ->
                    snackbarHostState.showSnackbar("OCR complete — ${effect.text.length} characters extracted")
                is SmartToolsSideEffect.QrDetected ->
                    snackbarHostState.showSnackbar("QR: ${effect.value}")
                is SmartToolsSideEffect.QrImageSaved ->
                    snackbarHostState.showSnackbar("QR saved to ${effect.path}")
                is SmartToolsSideEffect.TxtFileSaved ->
                    snackbarHostState.showSnackbar("Text saved to ${effect.path}")
                is SmartToolsSideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
                SmartToolsSideEffect.CopyToClipboard ->
                    snackbarHostState.showSnackbar("Copied to clipboard")
            }
        }
    }

    Scaffold(
        topBar = { PdfTopBar(title = "Smart Tools", onNavigateBack = onNavigateBack) },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Section tab row
            ScrollableTabRow(
                selectedTabIndex = SmartSection.entries.indexOf(state.activeSection),
                edgePadding = 8.dp
            ) {
                mapOf(
                    SmartSection.OCR to "OCR",
                    SmartSection.QR_SCAN to "QR Scan",
                    SmartSection.QR_GEN to "QR Gen",
                    SmartSection.PDF_SEARCH to "Search"
                ).forEach { (section, label) ->
                    Tab(
                        selected = state.activeSection == section,
                        onClick = { viewModel.onIntent(SmartToolsIntent.SectionSelected(section)) },
                        text = { Text(label) }
                    )
                }
            }

            Box(modifier = Modifier.fillMaxSize()) {
                when (state.activeSection) {
                    SmartSection.OCR -> OcrTab(
                        fileUri = state.ocrSourceUri,
                        ocrResult = state.ocrResult,
                        isProcessing = state.isOcrProcessing,
                        pageIndex = state.ocrPageIndex,
                        onLoadFile = { viewModel.onIntent(SmartToolsIntent.OcrLoadFile(it)) },
                        onPageChange = { viewModel.onIntent(SmartToolsIntent.OcrPageChanged(it)) },
                        onRunOcr = { viewModel.onIntent(SmartToolsIntent.RunOcr) },
                        onCopy = { viewModel.onIntent(SmartToolsIntent.CopyOcrText) },
                        onSave = { viewModel.onIntent(SmartToolsIntent.SaveOcrAsTxt) }
                    )
                    SmartSection.QR_SCAN -> QrScanTab(
                        qrResult = state.qrResult,
                        onQrScanned = { viewModel.onIntent(SmartToolsIntent.QrScanned(it)) }
                    )
                    SmartSection.QR_GEN -> QrGeneratorTab(
                        inputText = state.qrInputText,
                        bitmapPath = state.qrBitmapPath,
                        onTextChange = { viewModel.onIntent(SmartToolsIntent.QrTextChanged(it)) },
                        onGenerate = { viewModel.onIntent(SmartToolsIntent.GenerateQr) },
                        onSave = { viewModel.onIntent(SmartToolsIntent.SaveQrImage) }
                    )
                    SmartSection.PDF_SEARCH -> PdfSearchTab(
                        searchPdfUri = state.searchPdfUri,
                        query = state.searchQuery,
                        results = state.searchResults,
                        isSearching = state.isSearching,
                        onLoadFile = { viewModel.onIntent(SmartToolsIntent.SearchLoadFile(it)) },
                        onQueryChange = { viewModel.onIntent(SmartToolsIntent.SearchQueryChanged(it)) },
                        onSearch = { viewModel.onIntent(SmartToolsIntent.RunSearch) }
                    )
                }
            }
        }
    }
}

// ─── OCR Tab ─────────────────────────────────────────────────────────────────

@Composable
private fun OcrTab(
    fileUri: Uri?,
    ocrResult: String,
    isProcessing: Boolean,
    pageIndex: Int,
    onLoadFile: (Uri) -> Unit,
    onPageChange: (Int) -> Unit,
    onRunOcr: () -> Unit,
    onCopy: () -> Unit,
    onSave: () -> Unit
) {
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let(onLoadFile)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
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

        if (fileUri != null) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Page:", style = MaterialTheme.typography.labelMedium)
                Spacer(Modifier.width(8.dp))
                OutlinedTextField(
                    value = (pageIndex + 1).toString(),
                    onValueChange = { it.toIntOrNull()?.let { n -> onPageChange((n - 1).coerceAtLeast(0)) } },
                    modifier = Modifier.width(72.dp),
                    singleLine = true
                )
            }

            Button(onClick = onRunOcr, modifier = Modifier.fillMaxWidth(), enabled = !isProcessing) {
                Icon(Icons.Default.TextFields, null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Extract Text (OCR)")
            }
        }

        if (isProcessing) {
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        }

        if (ocrResult.isNotEmpty()) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onCopy, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.ContentCopy, null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Copy")
                }
                OutlinedButton(onClick = onSave, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.Save, null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Save TXT")
                }
            }

            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                SelectionContainer {
                    Text(
                        text = ocrResult,
                        modifier = Modifier.padding(12.dp),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

// ─── QR Scan Tab ─────────────────────────────────────────────────────────────

@OptIn(ExperimentalPermissionsApi::class)
@Composable
private fun QrScanTab(
    qrResult: String,
    onQrScanned: (String) -> Unit
) {
    val cameraPermission = rememberPermissionState(Manifest.permission.CAMERA)

    if (!cameraPermission.status.isGranted) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(Icons.Default.QrCodeScanner, null, modifier = Modifier.size(64.dp), tint = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(16.dp))
            Text("Camera permission is required to scan QR codes.", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(12.dp))
            Button(onClick = { cameraPermission.launchPermissionRequest() }) { Text("Grant Permission") }
        }
        return
    }

    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    // Prevent duplicate callbacks for the same barcode
    var lastScanned by remember { mutableStateOf("") }
    val barcodeScanner = remember { BarcodeScanning.getClient() }

    Column(modifier = Modifier.fillMaxSize()) {
        // Live camera preview — takes up most of the tab
        Box(modifier = Modifier.weight(1f)) {
            AndroidView(
                factory = { ctx ->
                    val previewView = PreviewView(ctx)
                    val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                    cameraProviderFuture.addListener({
                        val cameraProvider = cameraProviderFuture.get()
                        val preview = Preview.Builder().build()
                            .also { it.setSurfaceProvider(previewView.surfaceProvider) }
                        val analysis = ImageAnalysis.Builder()
                            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                            .build()
                        analysis.setAnalyzer(ContextCompat.getMainExecutor(ctx)) { imageProxy ->
                            @androidx.camera.core.ExperimentalGetImage
                            val mediaImage = imageProxy.image
                            if (mediaImage != null) {
                                val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
                                barcodeScanner.process(image)
                                    .addOnSuccessListener { barcodes ->
                                        barcodes.firstOrNull()?.rawValue?.let { value ->
                                            if (value != lastScanned) {
                                                lastScanned = value
                                                onQrScanned(value)
                                            }
                                        }
                                    }
                                    .addOnCompleteListener { imageProxy.close() }
                            } else {
                                imageProxy.close()
                            }
                        }
                        cameraProvider.unbindAll()
                        cameraProvider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis)
                    }, ContextCompat.getMainExecutor(ctx))
                    previewView
                },
                modifier = Modifier.fillMaxSize()
            )
        }

        // Result card
        if (qrResult.isNotEmpty()) {
            ElevatedCard(modifier = Modifier.fillMaxWidth().padding(12.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Last Scan Result:", style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(4.dp))
                    SelectionContainer {
                        Text(qrResult, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        } else {
            Text(
                "Point the camera at a QR code or barcode",
                modifier = Modifier.padding(12.dp).align(Alignment.CenterHorizontally),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

// ─── QR Generator Tab ────────────────────────────────────────────────────────

@Composable
private fun QrGeneratorTab(
    inputText: String,
    bitmapPath: String?,
    onTextChange: (String) -> Unit,
    onGenerate: () -> Unit,
    onSave: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        OutlinedTextField(
            value = inputText,
            onValueChange = onTextChange,
            label = { Text("Text or URL") },
            modifier = Modifier.fillMaxWidth(),
            maxLines = 4
        )

        Button(
            onClick = onGenerate,
            modifier = Modifier.fillMaxWidth(),
            enabled = inputText.isNotBlank()
        ) {
            Icon(Icons.Default.QrCode, null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text("Generate QR Code")
        }

        if (bitmapPath != null) {
            val bitmap = remember(bitmapPath) {
                android.graphics.BitmapFactory.decodeFile(bitmapPath)
            }
            bitmap?.let {
                Image(
                    bitmap = it.asImageBitmap(),
                    contentDescription = "Generated QR",
                    modifier = Modifier.size(256.dp)
                )
                OutlinedButton(onClick = onSave, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Save, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Save QR Image")
                }
            }
        }
    }
}

// ─── PDF Search Tab ───────────────────────────────────────────────────────────

@Composable
private fun PdfSearchTab(
    searchPdfUri: Uri?,
    query: String,
    results: List<SearchMatch>,
    isSearching: Boolean,
    onLoadFile: (Uri) -> Unit,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit
) {
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let(onLoadFile)
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { filePicker.launch("application/pdf") },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.FileOpen, null)
                Spacer(Modifier.width(8.dp))
                Text(if (searchPdfUri != null) "PDF loaded" else "Select PDF")
            }

            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                label = { Text("Search text") },
                modifier = Modifier.fillMaxWidth(),
                trailingIcon = {
                    IconButton(onClick = onSearch, enabled = !isSearching && searchPdfUri != null) {
                        Icon(Icons.Default.Search, "Search")
                    }
                },
                singleLine = true
            )

            if (isSearching) LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        }

        if (results.isEmpty() && !isSearching && query.isNotEmpty()) {
            PdfEmptyState(message = "No results found for \"$query\"")
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(results) { match ->
                    SearchResultCard(match = match, query = query)
                }
            }
        }
    }
}

@Composable
private fun SearchResultCard(match: SearchMatch, query: String) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                "Page ${match.pageIndex + 1}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(Modifier.height(4.dp))
            // Highlight the matched portion
            val highlightedText = buildAnnotatedString {
                val before = match.snippet.substring(0, match.matchStart.coerceAtLeast(0))
                val matched = match.snippet.substring(
                    match.matchStart.coerceAtLeast(0),
                    match.matchEnd.coerceAtMost(match.snippet.length)
                )
                val after = match.snippet.substring(match.matchEnd.coerceAtMost(match.snippet.length))
                append("…$before")
                withStyle(SpanStyle(background = MaterialTheme.colorScheme.primaryContainer, fontWeight = FontWeight.Bold)) {
                    append(matched)
                }
                append("$after…")
            }
            Text(text = highlightedText, style = MaterialTheme.typography.bodySmall)
        }
    }
}
