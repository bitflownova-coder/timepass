package com.bitflow.pdfconverter.core.domain.model

data class PdfDocument(
    val id: Long = 0,
    val name: String,
    val filePath: String,
    val sizeBytes: Long,
    val pageCount: Int,
    val createdAt: Long,
    val modifiedAt: Long,
    val folderId: Long? = null,
    val isPasswordProtected: Boolean = false,
    val thumbnailPath: String? = null
)
