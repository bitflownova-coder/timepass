package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.UserAccountEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface UserAccountDao {
    @Query("SELECT * FROM user_accounts WHERE isActive = 1 ORDER BY lastLoginAt DESC")
    fun getAllActiveUsers(): Flow<List<UserAccountEntity>>
    
    @Query("SELECT * FROM user_accounts WHERE userId = :userId")
    suspend fun getUserById(userId: String): UserAccountEntity?

    @Query("SELECT * FROM user_accounts WHERE userId = :userId")
    fun getUserFlow(userId: String): Flow<UserAccountEntity?>
    
    // Username is UNIQUE - returns single user or null
    @Query("SELECT * FROM user_accounts WHERE username = :username AND isActive = 1 LIMIT 1")
    suspend fun getUserByUsername(username: String): UserAccountEntity?
    
    // Authentication: Returns user if username and password match
    @Query("SELECT * FROM user_accounts WHERE username = :username AND passwordHash = :passwordHash AND isActive = 1 LIMIT 1")
    suspend fun authenticateUser(username: String, passwordHash: String): UserAccountEntity?
    
    // Verify security answer
    @Query("SELECT * FROM user_accounts WHERE username = :username AND securityAnswerHash = :answerHash AND isActive = 1 LIMIT 1")
    suspend fun verifySecurityAnswer(username: String, answerHash: String): UserAccountEntity?
    
    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertUser(user: UserAccountEntity)
    
    @Update
    suspend fun updateUser(user: UserAccountEntity)
    
    @Query("UPDATE user_accounts SET lastLoginAt = :timestamp WHERE userId = :userId")
    suspend fun updateLastLogin(userId: String, timestamp: Long)
    
    @Query("UPDATE user_accounts SET isActive = 0 WHERE userId = :userId")
    suspend fun softDeleteUser(userId: String)
}
