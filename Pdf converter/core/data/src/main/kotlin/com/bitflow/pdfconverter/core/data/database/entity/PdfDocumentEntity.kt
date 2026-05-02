package com.bitflow.pdfconverter.core.data.database.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "pdf_documents")
data class PdfDocumentEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val filePath: String,
    val sizeBytes: Long,
    val pageCount: Int,
    val createdAt: Long,
    val modifiedAt: Long,
    val folderId: Long?,
    val isPasswordProtected: Boolean = false,
    val thumbnailPath: String? = null
)
