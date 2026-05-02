package com.bitflow.pdfconverter.core.data.database.dao

import androidx.room.*
import com.bitflow.pdfconverter.core.data.database.entity.RecentFileEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface RecentFileDao {

    @Query("SELECT * FROM recent_files ORDER BY accessedAt DESC LIMIT :limit")
    fun getRecentFiles(limit: Int = 20): Flow<List<RecentFileEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(recentFile: RecentFileEntity)

    @Query("DELETE FROM recent_files WHERE documentId = :documentId")
    suspend fun deleteByDocumentId(documentId: Long)

    @Query("""
        UPDATE recent_files 
        SET accessedAt = :accessedAt 
        WHERE documentId = :documentId
    """)
    suspend fun updateAccessTime(documentId: Long, accessedAt: Long)

    @Query("DELETE FROM recent_files WHERE id NOT IN (SELECT id FROM recent_files ORDER BY accessedAt DESC LIMIT 50)")
    suspend fun pruneOldEntries()
}
