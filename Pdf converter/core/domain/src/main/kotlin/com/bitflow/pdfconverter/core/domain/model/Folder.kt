package com.bitflow.pdfconverter.core.domain.model

data class Folder(
    val id: Long = 0,
    val name: String,
    val parentId: Long? = null,
    val createdAt: Long,
    val documentCount: Int = 0
)
