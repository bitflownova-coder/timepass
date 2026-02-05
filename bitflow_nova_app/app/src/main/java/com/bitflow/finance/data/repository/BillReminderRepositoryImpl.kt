package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.BillReminderDao
import com.bitflow.finance.data.local.entity.BillReminderEntity
import com.bitflow.finance.domain.model.BillReminder
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.BillReminderRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import java.util.Calendar
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BillReminderRepositoryImpl @Inject constructor(
    private val dao: BillReminderDao,
    private val authRepository: AuthRepository
) : BillReminderRepository {

    override fun getActiveReminders(): Flow<List<BillReminder>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            if (userId != null) {
                dao.getActiveReminders(userId).map { entities -> entities.map { it.toDomain() } }
            } else {
                flowOf(emptyList())
            }
        }
    }

    override fun getAllReminders(): Flow<List<BillReminder>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            if (userId != null) {
                dao.getAllReminders(userId).map { entities -> entities.map { it.toDomain() } }
            } else {
                flowOf(emptyList())
            }
        }
    }

    override suspend fun getRemindersForNotification(): List<BillReminder> {
        val userId = authRepository.currentUserId.first()
        val currentMonth = Calendar.getInstance().get(Calendar.MONTH)
        return dao.getRemindersForNotification(userId, currentMonth).map { it.toDomain() }
    }

    override suspend fun markAsNotified(id: Long) {
        val currentMonth = Calendar.getInstance().get(Calendar.MONTH)
        dao.markAsNotified(id, currentMonth)
    }

    override suspend fun insertReminder(reminder: BillReminder): Long {
        val userId = authRepository.currentUserId.first()
        return dao.insertReminder(reminder.toEntity(userId))
    }

    override suspend fun updateReminder(reminder: BillReminder) {
        val userId = authRepository.currentUserId.first()
        dao.updateReminder(reminder.toEntity(userId))
    }

    override suspend fun deleteReminder(reminder: BillReminder) {
        val userId = authRepository.currentUserId.first()
        dao.deleteReminder(reminder.toEntity(userId))
    }

    override suspend fun setActive(id: Long, isActive: Boolean) {
        dao.setActive(id, isActive)
    }

    private fun BillReminderEntity.toDomain() = BillReminder(
        id = id,
        name = name,
        amount = amount,
        dueDay = dueDay,
        reminderDaysBefore = reminderDaysBefore,
        isRecurring = isRecurring,
        categoryId = categoryId,
        isActive = isActive,
        createdAt = createdAt
    )

    private fun BillReminder.toEntity(userId: String) = BillReminderEntity(
        id = id,
        userId = userId,
        name = name,
        amount = amount,
        dueDay = dueDay,
        reminderDaysBefore = reminderDaysBefore,
        isRecurring = isRecurring,
        categoryId = categoryId,
        isActive = isActive,
        createdAt = createdAt
    )
}
