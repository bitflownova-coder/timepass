package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.SavingsGoalDao
import com.bitflow.finance.data.local.entity.SavingsGoalEntity
import com.bitflow.finance.domain.model.SavingsGoal
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.SavingsGoalRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SavingsGoalRepositoryImpl @Inject constructor(
    private val dao: SavingsGoalDao,
    private val authRepository: AuthRepository
) : SavingsGoalRepository {

    override fun getAllGoals(): Flow<List<SavingsGoal>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            if (userId != null) {
                dao.getAllGoals(userId).map { entities -> entities.map { it.toDomain() } }
            } else {
                flowOf(emptyList())
            }
        }
    }

    override fun getActiveGoals(): Flow<List<SavingsGoal>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            if (userId != null) {
                dao.getActiveGoals(userId).map { entities -> entities.map { it.toDomain() } }
            } else {
                flowOf(emptyList())
            }
        }
    }

    override suspend fun getGoalById(goalId: Long): SavingsGoal? {
        val userId = authRepository.currentUserId.first()
        return dao.getGoalById(goalId, userId)?.toDomain()
    }

    override suspend fun insertGoal(goal: SavingsGoal): Long {
        val userId = authRepository.currentUserId.first()
        return dao.insertGoal(goal.toEntity(userId))
    }

    override suspend fun updateGoal(goal: SavingsGoal) {
        val userId = authRepository.currentUserId.first()
        dao.updateGoal(goal.toEntity(userId))
    }

    override suspend fun addContribution(goalId: Long, amount: Double) {
        val userId = authRepository.currentUserId.first()
        dao.addContribution(goalId, amount, userId)
        
        // Check if goal is now complete
        val goal = dao.getGoalById(goalId, userId)
        if (goal != null && goal.currentAmount >= goal.targetAmount) {
            dao.markCompleted(goalId, userId)
        }
    }

    override suspend fun markCompleted(goalId: Long) {
        val userId = authRepository.currentUserId.first()
        dao.markCompleted(goalId, userId)
    }

    override suspend fun deleteGoal(goal: SavingsGoal) {
        val userId = authRepository.currentUserId.first()
        dao.deleteGoal(goal.toEntity(userId))
    }

    private fun SavingsGoalEntity.toDomain() = SavingsGoal(
        id = id,
        name = name,
        targetAmount = targetAmount,
        currentAmount = currentAmount,
        deadline = deadline,
        iconEmoji = iconEmoji,
        colorHex = colorHex,
        createdAt = createdAt,
        isCompleted = isCompleted
    )

    private fun SavingsGoal.toEntity(userId: String) = SavingsGoalEntity(
        id = id,
        userId = userId,
        name = name,
        targetAmount = targetAmount,
        currentAmount = currentAmount,
        deadline = deadline,
        iconEmoji = iconEmoji,
        colorHex = colorHex,
        createdAt = createdAt,
        isCompleted = isCompleted
    )
}
