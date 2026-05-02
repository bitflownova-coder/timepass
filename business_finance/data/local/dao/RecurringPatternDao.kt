package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.RecurringPatternEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface RecurringPatternDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(pattern: RecurringPatternEntity): Long

    @Update
    suspend fun update(pattern: RecurringPatternEntity)

    @Query("DELETE FROM recurring_patterns WHERE id = :patternId")
    suspend fun deleteById(patternId: Long)

    @Query("SELECT * FROM recurring_patterns WHERE userId = :userId AND isDismissed = 0")
    fun getAllPatternsForUser(userId: String): Flow<List<RecurringPatternEntity>>

    @Query("SELECT * FROM recurring_patterns WHERE id = :patternId")
    suspend fun getById(patternId: Long): RecurringPatternEntity?

    @Query("SELECT * FROM recurring_patterns WHERE userId = :userId AND merchantName = :merchantName LIMIT 1")
    suspend fun findByMerchant(userId: String, merchantName: String): RecurringPatternEntity?

    @Query("SELECT * FROM recurring_patterns WHERE userId = :userId AND isConfirmedSubscription = 0 AND isDismissed = 0")
    suspend fun getUnconfirmedPatterns(userId: String): List<RecurringPatternEntity>

    @Query("UPDATE recurring_patterns SET isConfirmedSubscription = 1 WHERE id = :patternId")
    suspend fun confirmSubscription(patternId: Long)

    @Query("UPDATE recurring_patterns SET isDismissed = 1 WHERE id = :patternId")
    suspend fun dismissSubscription(patternId: Long)
    
    @Query("SELECT * FROM recurring_patterns WHERE userId = :userId AND isConfirmedSubscription = 1")
    fun getConfirmedSubscriptions(userId: String): Flow<List<RecurringPatternEntity>>

    @Query("SELECT * FROM recurring_patterns")
    suspend fun getAllPatternsRaw(): List<RecurringPatternEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPatternRaw(pattern: RecurringPatternEntity)
}
