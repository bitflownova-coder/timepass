package com.bitflow.pdfconverter.core.data.database.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "recent_files",
    foreignKeys = [ForeignKey(
        entity = PdfDocumentEntity::class,
        parentColumns = ["id"],
        childColumns = ["documentId"],
        onDelete = ForeignKey.CASCADE
    )],
    indices = [Index("documentId")]
)
data class RecentFileEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val documentId: Long,
    val name: String,
    val filePath: String,
    val accessedAt: Long,
    val thumbnailPath: String? = null
)
