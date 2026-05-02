package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.PasswordHistoryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PasswordHistoryDao {
    
    @Query("SELECT * FROM password_history WHERE userId = :userId ORDER BY createdAt DESC LIMIT :limit")
    fun getRecentPasswords(userId: String, limit: Int = 50): Flow<List<PasswordHistoryEntity>>
    
    @Query("SELECT * FROM password_history WHERE userId = :userId ORDER BY createdAt DESC")
    fun getAllPasswords(userId: String): Flow<List<PasswordHistoryEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPassword(password: PasswordHistoryEntity): Long
    
    @Delete
    suspend fun deletePassword(password: PasswordHistoryEntity)
    
    @Query("DELETE FROM password_history WHERE id = :id")
    suspend fun deleteById(id: Long)
    
    @Query("DELETE FROM password_history WHERE userId = :userId")
    suspend fun clearHistory(userId: String)
    
    // Keep only the latest N passwords
    @Query("""
        DELETE FROM password_history 
        WHERE userId = :userId AND id NOT IN (
            SELECT id FROM password_history WHERE userId = :userId ORDER BY createdAt DESC LIMIT :keepCount
        )
    """)
    suspend fun trimHistory(userId: String, keepCount: Int = 50)
}
