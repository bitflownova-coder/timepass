package com.bitflow.pdfconverter.feature.editor.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.automirrored.filled.Redo
import androidx.compose.material.icons.automirrored.filled.StickyNote2
import androidx.compose.material.icons.automirrored.filled.Undo
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import android.content.Intent
import android.net.Uri
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.bitflow.pdfconverter.core.ui.components.*
import com.bitflow.pdfconverter.feature.editor.contract.*
import com.bitflow.pdfconverter.feature.editor.viewmodel.EditorViewModel
import java.util.UUID

@Composable
fun EditorScreen(
    fileUri: String,
    onNavigateBack: () -> Unit,
    viewModel: EditorViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val context = LocalContext.current

    LaunchedEffect(fileUri) {
        if (fileUri.isNotBlank()) {
            viewModel.onIntent(EditorIntent.LoadFile(fileUri))
        }
    }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collect { effect ->
            when (effect) {
                is EditorSideEffect.NavigateBack -> onNavigateBack()
                is EditorSideEffect.FileSaved -> snackbarHostState.showSnackbar("PDF saved successfully")
                is EditorSideEffect.ShowError -> snackbarHostState.showSnackbar(effect.message)
            }
        }
    }

    Scaffold(
        topBar = {
            if (!state.isReadingMode) {
                PdfTopBar(
                    title = "Editor  •  Page ${state.currentPageIndex + 1} / ${state.totalPages}",
                    onNavigateBack = onNavigateBack,
                    actions = {
                        IconButton(onClick = { viewModel.onIntent(EditorIntent.TogglePageThumbnails) }) {
                            Icon(Icons.Default.ViewModule, "Pages")
                        }
                        IconButton(onClick = { viewModel.onIntent(EditorIntent.ToggleReadingMode) }) {
                            Icon(Icons.AutoMirrored.Filled.MenuBook, "Reading Mode")
                        }
                        IconButton(onClick = { viewModel.onIntent(EditorIntent.Undo) }, enabled = state.canUndo) {
                            Icon(Icons.AutoMirrored.Filled.Undo, "Undo")
                        }
                        IconButton(onClick = { viewModel.onIntent(EditorIntent.Redo) }, enabled = state.canRedo) {
                            Icon(Icons.AutoMirrored.Filled.Redo, "Redo")
                        }
                        IconButton(onClick = { viewModel.onIntent(EditorIntent.SaveFile) }) {
                            Icon(Icons.Default.Save, "Save")
                        }
                        IconButton(onClick = {
                            val uri: Uri? = if (fileUri.startsWith("content://")) {
                                Uri.parse(fileUri)
                            } else {
                                val file = java.io.File(fileUri)
                                if (file.exists()) {
                                    runCatching {
                                        FileProvider.getUriForFile(
                                            context, "${context.packageName}.provider", file
                                        )
                                    }.getOrNull()
                                } else null
                            }
                            if (uri != null) {
                                val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                    type = "application/pdf"
                                    putExtra(Intent.EXTRA_STREAM, uri)
                                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                }
                                context.startActivity(Intent.createChooser(shareIntent, "Share PDF"))
                            }
                        }) {
                            Icon(Icons.Default.Share, "Share")
                        }
                    }
                )
            }
        },
        bottomBar = {
            if (!state.isReadingMode) {
                Column {
                    // Page thumbnail strip
                    if (state.showPageThumbnails && state.pages.isNotEmpty()) {
                        PageThumbnailStrip(
                            pages = state.pages,
                            currentIndex = state.currentPageIndex,
                            onPageSelected = { viewModel.onIntent(EditorIntent.NavigateToPage(it)) }
                        )
                    }
                    EditorToolbar(
                        activeTool = state.activeTool,
                        onToolSelected = { viewModel.onIntent(EditorIntent.ToolSelected(it)) }
                    )
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        when {
            state.isLoading  -> PdfLoadingOverlay("Loading PDF…")
            state.isSaving   -> PdfLoadingOverlay("Saving…")
            state.errorMessage != null -> PdfErrorState(
                message = state.errorMessage!!,
                onRetry = { viewModel.onIntent(EditorIntent.LoadFile(fileUri)) }
            )
            state.pages.isNotEmpty() -> {
                val page = state.pages.getOrNull(state.currentPageIndex)
                val modifier = if (state.isReadingMode) Modifier.fillMaxSize() else Modifier.fillMaxSize().padding(padding)
                Box(modifier = modifier) {
                    // Page bitmap
                    AsyncImage(
                        model = page?.bitmap,
                        contentDescription = "PDF page",
                        contentScale = ContentScale.Fit,
                        modifier = Modifier.fillMaxSize()
                    )
                    // Annotation overlay (hidden in reading mode)
                    if (!state.isReadingMode) {
                        AnnotationOverlay(
                            annotations = page?.annotations ?: emptyList(),
                            activeTool  = state.activeTool,
                            activeColor = state.activeColor,
                            onAnnotationAdded = { viewModel.onIntent(EditorIntent.AddAnnotation(it)) },
                            onAnnotationRemoved = { viewModel.onIntent(EditorIntent.RemoveAnnotation(it)) },
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                    // Reading mode overlay: tap to exit, swipe navigation via buttons
                    if (state.isReadingMode) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .pointerInput(Unit) {
                                    detectTapGestures { viewModel.onIntent(EditorIntent.ToggleReadingMode) }
                                }
                        )
                        // Page nav buttons visible in reading mode
                        Row(
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .padding(bottom = 24.dp),
                            horizontalArrangement = Arrangement.spacedBy(32.dp)
                        ) {
                            FilledTonalIconButton(
                                onClick = { viewModel.onIntent(EditorIntent.NavigateToPage((state.currentPageIndex - 1).coerceAtLeast(0))) },
                                enabled = state.currentPageIndex > 0
                            ) { Icon(Icons.Default.ChevronLeft, "Prev") }
                            Surface(
                                tonalElevation = 4.dp,
                                shape = RoundedCornerShape(16.dp)
                            ) {
                                Text(
                                    "${state.currentPageIndex + 1} / ${state.totalPages}",
                                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                                    style = MaterialTheme.typography.labelLarge
                                )
                            }
                            FilledTonalIconButton(
                                onClick = { viewModel.onIntent(EditorIntent.NavigateToPage((state.currentPageIndex + 1).coerceAtMost(state.totalPages - 1))) },
                                enabled = state.currentPageIndex < state.totalPages - 1
                            ) { Icon(Icons.Default.ChevronRight, "Next") }
                        }
                    } else {
                        // Normal mode page navigation
                        Row(
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .padding(bottom = 16.dp),
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            IconButton(
                                onClick = { viewModel.onIntent(EditorIntent.NavigateToPage((state.currentPageIndex - 1).coerceAtLeast(0))) },
                                enabled = state.currentPageIndex > 0
                            ) { Icon(Icons.Default.ChevronLeft, "Prev", tint = Color.White) }

                            Text(
                                "${state.currentPageIndex + 1} / ${state.totalPages}",
                                color = Color.White,
                                modifier = Modifier.background(Color.Black.copy(alpha = 0.5f)).padding(horizontal = 12.dp, vertical = 4.dp)
                            )

                            IconButton(
                                onClick = { viewModel.onIntent(EditorIntent.NavigateToPage((state.currentPageIndex + 1).coerceAtMost(state.totalPages - 1))) },
                                enabled = state.currentPageIndex < state.totalPages - 1
                            ) { Icon(Icons.Default.ChevronRight, "Next", tint = Color.White) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun EditorToolbar(activeTool: EditorTool, onToolSelected: (EditorTool) -> Unit) {    Surface(tonalElevation = 4.dp) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            ToolButton(Icons.Default.Highlight, "Highlight", activeTool == EditorTool.HIGHLIGHT) {
                onToolSelected(if (activeTool == EditorTool.HIGHLIGHT) EditorTool.NONE else EditorTool.HIGHLIGHT)
            }
            ToolButton(Icons.Default.Draw, "Draw", activeTool == EditorTool.FREEHAND) {
                onToolSelected(if (activeTool == EditorTool.FREEHAND) EditorTool.NONE else EditorTool.FREEHAND)
            }
            ToolButton(Icons.Default.AutoFixNormal, "Eraser", activeTool == EditorTool.ERASER) {
                onToolSelected(if (activeTool == EditorTool.ERASER) EditorTool.NONE else EditorTool.ERASER)
            }
            ToolButton(Icons.AutoMirrored.Filled.StickyNote2, "Note", activeTool == EditorTool.STICKY_NOTE) {
                onToolSelected(if (activeTool == EditorTool.STICKY_NOTE) EditorTool.NONE else EditorTool.STICKY_NOTE)
            }
            ToolButton(Icons.Default.TextFields, "Text", activeTool == EditorTool.TEXT_BOX) {
                onToolSelected(if (activeTool == EditorTool.TEXT_BOX) EditorTool.NONE else EditorTool.TEXT_BOX)
            }
        }
    }
}

@Composable
private fun ToolButton(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, active: Boolean, onClick: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        IconButton(
            onClick = onClick,
            modifier = Modifier.background(
                if (active) MaterialTheme.colorScheme.primaryContainer else Color.Transparent,
                shape = MaterialTheme.shapes.small
            )
        ) { Icon(icon, contentDescription = label) }
        Text(label, style = MaterialTheme.typography.labelSmall)
    }
}

@Composable
private fun PageThumbnailStrip(
    pages: List<PdfPageState>,
    currentIndex: Int,
    onPageSelected: (Int) -> Unit
) {
    Surface(tonalElevation = 8.dp) {
        LazyRow(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            itemsIndexed(pages) { index, page ->
                val isSelected = index == currentIndex
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(
                            if (isSelected) MaterialTheme.colorScheme.primaryContainer
                            else Color.Transparent
                        )
                        .padding(4.dp)
                ) {
                    AsyncImage(
                        model = page.bitmap,
                        contentDescription = "Page ${index + 1}",
                        contentScale = ContentScale.Fit,
                        modifier = Modifier
                            .size(width = 44.dp, height = 60.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(Color.White)
                            .pointerInput(Unit) {
                                detectTapGestures { onPageSelected(index) }
                            }
                    )
                    Text(
                        "${index + 1}",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun AnnotationOverlay(
    annotations: List<PdfAnnotation>,
    activeTool: EditorTool,
    activeColor: Color,
    onAnnotationAdded: (PdfAnnotation) -> Unit,
    onAnnotationRemoved: (String) -> Unit = {},
    modifier: Modifier = Modifier
) {
    var currentPath by remember { mutableStateOf<List<Offset>>(emptyList()) }
    var highlightStart by remember { mutableStateOf<Offset?>(null) }
    var highlightCurrent by remember { mutableStateOf<Offset?>(null) }
    var eraseStart by remember { mutableStateOf<Offset?>(null) }
    var eraseCurrent by remember { mutableStateOf<Offset?>(null) }

    // Dialogs for text-input tools
    var stickyNotePendingOffset by remember { mutableStateOf<Offset?>(null) }
    var textBoxPendingOffset by remember { mutableStateOf<Offset?>(null) }
    var inputText by remember { mutableStateOf("") }

    stickyNotePendingOffset?.let { offset ->
        AlertDialog(
            onDismissRequest = { stickyNotePendingOffset = null; inputText = "" },
            title = { Text("Add Note") },
            text = {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    label = { Text("Note text") },
                    singleLine = false,
                    maxLines = 5
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    if (inputText.isNotBlank()) {
                        onAnnotationAdded(PdfAnnotation.StickyNote(
                            id = UUID.randomUUID().toString(),
                            position = android.graphics.PointF(offset.x, offset.y),
                            text = inputText.trim()
                        ))
                    }
                    stickyNotePendingOffset = null
                    inputText = ""
                }) { Text("Add") }
            },
            dismissButton = {
                TextButton(onClick = { stickyNotePendingOffset = null; inputText = "" }) { Text("Cancel") }
            }
        )
    }

    textBoxPendingOffset?.let { offset ->
        AlertDialog(
            onDismissRequest = { textBoxPendingOffset = null; inputText = "" },
            title = { Text("Add Text") },
            text = {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    label = { Text("Text") },
                    singleLine = false,
                    maxLines = 5
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    if (inputText.isNotBlank()) {
                        onAnnotationAdded(PdfAnnotation.TextBox(
                            id = UUID.randomUUID().toString(),
                            position = android.graphics.PointF(offset.x, offset.y),
                            text = inputText.trim(),
                            color = activeColor
                        ))
                    }
                    textBoxPendingOffset = null
                    inputText = ""
                }) { Text("Add") }
            },
            dismissButton = {
                TextButton(onClick = { textBoxPendingOffset = null; inputText = "" }) { Text("Cancel") }
            }
        )
    }

    Box(modifier = modifier) {
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(activeTool) {
                    when (activeTool) {
                        EditorTool.FREEHAND -> detectDragGestures(
                            onDragStart = { currentPath = listOf(it) },
                            onDrag = { change, _ -> currentPath = currentPath + change.position },
                            onDragEnd = {
                                if (currentPath.size > 2) {
                                    onAnnotationAdded(PdfAnnotation.FreehandPath(
                                        id = UUID.randomUUID().toString(),
                                        points = currentPath.map { android.graphics.PointF(it.x, it.y) },
                                        color = activeColor,
                                        strokeWidth = 4f
                                    ))
                                }
                                currentPath = emptyList()
                            }
                        )
                        EditorTool.ERASER -> detectDragGestures(
                            onDragStart = { pos ->
                                eraseStart = pos
                                eraseCurrent = pos
                                // Also remove any annotation overlapping this point
                                annotations.forEach { ann ->
                                    val hit = when (ann) {
                                        is PdfAnnotation.FreehandPath -> ann.points.any { p ->
                                            kotlin.math.sqrt(((p.x - pos.x) * (p.x - pos.x) + (p.y - pos.y) * (p.y - pos.y)).toDouble()) < 40.0
                                        }
                                        is PdfAnnotation.Highlight -> ann.rects.any { r -> r.contains(pos.x, pos.y) }
                                        is PdfAnnotation.StickyNote -> {
                                            val x = ann.position.x; val y = ann.position.y
                                            pos.x in x..(x + 140f) && pos.y in y..(y + 60f)
                                        }
                                        is PdfAnnotation.TextBox -> {
                                            val x = ann.position.x; val y = ann.position.y
                                            pos.x in x..(x + 180f) && pos.y in y..(y + 60f)
                                        }
                                        is PdfAnnotation.EraseBox -> ann.rect.contains(pos.x, pos.y)
                                    }
                                    if (hit) onAnnotationRemoved(ann.id)
                                }
                            },
                            onDrag = { change, _ ->
                                val pos = change.position
                                eraseCurrent = pos
                                annotations.forEach { ann ->
                                    val hit = when (ann) {
                                        is PdfAnnotation.FreehandPath -> ann.points.any { p ->
                                            kotlin.math.sqrt(((p.x - pos.x) * (p.x - pos.x) + (p.y - pos.y) * (p.y - pos.y)).toDouble()) < 40.0
                                        }
                                        is PdfAnnotation.Highlight -> ann.rects.any { r -> r.contains(pos.x, pos.y) }
                                        is PdfAnnotation.StickyNote -> {
                                            val x = ann.position.x; val y = ann.position.y
                                            pos.x in x..(x + 140f) && pos.y in y..(y + 60f)
                                        }
                                        is PdfAnnotation.TextBox -> {
                                            val x = ann.position.x; val y = ann.position.y
                                            pos.x in x..(x + 180f) && pos.y in y..(y + 60f)
                                        }
                                        is PdfAnnotation.EraseBox -> ann.rect.contains(pos.x, pos.y)
                                    }
                                    if (hit) onAnnotationRemoved(ann.id)
                                }
                            },
                            onDragEnd = {
                                val start = eraseStart
                                val end = eraseCurrent
                                if (start != null && end != null) {
                                    val w = kotlin.math.abs(end.x - start.x)
                                    val h = kotlin.math.abs(end.y - start.y)
                                    if (w > 8f || h > 8f) {
                                        onAnnotationAdded(PdfAnnotation.EraseBox(
                                            id = UUID.randomUUID().toString(),
                                            rect = android.graphics.RectF(
                                                minOf(start.x, end.x), minOf(start.y, end.y),
                                                maxOf(start.x, end.x), maxOf(start.y, end.y)
                                            )
                                        ))
                                    }
                                }
                                eraseStart = null
                                eraseCurrent = null
                            }
                        )
                        EditorTool.HIGHLIGHT -> detectDragGestures(
                            onDragStart = { pos ->
                                highlightStart = pos
                                highlightCurrent = pos
                            },
                            onDrag = { change, _ -> highlightCurrent = change.position },
                            onDragEnd = {
                                val start = highlightStart
                                val end = highlightCurrent
                                if (start != null && end != null) {
                                    val rect = android.graphics.RectF(
                                        minOf(start.x, end.x), minOf(start.y, end.y),
                                        maxOf(start.x, end.x), maxOf(start.y, end.y)
                                    )
                                    if (rect.width() > 4f && rect.height() > 4f) {
                                        onAnnotationAdded(PdfAnnotation.Highlight(
                                            id = UUID.randomUUID().toString(),
                                            rects = listOf(rect),
                                            color = activeColor
                                        ))
                                    }
                                }
                                highlightStart = null
                                highlightCurrent = null
                            }
                        )
                        EditorTool.STICKY_NOTE -> detectTapGestures { offset ->
                            stickyNotePendingOffset = offset
                        }
                        EditorTool.TEXT_BOX -> detectTapGestures { offset ->
                            textBoxPendingOffset = offset
                        }
                        else -> Unit
                    }
                }
        ) {
            // Draw erase boxes (white fill — covers underlying text/images)
            annotations.filterIsInstance<PdfAnnotation.EraseBox>().forEach { ann ->
                drawRect(
                    color = Color.White,
                    topLeft = Offset(ann.rect.left, ann.rect.top),
                    size = Size(ann.rect.width(), ann.rect.height())
                )
            }

            // Draw in-progress erase selection
            val es = eraseStart
            val ec = eraseCurrent
            if (activeTool == EditorTool.ERASER && es != null && ec != null) {
                val minX = minOf(es.x, ec.x)
                val minY = minOf(es.y, ec.y)
                val w = kotlin.math.abs(ec.x - es.x)
                val h = kotlin.math.abs(ec.y - es.y)
                if (w > 4f || h > 4f) {
                    drawRect(color = Color.White, topLeft = Offset(minX, minY), size = Size(w, h))
                    drawRect(
                        color = Color.Gray.copy(alpha = 0.6f),
                        topLeft = Offset(minX, minY),
                        size = Size(w, h),
                        style = Stroke(width = 2f)
                    )
                }
            }

            // Draw existing freehand paths
            annotations.filterIsInstance<PdfAnnotation.FreehandPath>().forEach { ann ->
                if (ann.points.size > 1) {
                    val path = Path().apply {
                        moveTo(ann.points.first().x, ann.points.first().y)
                        ann.points.drop(1).forEach { lineTo(it.x, it.y) }
                    }
                    drawPath(path, ann.color, style = Stroke(width = ann.strokeWidth))
                }
            }

            // Draw in-progress freehand path
            if (activeTool == EditorTool.FREEHAND && currentPath.size > 1) {
                val path = Path().apply {
                    moveTo(currentPath.first().x, currentPath.first().y)
                    currentPath.drop(1).forEach { lineTo(it.x, it.y) }
                }
                drawPath(path, activeColor, style = Stroke(width = 4f))
            }

            // Draw highlights
            annotations.filterIsInstance<PdfAnnotation.Highlight>().forEach { ann ->
                ann.rects.forEach { rect ->
                    drawRect(
                        color = ann.color.copy(alpha = 0.4f),
                        topLeft = Offset(rect.left, rect.top),
                        size = Size(rect.width(), rect.height())
                    )
                }
            }

            // Draw in-progress highlight
            val hs = highlightStart
            val hc = highlightCurrent
            if (activeTool == EditorTool.HIGHLIGHT && hs != null && hc != null) {
                drawRect(
                    color = activeColor.copy(alpha = 0.3f),
                    topLeft = Offset(minOf(hs.x, hc.x), minOf(hs.y, hc.y)),
                    size = Size(kotlin.math.abs(hc.x - hs.x), kotlin.math.abs(hc.y - hs.y))
                )
            }

            // Draw sticky notes (yellow pin icon + text box)
            annotations.filterIsInstance<PdfAnnotation.StickyNote>().forEach { ann ->
                val x = ann.position.x
                val y = ann.position.y
                drawRect(
                    color = Color(0xFFFFF176).copy(alpha = 0.9f),
                    topLeft = Offset(x, y),
                    size = Size(140f, 60f)
                )
                drawRect(
                    color = Color(0xFFF9A825),
                    topLeft = Offset(x, y),
                    size = Size(140f, 60f),
                    style = Stroke(width = 2f)
                )
                drawContext.canvas.nativeCanvas.drawText(
                    ann.text.take(25),
                    x + 6f,
                    y + 22f,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.BLACK
                        textSize = 14f * density
                    }
                )
            }

            // Draw text boxes
            annotations.filterIsInstance<PdfAnnotation.TextBox>().forEach { ann ->
                val x = ann.position.x
                val y = ann.position.y
                drawRect(
                    color = Color.White.copy(alpha = 0.85f),
                    topLeft = Offset(x, y),
                    size = Size(160f, 50f)
                )
                drawRect(
                    color = ann.color,
                    topLeft = Offset(x, y),
                    size = Size(160f, 50f),
                    style = Stroke(width = 2f)
                )
                drawContext.canvas.nativeCanvas.drawText(
                    ann.text.take(28),
                    x + 6f,
                    y + 20f,
                    android.graphics.Paint().apply {
                        color = ann.color.toArgb()
                        textSize = 13f * density
                    }
                )
            }
        }
    }
}
