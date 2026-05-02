package com.bitflow.pdfconverter.feature.scanner.ui

import android.graphics.PointF
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.scanner.contract.ImageFilter
import com.bitflow.pdfconverter.feature.scanner.contract.ScannerIntent
import com.bitflow.pdfconverter.feature.scanner.viewmodel.ScannerViewModel

@Composable
fun CropScreen(
    onNavigateBack: () -> Unit,
    onScanComplete: () -> Unit = {},
    onExportClick: (() -> Unit)? = null,
    viewModel: ScannerViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val page = state.pages.lastOrNull() ?: run { onNavigateBack(); return }

    // Local mutable corners for drag interaction
    var corners by remember(page.id) {
        mutableStateOf(page.cropCorners.map { PointF(it.x, it.y) })
    }

    Scaffold(
        topBar = {
            PdfTopBar(title = "Adjust Crop", onNavigateBack = onNavigateBack)
        },
        bottomBar = {
            CropBottomBar(
                currentFilter = page.appliedFilter,
                onFilterSelected = { filter ->
                    viewModel.onIntent(ScannerIntent.ApplyFilterToPage(page.id, filter))
                },
                onApply = {
                    viewModel.onIntent(ScannerIntent.CornersAdjusted(page.id, corners))
                    viewModel.onIntent(ScannerIntent.ApplyCrop(page.id))
                },
                onAddPage = onNavigateBack,
                onExport = onExportClick ?: {
                    viewModel.onIntent(ScannerIntent.ExportToPdf("Scan_${System.currentTimeMillis()}"))
                }
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Page preview image
            AsyncImage(
                model = page.processedBitmap,
                contentDescription = "Scanned page preview",
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize()
            )

            // Crop overlay with draggable corners
            CropOverlay(
                corners = corners,
                onCornerMoved = { index, newPos -> corners = corners.toMutableList().also { it[index] = newPos } },
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}

@Composable
private fun CropOverlay(
    corners: List<PointF>,
    onCornerMoved: (Int, PointF) -> Unit,
    modifier: Modifier = Modifier
) {
    val handleRadius = 20.dp
    val handleRadiusPx = with(androidx.compose.ui.platform.LocalDensity.current) { handleRadius.toPx() }

    Box(modifier = modifier) {
        // Draw lines between corners
        Canvas(modifier = Modifier.fillMaxSize()) {
            if (corners.size == 4) {
                val path = Path().apply {
                    moveTo(corners[0].x, corners[0].y)
                    lineTo(corners[1].x, corners[1].y)
                    lineTo(corners[2].x, corners[2].y)
                    lineTo(corners[3].x, corners[3].y)
                    close()
                }
                drawPath(path, Color.White.copy(alpha = 0.4f), style = Stroke(width = 2.dp.toPx()))
                drawPath(path, Color(0xFF2196F3), style = Stroke(width = 2.dp.toPx()))
            }
        }

        // Draggable handle for each corner
        corners.forEachIndexed { index, corner ->
            Box(
                modifier = Modifier
                    .offset(
                        x = with(androidx.compose.ui.platform.LocalDensity.current) { corner.x.toDp() } - handleRadius,
                        y = with(androidx.compose.ui.platform.LocalDensity.current) { corner.y.toDp() } - handleRadius
                    )
                    .size(handleRadius * 2)
                    .pointerInput(index) {
                        detectDragGestures { change, dragAmount ->
                            change.consume()
                            onCornerMoved(index, PointF(
                                corner.x + dragAmount.x,
                                corner.y + dragAmount.y
                            ))
                        }
                    }
            ) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    drawCircle(Color.White, radius = handleRadiusPx)
                    drawCircle(Color(0xFF1565C0), radius = handleRadiusPx, style = Stroke(width = 3.dp.toPx()))
                }
            }
        }
    }
}

@Composable
private fun CropBottomBar(
    currentFilter: ImageFilter,
    onFilterSelected: (ImageFilter) -> Unit,
    onApply: () -> Unit,
    onAddPage: () -> Unit,
    onExport: () -> Unit
) {
    Surface(tonalElevation = 8.dp) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            // Filter chips
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ImageFilter.entries.forEach { filter ->
                    FilterChip(
                        selected = filter == currentFilter,
                        onClick = { onFilterSelected(filter) },
                        label = { Text(filter.name.replace('_', ' ')) }
                    )
                }
            }
            // Action buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(onClick = onAddPage, modifier = Modifier.weight(1f)) { Text("+ Add Page") }
                Button(onClick = onApply, modifier = Modifier.weight(1f)) { Text("Apply Crop") }
                Button(onClick = onExport, modifier = Modifier.weight(1f)) { Text("Save PDF") }
            }
        }
    }
}
