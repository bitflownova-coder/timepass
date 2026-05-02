package com.bitflow.pdfconverter.core.data.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.bitflow.pdfconverter.core.data.database.dao.FolderDao
import com.bitflow.pdfconverter.core.data.database.dao.PdfDocumentDao
import com.bitflow.pdfconverter.core.data.database.dao.RecentFileDao
import com.bitflow.pdfconverter.core.data.database.entity.FolderEntity
import com.bitflow.pdfconverter.core.data.database.entity.PdfDocumentEntity
import com.bitflow.pdfconverter.core.data.database.entity.RecentFileEntity

@Database(
    entities = [PdfDocumentEntity::class, RecentFileEntity::class, FolderEntity::class],
    version = 1,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun pdfDocumentDao(): PdfDocumentDao
    abstract fun recentFileDao(): RecentFileDao
    abstract fun folderDao(): FolderDao

    companion object {
        const val DATABASE_NAME = "pdf_converter.db"
    }
}
