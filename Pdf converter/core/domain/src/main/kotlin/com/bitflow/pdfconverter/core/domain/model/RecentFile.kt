package com.bitflow.pdfconverter.core.domain.model

data class RecentFile(
    val id: Long = 0,
    val documentId: Long,
    val name: String,
    val filePath: String,
    val accessedAt: Long,
    val thumbnailPath: String? = null
)
