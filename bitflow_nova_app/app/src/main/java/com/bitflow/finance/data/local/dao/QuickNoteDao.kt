package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.QuickNoteEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface QuickNoteDao {
    
    @Query("SELECT * FROM quick_notes WHERE userId = :userId ORDER BY isPinned DESC, updatedAt DESC")
    fun getAllNotes(userId: String): Flow<List<QuickNoteEntity>>
    
    @Query("SELECT * FROM quick_notes WHERE userId = :userId AND isPinned = 1 ORDER BY updatedAt DESC")
    fun getPinnedNotes(userId: String): Flow<List<QuickNoteEntity>>
    
    @Query("SELECT * FROM quick_notes WHERE userId = :userId AND folder = :folder ORDER BY isPinned DESC, updatedAt DESC")
    fun getNotesByFolder(userId: String, folder: String): Flow<List<QuickNoteEntity>>
    
    @Query("SELECT * FROM quick_notes WHERE userId = :userId AND (title LIKE '%' || :query || '%' OR content LIKE '%' || :query || '%') ORDER BY isPinned DESC, updatedAt DESC")
    fun searchNotes(userId: String, query: String): Flow<List<QuickNoteEntity>>
    
    @Query("SELECT DISTINCT folder FROM quick_notes WHERE userId = :userId ORDER BY folder ASC")
    fun getAllFolders(userId: String): Flow<List<String>>
    
    @Query("SELECT * FROM quick_notes WHERE id = :id")
    suspend fun getNoteById(id: Long): QuickNoteEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNote(note: QuickNoteEntity): Long
    
    @Update
    suspend fun updateNote(note: QuickNoteEntity)
    
    @Delete
    suspend fun deleteNote(note: QuickNoteEntity)
    
    @Query("DELETE FROM quick_notes WHERE id = :id")
    suspend fun deleteById(id: Long)
    
    @Query("UPDATE quick_notes SET isPinned = :pinned, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updatePinStatus(id: Long, pinned: Boolean, updatedAt: Long = System.currentTimeMillis())
}
