package com.bitflow.finance.domain.repository

import com.bitflow.finance.domain.model.SavingsGoal
import kotlinx.coroutines.flow.Flow

interface SavingsGoalRepository {
    fun getAllGoals(): Flow<List<SavingsGoal>>
    fun getActiveGoals(): Flow<List<SavingsGoal>>
    suspend fun getGoalById(goalId: Long): SavingsGoal?
    suspend fun insertGoal(goal: SavingsGoal): Long
    suspend fun updateGoal(goal: SavingsGoal)
    suspend fun addContribution(goalId: Long, amount: Double)
    suspend fun markCompleted(goalId: Long)
    suspend fun deleteGoal(goal: SavingsGoal)
}
