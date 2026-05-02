package com.bitflow.pdfconverter.core.data.repository

import com.bitflow.pdfconverter.core.data.database.dao.FolderDao
import com.bitflow.pdfconverter.core.data.database.dao.PdfDocumentDao
import com.bitflow.pdfconverter.core.data.database.dao.RecentFileDao
import com.bitflow.pdfconverter.core.data.database.entity.FolderEntity
import com.bitflow.pdfconverter.core.data.database.entity.PdfDocumentEntity
import com.bitflow.pdfconverter.core.data.database.entity.RecentFileEntity
import com.bitflow.pdfconverter.core.domain.model.Folder
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.domain.model.RecentFile
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class PdfDocumentRepository @Inject constructor(
    private val documentDao: PdfDocumentDao,
    private val recentFileDao: RecentFileDao,
    private val folderDao: FolderDao
) {
    // ── Documents ──────────────────────────────────────────────────────────

    fun getAllDocuments(): Flow<List<PdfDocument>> =
        documentDao.getAllDocuments().map { list -> list.map { it.toDomain() } }

    fun getDocumentsByFolder(folderId: Long?): Flow<List<PdfDocument>> =
        documentDao.getDocumentsByFolder(folderId).map { list -> list.map { it.toDomain() } }

    fun searchDocuments(query: String): Flow<List<PdfDocument>> =
        documentDao.searchDocuments(query).map { list -> list.map { it.toDomain() } }

    suspend fun getDocumentById(documentId: Long): PdfDocument? =
        documentDao.getDocumentById(documentId)?.toDomain()

    fun getRecentFiles(limit: Int = 20): Flow<List<RecentFile>> =
        recentFileDao.getRecentFiles().map { list -> list.take(limit).map { it.toDomain() } }

    suspend fun saveDocument(document: PdfDocument): Long {
        val id = if (document.id == 0L) {
            documentDao.insertDocument(document.toEntity())
        } else {
            documentDao.updateDocument(document.toEntity())
            document.id
        }
        recentFileDao.insertOrUpdate(
            RecentFileEntity(
                documentId = id,
                name = document.name,
                filePath = document.filePath,
                accessedAt = System.currentTimeMillis(),
                thumbnailPath = document.thumbnailPath
            )
        )
        recentFileDao.pruneOldEntries()
        return id
    }

    suspend fun recordAccess(documentId: Long) {
        recentFileDao.updateAccessTime(documentId, System.currentTimeMillis())
    }

    suspend fun deleteDocument(documentId: Long) {
        documentDao.deleteDocumentById(documentId)
        recentFileDao.deleteByDocumentId(documentId)
    }

    // ── Folders ────────────────────────────────────────────────────────────

    fun getAllFolders(): Flow<List<Folder>> =
        folderDao.getFoldersByParent(null).map { list -> list.map { it.toDomain() } }

    fun getFoldersByParent(parentId: Long?): Flow<List<Folder>> =
        folderDao.getFoldersByParent(parentId).map { list -> list.map { it.toDomain() } }

    suspend fun getFolderById(folderId: Long): Folder? =
        folderDao.getFolderById(folderId)?.toDomain()

    suspend fun createFolder(folder: Folder): Long =
        folderDao.insertFolder(folder.toEntity())

    suspend fun updateFolder(folder: Folder) =
        folderDao.updateFolder(folder.toEntity())

    suspend fun deleteFolder(folderId: Long) {
        val entity = folderDao.getFolderById(folderId) ?: return
        folderDao.deleteFolder(entity)
    }

    // ── Mapping helpers ────────────────────────────────────────────────────

    private fun PdfDocumentEntity.toDomain() = PdfDocument(
        id = id, name = name, filePath = filePath, sizeBytes = sizeBytes,
        pageCount = pageCount, createdAt = createdAt, modifiedAt = modifiedAt,
        folderId = folderId, isPasswordProtected = isPasswordProtected, thumbnailPath = thumbnailPath
    )

    private fun PdfDocument.toEntity() = PdfDocumentEntity(
        id = id, name = name, filePath = filePath, sizeBytes = sizeBytes,
        pageCount = pageCount, createdAt = createdAt, modifiedAt = modifiedAt,
        folderId = folderId, isPasswordProtected = isPasswordProtected, thumbnailPath = thumbnailPath
    )

    private fun RecentFileEntity.toDomain() = RecentFile(
        id = id, documentId = documentId, name = name,
        filePath = filePath, accessedAt = accessedAt, thumbnailPath = thumbnailPath
    )

    private fun FolderEntity.toDomain() = Folder(
        id = id, name = name, parentId = parentId, createdAt = createdAt
    )

    private fun Folder.toEntity() = FolderEntity(
        id = id, name = name, parentId = parentId, createdAt = createdAt
    )
}
