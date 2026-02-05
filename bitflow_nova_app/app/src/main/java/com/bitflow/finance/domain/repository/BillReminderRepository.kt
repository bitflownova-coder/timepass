package com.bitflow.finance.domain.repository

import com.bitflow.finance.domain.model.BillReminder
import kotlinx.coroutines.flow.Flow

interface BillReminderRepository {
    fun getActiveReminders(): Flow<List<BillReminder>>
    fun getAllReminders(): Flow<List<BillReminder>>
    suspend fun getRemindersForNotification(): List<BillReminder>
    suspend fun markAsNotified(id: Long)
    suspend fun insertReminder(reminder: BillReminder): Long
    suspend fun updateReminder(reminder: BillReminder)
    suspend fun deleteReminder(reminder: BillReminder)
    suspend fun setActive(id: Long, isActive: Boolean)
}
