package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.SavingsGoalEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SavingsGoalDao {
    
    @Query("SELECT * FROM savings_goals WHERE userId = :userId ORDER BY createdAt DESC")
    fun getAllGoals(userId: String): Flow<List<SavingsGoalEntity>>
    
    @Query("SELECT * FROM savings_goals WHERE userId = :userId AND isCompleted = 0 ORDER BY deadline ASC")
    fun getActiveGoals(userId: String): Flow<List<SavingsGoalEntity>>
    
    @Query("SELECT * FROM savings_goals WHERE id = :goalId AND userId = :userId")
    suspend fun getGoalById(goalId: Long, userId: String): SavingsGoalEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGoal(goal: SavingsGoalEntity): Long
    
    @Update
    suspend fun updateGoal(goal: SavingsGoalEntity)
    
    @Query("UPDATE savings_goals SET currentAmount = currentAmount + :amount WHERE id = :goalId AND userId = :userId")
    suspend fun addContribution(goalId: Long, amount: Double, userId: String)
    
    @Query("UPDATE savings_goals SET isCompleted = 1 WHERE id = :goalId AND userId = :userId")
    suspend fun markCompleted(goalId: Long, userId: String)
    
    @Delete
    suspend fun deleteGoal(goal: SavingsGoalEntity)
    @Query("SELECT * FROM savings_goals")
    suspend fun getAllGoalsRaw(): List<SavingsGoalEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGoalRaw(goal: SavingsGoalEntity)
}
