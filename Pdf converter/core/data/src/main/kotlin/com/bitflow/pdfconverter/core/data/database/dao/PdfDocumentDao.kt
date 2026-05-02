package com.bitflow.pdfconverter.core.data.database.dao

import androidx.room.*
import com.bitflow.pdfconverter.core.data.database.entity.PdfDocumentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PdfDocumentDao {

    @Query("SELECT * FROM pdf_documents WHERE folderId IS :folderId ORDER BY modifiedAt DESC")
    fun getDocumentsByFolder(folderId: Long?): Flow<List<PdfDocumentEntity>>

    @Query("SELECT * FROM pdf_documents ORDER BY modifiedAt DESC")
    fun getAllDocuments(): Flow<List<PdfDocumentEntity>>

    @Query("SELECT * FROM pdf_documents WHERE id = :id")
    suspend fun getDocumentById(id: Long): PdfDocumentEntity?

    @Query("SELECT * FROM pdf_documents WHERE name LIKE '%' || :query || '%' ORDER BY modifiedAt DESC")
    fun searchDocuments(query: String): Flow<List<PdfDocumentEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocument(document: PdfDocumentEntity): Long

    @Update
    suspend fun updateDocument(document: PdfDocumentEntity)

    @Delete
    suspend fun deleteDocument(document: PdfDocumentEntity)

    @Query("DELETE FROM pdf_documents WHERE id = :id")
    suspend fun deleteDocumentById(id: Long)
}
