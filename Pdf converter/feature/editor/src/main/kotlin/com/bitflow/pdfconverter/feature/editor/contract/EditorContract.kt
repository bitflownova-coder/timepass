package com.bitflow.pdfconverter.feature.editor.contract

import android.graphics.Bitmap
import android.graphics.PointF
import androidx.compose.ui.graphics.Color
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState

// ── Data models ──────────────────────────────────────────────────────────────

data class PdfPageState(
    val pageIndex: Int,
    val bitmap: Bitmap?,
    val annotations: List<PdfAnnotation> = emptyList()
)

sealed interface PdfAnnotation {
    val id: String
    data class Highlight(override val id: String, val rects: List<android.graphics.RectF>, val color: Color) : PdfAnnotation
    data class FreehandPath(override val id: String, val points: List<PointF>, val color: Color, val strokeWidth: Float) : PdfAnnotation
    data class StickyNote(override val id: String, val position: PointF, val text: String) : PdfAnnotation
    data class TextBox(override val id: String, val position: PointF, val text: String, val color: Color) : PdfAnnotation
    /** White-fill rectangle that covers/erases underlying content (text, images) */
    data class EraseBox(override val id: String, val rect: android.graphics.RectF) : PdfAnnotation
}

enum class EditorTool { NONE, HIGHLIGHT, FREEHAND, ERASER, STICKY_NOTE, TEXT_BOX }

// ── State ────────────────────────────────────────────────────────────────────

data class EditorState(
    val fileUri: String = "",
    val pages: List<PdfPageState> = emptyList(),
    val currentPageIndex: Int = 0,
    val totalPages: Int = 0,
    val activeTool: EditorTool = EditorTool.NONE,
    val activeColor: Color = Color(0xFFFFEB3B),
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val canUndo: Boolean = false,
    val canRedo: Boolean = false,
    val isReadingMode: Boolean = false,
    val showPageThumbnails: Boolean = false,
    val errorMessage: String? = null
) : MviState

// ── Intents ──────────────────────────────────────────────────────────────────

sealed interface EditorIntent : MviIntent {
    data class LoadFile(val fileUri: String) : EditorIntent
    data class NavigateToPage(val pageIndex: Int) : EditorIntent
    data class ToolSelected(val tool: EditorTool) : EditorIntent
    data class ColorSelected(val color: Color) : EditorIntent
    data class AddAnnotation(val annotation: PdfAnnotation) : EditorIntent
    data class RemoveAnnotation(val annotationId: String) : EditorIntent
    data class DeletePage(val pageIndex: Int) : EditorIntent
    data class RotatePage(val pageIndex: Int, val degrees: Int) : EditorIntent
    data class ReorderPage(val from: Int, val to: Int) : EditorIntent
    data object Undo : EditorIntent
    data object Redo : EditorIntent
    data object SaveFile : EditorIntent
    data object ToggleReadingMode : EditorIntent
    data object TogglePageThumbnails : EditorIntent
    data object DismissError : EditorIntent
}

// ── Side Effects ─────────────────────────────────────────────────────────────

sealed interface EditorSideEffect : MviSideEffect {
    data class FileSaved(val filePath: String) : EditorSideEffect
    data class ShowError(val message: String) : EditorSideEffect
    data object NavigateBack : EditorSideEffect
}
