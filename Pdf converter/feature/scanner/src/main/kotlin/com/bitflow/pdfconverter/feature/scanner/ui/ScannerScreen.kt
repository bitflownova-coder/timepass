package com.bitflow.pdfconverter.feature.scanner.ui

import android.Manifest
import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.FlashOff
import androidx.compose.material.icons.filled.FlashOn
import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.pdfconverter.core.ui.components.PermissionRationaleCard
import com.bitflow.pdfconverter.feature.scanner.contract.ScannerIntent
import com.bitflow.pdfconverter.feature.scanner.contract.ScannerSideEffect
import com.bitflow.pdfconverter.feature.scanner.viewmodel.ScannerViewModel
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import timber.log.Timber

@OptIn(ExperimentalPermissionsApi::class, ExperimentalMaterial3Api::class)
@Composable
fun ScannerScreen(
    onNavigateToCrop: () -> Unit,
    onNavigateBack: () -> Unit,
    onPdfExported: (String) -> Unit = {},
    viewModel: ScannerViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var showExportDialog by remember { mutableStateOf(false) }
    var exportName by remember { mutableStateOf("Scan") }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is ScannerSideEffect.PdfExported    -> onPdfExported(effect.filePath)
                is ScannerSideEffect.ShowError      -> Timber.e(effect.message)
                else                                -> Unit
            }
        }
    }

    // Gallery picker — pick multiple images
    val galleryLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.GetMultipleContents()
    ) { uris ->
        if (uris.isNotEmpty()) {
            scope.launch(Dispatchers.IO) {
                val bitmaps = uris.mapNotNull { uri ->
                    runCatching {
                        context.contentResolver.openInputStream(uri)
                            ?.use { stream -> BitmapFactory.decodeStream(stream) }
                    }.getOrNull()
                }
                if (bitmaps.isNotEmpty()) {
                    viewModel.onIntent(ScannerIntent.ImportPhotosFromGallery(bitmaps))
                }
            }
        }
    }

    val cameraPermission = rememberPermissionState(Manifest.permission.CAMERA)

    if (!cameraPermission.status.isGranted) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            PermissionRationaleCard(
                message = "Camera permission is needed to scan documents.",
                onGrantClick = { cameraPermission.launchPermissionRequest() }
            )
        }
        return
    }

    var flashEnabled by remember { mutableStateOf(false) }
    var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
    var camera by remember { mutableStateOf<Camera?>(null) }
    val lifecycleOwner = LocalLifecycleOwner.current

    Box(modifier = Modifier.fillMaxSize()) {

        // CameraX Preview
        AndroidView(
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()
                    val preview = Preview.Builder().build()
                        .also { it.setSurfaceProvider(previewView.surfaceProvider) }
                    val capture = ImageCapture.Builder()
                        .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                        .build()
                    imageCapture = capture
                    val selector = CameraSelector.DEFAULT_BACK_CAMERA
                    cameraProvider.unbindAll()
                    camera = cameraProvider.bindToLifecycle(lifecycleOwner, selector, preview, capture)
                    viewModel.onIntent(ScannerIntent.CameraReady)
                }, ContextCompat.getMainExecutor(ctx))
                previewView
            },
            modifier = Modifier.fillMaxSize()
        )

        // Rule-of-thirds grid overlay
        GridOverlay(modifier = Modifier.fillMaxSize())

        // ── Top bar ──────────────────────────────────────────────────────────
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .statusBarsPadding()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onNavigateBack) {
                Icon(Icons.Default.Close, contentDescription = "Back", tint = Color.White)
            }
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = Color.Black.copy(alpha = 0.5f)
            ) {
                Text(
                    text = if (state.pages.isEmpty()) "Tap to scan" else "${state.pages.size} page(s)",
                    color = Color.White,
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                )
            }
            IconButton(onClick = {
                flashEnabled = !flashEnabled
                camera?.cameraControl?.enableTorch(flashEnabled)
            }) {
                Icon(
                    imageVector = if (flashEnabled) Icons.Default.FlashOn else Icons.Default.FlashOff,
                    contentDescription = "Flash",
                    tint = if (flashEnabled) Color.Yellow else Color.White
                )
            }
        }

        // ── Bottom section ───────────────────────────────────────────────────
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
        ) {
            // Thumbnail strip — shown when at least one page is captured
            if (state.pages.isNotEmpty()) {
                LazyRow(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(88.dp)
                        .background(Color.Black.copy(alpha = 0.75f)),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    itemsIndexed(state.pages) { index, page ->
                        Box {
                            Image(
                                bitmap = page.processedBitmap.asImageBitmap(),
                                contentDescription = "Page ${index + 1}",
                                contentScale = ContentScale.Crop,
                                modifier = Modifier
                                    .size(56.dp)
                                    .clip(RoundedCornerShape(6.dp))
                                    .border(1.5.dp, Color.White.copy(alpha = 0.6f), RoundedCornerShape(6.dp))
                            )
                            // Page number badge
                            Surface(
                                modifier = Modifier
                                    .align(Alignment.BottomStart)
                                    .padding(2.dp),
                                shape = RoundedCornerShape(4.dp),
                                color = Color.Black.copy(alpha = 0.65f)
                            ) {
                                Text(
                                    text = "${index + 1}",
                                    color = Color.White,
                                    style = MaterialTheme.typography.labelSmall,
                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                )
                            }
                            // Delete button
                            IconButton(
                                onClick = { viewModel.onIntent(ScannerIntent.DeletePage(page.id)) },
                                modifier = Modifier
                                    .size(20.dp)
                                    .align(Alignment.TopEnd)
                            ) {
                                Icon(
                                    Icons.Default.Close, null,
                                    tint = Color.White,
                                    modifier = Modifier.size(14.dp)
                                )
                            }
                        }
                    }
                }
            }

            // Controls row: [Gallery] [Capture] [Create PDF / placeholder]
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.Black.copy(alpha = 0.6f))
                    .navigationBarsPadding()
                    .padding(horizontal = 24.dp, vertical = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Gallery import button
                IconButton(
                    onClick = { galleryLauncher.launch("image/*") },
                    modifier = Modifier.size(52.dp)
                ) {
                    Icon(
                        Icons.Default.PhotoLibrary,
                        contentDescription = "Import from gallery",
                        tint = Color.White,
                        modifier = Modifier.size(30.dp)
                    )
                }

                // Capture (shutter) button
                OutlinedButton(
                    onClick = {
                        val capture = imageCapture ?: return@OutlinedButton
                        capture.takePicture(
                            ContextCompat.getMainExecutor(context),
                            object : ImageCapture.OnImageCapturedCallback() {
                                @ExperimentalGetImage
                                override fun onCaptureSuccess(proxy: ImageProxy) {
                                    val buffer = proxy.planes[0].buffer
                                    val bytes = ByteArray(buffer.remaining())
                                    buffer.get(bytes)
                                    proxy.close()
                                    val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                                    if (bitmap != null) {
                                        scope.launch {
                                            viewModel.onIntent(ScannerIntent.PhotoCaptured(bitmap))
                                        }
                                    }
                                }
                                override fun onError(e: ImageCaptureException) {
                                    Timber.e(e, "Capture failed")
                                }
                            })
                    },
                    modifier = Modifier.size(72.dp),
                    shape = CircleShape,
                    border = androidx.compose.foundation.BorderStroke(3.dp, Color.White),
                    colors = ButtonDefaults.outlinedButtonColors(containerColor = Color.White.copy(alpha = 0.15f))
                ) {}

                // Create PDF button (visible only when pages captured, else spacer)
                if (state.pages.isNotEmpty()) {
                    Button(
                        onClick = {
                            exportName = "Scan"
                            showExportDialog = true
                        },
                        modifier = Modifier.height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.PictureAsPdf, null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("Create\nPDF", style = MaterialTheme.typography.labelSmall)
                    }
                } else {
                    Spacer(Modifier.size(52.dp))
                }
            }
        }

        // Loading overlay
        if (state.isProcessing) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.4f)),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = Color.White)
            }
        }

        // Crop view overlay — shown inline after a photo is captured (same ViewModel, no scoping issues)
        if (state.showCropView) {
            CropScreen(
                onNavigateBack = { viewModel.onIntent(ScannerIntent.HideCropView) },
                onExportClick = {
                    exportName = "Scan"
                    showExportDialog = true
                },
                viewModel = viewModel
            )
        }
    }

    // Export dialog
    if (showExportDialog) {
        AlertDialog(
            onDismissRequest = { showExportDialog = false },
            title = { Text("Create PDF") },
            text = {
                OutlinedTextField(
                    value = exportName,
                    onValueChange = { exportName = it },
                    label = { Text("Document name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            },
            confirmButton = {
                Button(onClick = {
                    showExportDialog = false
                    viewModel.onIntent(ScannerIntent.ExportToPdf(exportName))
                }) { Text("Create") }
            },
            dismissButton = {
                TextButton(onClick = { showExportDialog = false }) { Text("Cancel") }
            }
        )
    }
}

@Composable
private fun GridOverlay(modifier: Modifier = Modifier) {
    androidx.compose.foundation.Canvas(modifier = modifier) {
        val strokeWidth = 1.dp.toPx()
        val color = Color.White.copy(alpha = 0.3f)
        val thirdW = size.width / 3f
        val thirdH = size.height / 3f
        drawLine(color, androidx.compose.ui.geometry.Offset(thirdW, 0f),
            androidx.compose.ui.geometry.Offset(thirdW, size.height), strokeWidth)
        drawLine(color, androidx.compose.ui.geometry.Offset(thirdW * 2, 0f),
            androidx.compose.ui.geometry.Offset(thirdW * 2, size.height), strokeWidth)
        drawLine(color, androidx.compose.ui.geometry.Offset(0f, thirdH),
            androidx.compose.ui.geometry.Offset(size.width, thirdH), strokeWidth)
        drawLine(color, androidx.compose.ui.geometry.Offset(0f, thirdH * 2),
            androidx.compose.ui.geometry.Offset(size.width, thirdH * 2), strokeWidth)
    }
}
