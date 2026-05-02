package com.bitflow.pdfconverter.feature.storage.contract

import android.net.Uri
import com.bitflow.pdfconverter.core.common.mvi.MviIntent
import com.bitflow.pdfconverter.core.common.mvi.MviSideEffect
import com.bitflow.pdfconverter.core.common.mvi.MviState
import com.bitflow.pdfconverter.core.domain.model.Folder
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.domain.model.RecentFile

data class StorageState(
    val currentFolderId: Long? = null,
    val currentFolderName: String = "All Files",
    val documents: List<PdfDocument> = emptyList(),
    val recentFiles: List<RecentFile> = emptyList(),
    val folders: List<Folder> = emptyList(),
    val isLoading: Boolean = false,
    val searchQuery: String = "",
    val viewMode: ViewMode = ViewMode.GRID,
    val sortOrder: SortOrder = SortOrder.MODIFIED_DESC,
    val selectedDocumentIds: Set<Long> = emptySet(),
    val isSelectionMode: Boolean = false,
    val errorMessage: String? = null
) : MviState

enum class ViewMode { GRID, LIST }

enum class SortOrder {
    NAME_ASC, NAME_DESC,
    SIZE_ASC, SIZE_DESC,
    MODIFIED_DESC, MODIFIED_ASC
}

sealed interface StorageIntent : MviIntent {
    data class NavigateToFolder(val folderId: Long?, val folderName: String) : StorageIntent
    data class SearchQueryChanged(val query: String) : StorageIntent
    data class ViewModeChanged(val mode: ViewMode) : StorageIntent
    data class SortOrderChanged(val order: SortOrder) : StorageIntent
    // Document ops
    data class OpenDocument(val document: PdfDocument) : StorageIntent
    data class DeleteDocument(val documentId: Long) : StorageIntent
    data class RenameDocument(val documentId: Long, val newName: String) : StorageIntent
    data class MoveDocument(val documentId: Long, val targetFolderId: Long?) : StorageIntent
    data class ShareDocument(val document: PdfDocument) : StorageIntent
    data class ImportFile(val uri: Uri) : StorageIntent
    // Selection
    data class ToggleSelection(val documentId: Long) : StorageIntent
    data object SelectAll : StorageIntent
    data object ClearSelection : StorageIntent
    data object DeleteSelected : StorageIntent
    // Folders
    data class CreateFolder(val name: String, val parentId: Long?) : StorageIntent
    data class DeleteFolder(val folderId: Long) : StorageIntent
    data class RenameFolder(val folderId: Long, val newName: String) : StorageIntent
    data object DismissError : StorageIntent
}

sealed interface StorageSideEffect : MviSideEffect {
    data class OpenPdf(val filePath: String) : StorageSideEffect
    data class SharePdf(val uri: Uri) : StorageSideEffect
    data class ShowError(val message: String) : StorageSideEffect
    data class ShowMessage(val message: String) : StorageSideEffect
}

