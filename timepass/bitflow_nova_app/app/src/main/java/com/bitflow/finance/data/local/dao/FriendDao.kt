package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bitflow.finance.data.local.entity.FriendEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface FriendDao {
    @Query("SELECT * FROM friends WHERE userId = :userId ORDER BY addedAt DESC")
    fun getFriendsByUser(userId: String): Flow<List<FriendEntity>>
    
    @Query("SELECT * FROM friends WHERE userId = :userId AND friendUserId = :friendUserId")
    suspend fun getFriend(userId: String, friendUserId: String): FriendEntity?
    
    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertFriend(friend: FriendEntity)
    
    @Query("DELETE FROM friends WHERE userId = :userId AND friendUserId = :friendUserId")
    suspend fun deleteFriend(userId: String, friendUserId: String)
    
    @Query("SELECT COUNT(*) FROM friends WHERE userId = :userId")
    suspend fun getFriendCount(userId: String): Int
}
