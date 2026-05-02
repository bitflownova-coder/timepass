package com.bitflow.pdfconverter.core.data.di

import android.content.Context
import androidx.room.Room
import com.bitflow.pdfconverter.core.data.database.AppDatabase
import com.bitflow.pdfconverter.core.data.database.AppDatabase.Companion.DATABASE_NAME
import com.bitflow.pdfconverter.core.data.repository.PdfDocumentRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DataModule {

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, DATABASE_NAME)
            .fallbackToDestructiveMigration()
            .build()

    @Provides
    fun providePdfDocumentDao(db: AppDatabase) = db.pdfDocumentDao()

    @Provides
    fun provideRecentFileDao(db: AppDatabase) = db.recentFileDao()

    @Provides
    fun provideFolderDao(db: AppDatabase) = db.folderDao()

    @Provides
    @Singleton
    fun providePdfDocumentRepository(
        db: AppDatabase
    ): PdfDocumentRepository = PdfDocumentRepository(
        documentDao = db.pdfDocumentDao(),
        recentFileDao = db.recentFileDao(),
        folderDao = db.folderDao()
    )
}
