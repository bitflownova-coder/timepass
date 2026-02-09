package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.ClientDiscussionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ClientDiscussionDao {
    
    @Query("SELECT * FROM client_discussions WHERE userId = :userId ORDER BY lastUpdated DESC")
    fun getAllDiscussions(userId: String): Flow<List<ClientDiscussionEntity>>
    
    @Query("SELECT * FROM client_discussions WHERE clientId = :clientId AND userId = :userId ORDER BY lastUpdated DESC")
    fun getDiscussionsByClient(clientId: Long, userId: String): Flow<List<ClientDiscussionEntity>>
    
    @Query("SELECT * FROM client_discussions WHERE status = :status AND userId = :userId ORDER BY lastUpdated DESC")
    fun getDiscussionsByStatus(status: String, userId: String): Flow<List<ClientDiscussionEntity>>
    
    @Query("SELECT * FROM client_discussions WHERE id = :id AND userId = :userId")
    suspend fun getDiscussionById(id: Long, userId: String): ClientDiscussionEntity?
    
    @Query("SELECT SUM(expectedAmount) FROM client_discussions WHERE status = 'pending' AND userId = :userId")
    fun getPendingTotal(userId: String): Flow<Double?>
    
    @Query("SELECT SUM(expectedAmount) FROM client_discussions WHERE status = 'finalized' AND userId = :userId")
    fun getFinalizedTotal(userId: String): Flow<Double?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDiscussion(discussion: ClientDiscussionEntity): Long
    
    @Update
    suspend fun updateDiscussion(discussion: ClientDiscussionEntity)
    
    @Delete
    suspend fun deleteDiscussion(discussion: ClientDiscussionEntity)
    
    @Query("UPDATE client_discussions SET status = :newStatus, lastUpdated = :timestamp WHERE id = :id")
    suspend fun updateStatus(id: Long, newStatus: String, timestamp: Long = System.currentTimeMillis())
    
    @Query("UPDATE client_discussions SET expectedAmount = :newAmount, notes = :notes, lastUpdated = :timestamp WHERE id = :id")
    suspend fun updateAmount(id: Long, newAmount: Double, notes: String, timestamp: Long = System.currentTimeMillis())
}
