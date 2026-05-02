package com.bitflow.pdfconverter.feature.storage.viewmodel

import android.content.Context
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import androidx.lifecycle.viewModelScope
import com.bitflow.pdfconverter.core.common.mvi.MviViewModel
import com.bitflow.pdfconverter.core.common.result.*
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import com.bitflow.pdfconverter.core.domain.model.Folder
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.filesystem.FileManager
import com.bitflow.pdfconverter.core.filesystem.SafHelper
import com.bitflow.pdfconverter.feature.storage.contract.SortOrder
import com.bitflow.pdfconverter.feature.storage.contract.StorageIntent
import com.bitflow.pdfconverter.feature.storage.contract.StorageSideEffect
import com.bitflow.pdfconverter.feature.storage.contract.StorageState
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class StorageViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: PdfDocumentRepository,
    private val fileManager: FileManager,
    private val safHelper: SafHelper
) : MviViewModel<StorageState, StorageIntent, StorageSideEffect>(StorageState()) {

    init {
        observeDocuments()
        observeRecentFiles()
        observeFolders()
    }

    override suspend fun handleIntent(intent: StorageIntent) {
        when (intent) {
            is StorageIntent.NavigateToFolder -> {
                updateState { copy(currentFolderId = intent.folderId, currentFolderName = intent.folderName) }
                observeDocuments()
            }
            is StorageIntent.SearchQueryChanged -> updateState { copy(searchQuery = intent.query) }
            is StorageIntent.ViewModeChanged -> updateState { copy(viewMode = intent.mode) }
            is StorageIntent.SortOrderChanged -> updateState { copy(sortOrder = intent.order) }
            is StorageIntent.OpenDocument -> openDocument(intent.document)
            is StorageIntent.DeleteDocument -> deleteDocument(intent.documentId)
            is StorageIntent.RenameDocument -> renameDocument(intent.documentId, intent.newName)
            is StorageIntent.MoveDocument -> moveDocument(intent.documentId, intent.targetFolderId)
            is StorageIntent.ShareDocument -> shareDocument(intent.document)
            is StorageIntent.ImportFile -> importFile(intent.uri)
            is StorageIntent.ToggleSelection -> toggleSelection(intent.documentId)
            StorageIntent.SelectAll -> updateState { copy(selectedDocumentIds = documents.map { it.id }.toSet(), isSelectionMode = true) }
            StorageIntent.ClearSelection -> updateState { copy(selectedDocumentIds = emptySet(), isSelectionMode = false) }
            StorageIntent.DeleteSelected -> deleteSelected()
            is StorageIntent.CreateFolder -> createFolder(intent.name, intent.parentId)
            is StorageIntent.DeleteFolder -> deleteFolder(intent.folderId)
            is StorageIntent.RenameFolder -> renameFolder(intent.folderId, intent.newName)
            StorageIntent.DismissError -> updateState { copy(errorMessage = null) }
        }
    }

    private fun observeDocuments() {
        viewModelScope.launch {
            val folderId = state.value.currentFolderId
            val flow = if (folderId != null) {
                repository.getDocumentsByFolder(folderId)
            } else {
                repository.getAllDocuments()
            }
            flow.collect { docs ->
                updateState { copy(documents = sortDocuments(docs, sortOrder)) }
            }
        }
    }

    private fun observeRecentFiles() {
        viewModelScope.launch {
            repository.getRecentFiles(20).collect { recent ->
                updateState { copy(recentFiles = recent) }
            }
        }
    }

    private fun observeFolders() {
        viewModelScope.launch {
            repository.getAllFolders().collect { folders ->
                updateState { copy(folders = folders) }
            }
        }
    }

    private fun sortDocuments(docs: List<PdfDocument>, order: SortOrder): List<PdfDocument> =
        when (order) {
            SortOrder.NAME_ASC -> docs.sortedBy { it.name.lowercase() }
            SortOrder.NAME_DESC -> docs.sortedByDescending { it.name.lowercase() }
            SortOrder.SIZE_ASC -> docs.sortedBy { it.sizeBytes }
            SortOrder.SIZE_DESC -> docs.sortedByDescending { it.sizeBytes }
            SortOrder.MODIFIED_DESC -> docs.sortedByDescending { it.modifiedAt }
            SortOrder.MODIFIED_ASC -> docs.sortedBy { it.modifiedAt }
        }

    private fun openDocument(document: PdfDocument) {
        viewModelScope.launch {
            repository.recordAccess(document.id)
            sendEffect(StorageSideEffect.OpenPdf(document.filePath))
        }
    }

    private fun deleteDocument(documentId: Long) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf { repository.deleteDocument(documentId) }
                .onFailure { e ->
                    sendEffect(StorageSideEffect.ShowError(e.message ?: "Delete failed"))
                }
        }
    }

    private fun renameDocument(documentId: Long, newName: String) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf {
                val doc = repository.getDocumentById(documentId) ?: return@runCatchingPdf
                val newFile = File(doc.filePath).parentFile?.let { File(it, "$newName.pdf") }
                    ?: return@runCatchingPdf
                File(doc.filePath).renameTo(newFile)
                repository.saveDocument(doc.copy(name = newName, filePath = newFile.absolutePath))
            }.onFailure { e ->
                sendEffect(StorageSideEffect.ShowError(e.message ?: "Rename failed"))
            }
        }
    }

    private fun moveDocument(documentId: Long, targetFolderId: Long?) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf {
                val doc = repository.getDocumentById(documentId) ?: return@runCatchingPdf
                repository.saveDocument(doc.copy(folderId = targetFolderId))
            }.onFailure { e ->
                sendEffect(StorageSideEffect.ShowError(e.message ?: "Move failed"))
            }
        }
    }

    private fun shareDocument(document: PdfDocument) {
        val file = File(document.filePath)
        val uri = safHelper.getShareUri(file)
        sendEffect(StorageSideEffect.SharePdf(uri))
    }

    private fun importFile(uri: Uri) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf {
                val name = context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                    val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                    cursor.moveToFirst()
                    cursor.getString(nameIndex)
                } ?: "imported_${System.currentTimeMillis()}.pdf"
                val destFile = fileManager.newOutputFile(name)
                context.contentResolver.openInputStream(uri)?.use { input ->
                    destFile.outputStream().use { input.copyTo(it) }
                }
                val doc = PdfDocument(
                    name = destFile.nameWithoutExtension,
                    filePath = destFile.absolutePath,
                    sizeBytes = destFile.length(),
                    pageCount = countPages(destFile),
                    createdAt = System.currentTimeMillis(),
                    modifiedAt = System.currentTimeMillis()
                )
                repository.saveDocument(doc)
            }.onSuccess {
                sendEffect(StorageSideEffect.ShowMessage("File imported"))
            }.onFailure { e ->
                sendEffect(StorageSideEffect.ShowError(e.message ?: "Import failed"))
            }
        }
    }

    private fun toggleSelection(documentId: Long) {
        val current = state.value.selectedDocumentIds.toMutableSet()
        if (documentId in current) current.remove(documentId) else current.add(documentId)
        updateState { copy(selectedDocumentIds = current, isSelectionMode = current.isNotEmpty()) }
    }

    private fun deleteSelected() {
        viewModelScope.launch(Dispatchers.IO) {
            state.value.selectedDocumentIds.forEach { id ->
                runCatching { repository.deleteDocument(id) }
            }
            updateState { copy(selectedDocumentIds = emptySet(), isSelectionMode = false) }
        }
    }

    private fun createFolder(name: String, parentId: Long?) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf {
                val folder = Folder(
                    name = name,
                    parentId = parentId,
                    createdAt = System.currentTimeMillis()
                )
                repository.createFolder(folder)
            }.onFailure { e ->
                sendEffect(StorageSideEffect.ShowError(e.message ?: "Create folder failed"))
            }
        }
    }

    private fun deleteFolder(folderId: Long) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf { repository.deleteFolder(folderId) }
                .onFailure { e -> sendEffect(StorageSideEffect.ShowError(e.message ?: "Delete folder failed")) }
        }
    }

    private fun renameFolder(folderId: Long, newName: String) {
        viewModelScope.launch(Dispatchers.IO) {
            runCatchingPdf {
                val folder = repository.getFolderById(folderId) ?: return@runCatchingPdf
                repository.updateFolder(folder.copy(name = newName))
            }.onFailure { e -> sendEffect(StorageSideEffect.ShowError(e.message ?: "Rename failed")) }
        }
    }

    private fun countPages(file: java.io.File): Int = try {
        PdfRenderer(
            ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY)
        ).use { it.pageCount }
    } catch (_: Exception) {
        0
    }

}
