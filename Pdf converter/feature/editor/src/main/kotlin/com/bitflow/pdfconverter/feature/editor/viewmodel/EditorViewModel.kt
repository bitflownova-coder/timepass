package com.bitflow.pdfconverter.feature.editor.viewmodel

import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.net.Uri
import androidx.compose.ui.graphics.toArgb
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.runCatchingPdf
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.feature.editor.contract.*
import com.bitflow.pdfconverter.feature.editor.engine.PdfPageRenderer
import com.bitflow.pdfconverter.feature.editor.engine.UndoRedoStack
import com.bitflow.pdfconverter.feature.editor.engine.Command
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.FileOutputStream
import javax.inject.Inject

@HiltViewModel
class EditorViewModel @Inject constructor(
    private val pageRenderer: PdfPageRenderer,
    private val fileManager: FileManager,
    private val repository: PdfDocumentRepository
) : MviViewModel<EditorState, EditorIntent, EditorSideEffect>(EditorState()) {

    private val undoRedo = UndoRedoStack()

    override suspend fun handleIntent(intent: EditorIntent) {
        when (intent) {
            is EditorIntent.LoadFile        -> loadFile(intent.fileUri)
            is EditorIntent.NavigateToPage  -> updateState { copy(currentPageIndex = intent.pageIndex) }
            is EditorIntent.ToolSelected    -> updateState { copy(activeTool = intent.tool) }
            is EditorIntent.ColorSelected   -> updateState { copy(activeColor = intent.color) }
            is EditorIntent.AddAnnotation   -> addAnnotation(intent.annotation)
            is EditorIntent.RemoveAnnotation -> removeAnnotation(intent.annotationId)
            is EditorIntent.DeletePage      -> deletePage(intent.pageIndex)
            is EditorIntent.RotatePage      -> rotatePage(intent.pageIndex, intent.degrees)
            is EditorIntent.ReorderPage     -> reorderPage(intent.from, intent.to)
            EditorIntent.Undo               -> { undoRedo.undo(); syncUndoState() }
            EditorIntent.Redo               -> { undoRedo.redo(); syncUndoState() }
            EditorIntent.SaveFile           -> saveFile()
            EditorIntent.ToggleReadingMode  -> updateState { copy(isReadingMode = !isReadingMode, activeTool = EditorTool.NONE) }
            EditorIntent.TogglePageThumbnails -> updateState { copy(showPageThumbnails = !showPageThumbnails) }
            EditorIntent.DismissError       -> updateState { copy(errorMessage = null) }
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private suspend fun loadFile(uriString: String) {
        if (uriString.isBlank()) return
        updateState { copy(isLoading = true, fileUri = uriString) }

        val result = withContext(Dispatchers.IO) {
            runCatchingPdf {
                val uri = Uri.parse(uriString)
                val (bitmaps, _) = pageRenderer.renderAllPages(uri)
                bitmaps.mapIndexed { i, bmp -> PdfPageState(pageIndex = i, bitmap = bmp) }
            }
        }

        result
            .onSuccess { pages ->
                updateState { copy(pages = pages, totalPages = pages.size, isLoading = false) }
            }
            .onError { msg, _ ->
                updateState { copy(isLoading = false, errorMessage = msg) }
            }
    }

    private fun addAnnotation(annotation: PdfAnnotation) {
        val pageIndex = currentState.currentPageIndex
        val oldPages  = currentState.pages
        val command   = object : Command {
            override fun execute() {
                updateState {
                    copy(pages = pages.mapIndexed { i, p ->
                        if (i == pageIndex) p.copy(annotations = p.annotations + annotation) else p
                    })
                }
            }
            override fun undo() {
                updateState { copy(pages = oldPages) }
            }
        }
        undoRedo.execute(command)
        syncUndoState()
    }

    private fun removeAnnotation(annotationId: String) {
        val pageIndex  = currentState.currentPageIndex
        val oldPages   = currentState.pages
        val command    = object : Command {
            override fun execute() {
                updateState {
                    copy(pages = pages.mapIndexed { i, p ->
                        if (i == pageIndex) p.copy(annotations = p.annotations.filterNot { it.id == annotationId }) else p
                    })
                }
            }
            override fun undo() { updateState { copy(pages = oldPages) } }
        }
        undoRedo.execute(command)
        syncUndoState()
    }

    private fun deletePage(pageIndex: Int) {
        val oldPages = currentState.pages
        val command  = object : Command {
            override fun execute() {
                updateState {
                    val newPages = pages.filterIndexed { i, _ -> i != pageIndex }
                    copy(pages = newPages, totalPages = newPages.size,
                        currentPageIndex = currentPageIndex.coerceAtMost((newPages.size - 1).coerceAtLeast(0)))
                }
            }
            override fun undo() { updateState { copy(pages = oldPages, totalPages = oldPages.size) } }
        }
        undoRedo.execute(command)
        syncUndoState()
    }

    private fun rotatePage(pageIndex: Int, degrees: Int) {
        val oldPages = currentState.pages
        val page     = oldPages.getOrNull(pageIndex) ?: return
        val bmp      = page.bitmap ?: return
        val matrix   = android.graphics.Matrix().apply { postRotate(degrees.toFloat()) }
        val rotated  = android.graphics.Bitmap.createBitmap(bmp, 0, 0, bmp.width, bmp.height, matrix, true)
        val command  = object : Command {
            override fun execute() {
                updateState {
                    copy(pages = pages.mapIndexed { i, p ->
                        if (i == pageIndex) p.copy(bitmap = rotated) else p
                    })
                }
            }
            override fun undo() { updateState { copy(pages = oldPages) } }
        }
        undoRedo.execute(command)
        syncUndoState()
    }

    private fun reorderPage(from: Int, to: Int) {
        val oldPages = currentState.pages
        val command  = object : Command {
            override fun execute() {
                val newPages = oldPages.toMutableList()
                val item = newPages.removeAt(from)
                newPages.add(to, item)
                updateState { copy(pages = newPages.mapIndexed { i, p -> p.copy(pageIndex = i) }) }
            }
            override fun undo() { updateState { copy(pages = oldPages) } }
        }
        undoRedo.execute(command)
        syncUndoState()
    }

    private suspend fun saveFile() {
        updateState { copy(isSaving = true) }
        val pages = currentState.pages

        val result = withContext(Dispatchers.IO) {
            runCatchingPdf {
                val doc = android.graphics.pdf.PdfDocument()
                pages.forEachIndexed { i, page ->
                    val srcBitmap = page.bitmap ?: return@forEachIndexed
                    // Create a mutable copy to draw annotations on
                    val mutable = srcBitmap.copy(android.graphics.Bitmap.Config.ARGB_8888, true)
                    val canvas = Canvas(mutable)

                    page.annotations.forEach { ann ->
                        when (ann) {
                            is PdfAnnotation.FreehandPath -> {
                                if (ann.points.size > 1) {
                                    val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                        color = ann.color.toArgb()
                                        strokeWidth = ann.strokeWidth
                                        style = Paint.Style.STROKE
                                        strokeCap = Paint.Cap.ROUND
                                        strokeJoin = Paint.Join.ROUND
                                    }
                                    val path = Path().apply {
                                        moveTo(ann.points.first().x, ann.points.first().y)
                                        ann.points.drop(1).forEach { lineTo(it.x, it.y) }
                                    }
                                    canvas.drawPath(path, paint)
                                }
                            }
                            is PdfAnnotation.Highlight -> {
                                val paint = Paint().apply {
                                    color = ann.color.copy(alpha = 0.4f).toArgb()
                                    style = Paint.Style.FILL
                                }
                                ann.rects.forEach { canvas.drawRect(it, paint) }
                            }
                            is PdfAnnotation.StickyNote -> {
                                val bgPaint = Paint().apply {
                                    color = android.graphics.Color.argb(230, 255, 241, 118)
                                    style = Paint.Style.FILL
                                }
                                val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                    color = android.graphics.Color.argb(255, 249, 168, 37)
                                    style = Paint.Style.STROKE
                                    strokeWidth = 2f
                                }
                                val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                    color = android.graphics.Color.BLACK
                                    textSize = 14f
                                }
                                val rect = android.graphics.RectF(
                                    ann.position.x, ann.position.y,
                                    ann.position.x + 140f, ann.position.y + 60f
                                )
                                canvas.drawRect(rect, bgPaint)
                                canvas.drawRect(rect, borderPaint)
                                canvas.drawText(ann.text.take(25), ann.position.x + 6f, ann.position.y + 22f, textPaint)
                            }
                            is PdfAnnotation.TextBox -> {
                                val bgPaint = Paint().apply {
                                    color = android.graphics.Color.argb(216, 255, 255, 255)
                                    style = Paint.Style.FILL
                                }
                                val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                    color = ann.color.toArgb()
                                    style = Paint.Style.STROKE
                                    strokeWidth = 2f
                                }
                                val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                                    color = ann.color.toArgb()
                                    textSize = 13f
                                }
                                val rect = android.graphics.RectF(
                                    ann.position.x, ann.position.y,
                                    ann.position.x + 160f, ann.position.y + 50f
                                )
                                canvas.drawRect(rect, bgPaint)
                                canvas.drawRect(rect, borderPaint)
                                canvas.drawText(ann.text.take(28), ann.position.x + 6f, ann.position.y + 20f, textPaint)
                            }
                            is PdfAnnotation.EraseBox -> {
                                val paint = Paint().apply {
                                    color = android.graphics.Color.WHITE
                                    style = Paint.Style.FILL
                                }
                                canvas.drawRect(ann.rect, paint)
                            }
                        }
                    }

                    val pageInfo = android.graphics.pdf.PdfDocument.PageInfo.Builder(
                        mutable.width, mutable.height, i + 1
                    ).create()
                    val pdfPage = doc.startPage(pageInfo)
                    pdfPage.canvas.drawBitmap(mutable, 0f, 0f, null)
                    mutable.recycle()
                    doc.finishPage(pdfPage)
                }

                val outputFile = fileManager.newOutputFile("edited_${System.currentTimeMillis()}.pdf")
                FileOutputStream(outputFile).use { doc.writeTo(it) }
                doc.close()
                fileManager.publishToDownloads(outputFile, "Edit")
                outputFile.absolutePath
            }
        }

        updateState { copy(isSaving = false) }
        result
            .onSuccess { path ->
                val outFile = java.io.File(path)
                val now = System.currentTimeMillis()
                val pageCount = runCatching {
                    android.graphics.pdf.PdfRenderer(
                        android.os.ParcelFileDescriptor.open(outFile, android.os.ParcelFileDescriptor.MODE_READ_ONLY)
                    ).use { it.pageCount }
                }.getOrDefault(currentState.pages.size)
                repository.saveDocument(
                    PdfDocument(
                        name       = outFile.nameWithoutExtension,
                        filePath   = path,
                        sizeBytes  = outFile.length(),
                        pageCount  = pageCount,
                        createdAt  = now,
                        modifiedAt = now
                    )
                )
                sendEffect(EditorSideEffect.FileSaved(path))
            }
            .onError { msg, _ ->
                updateState { copy(errorMessage = msg) }
            }
    }

    private fun syncUndoState() = updateState {
        copy(canUndo = undoRedo.canUndo, canRedo = undoRedo.canRedo)
    }
}
