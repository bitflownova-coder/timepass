package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.BillReminderEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface BillReminderDao {
    
    @Query("SELECT * FROM bill_reminders WHERE userId = :userId AND isActive = 1 ORDER BY dueDay ASC")
    fun getActiveReminders(userId: String): Flow<List<BillReminderEntity>>
    
    @Query("SELECT * FROM bill_reminders WHERE userId = :userId ORDER BY dueDay ASC")
    fun getAllReminders(userId: String): Flow<List<BillReminderEntity>>
    
    @Query("SELECT * FROM bill_reminders WHERE userId = :userId AND isActive = 1 AND (lastNotifiedMonth IS NULL OR lastNotifiedMonth != :currentMonth)")
    suspend fun getRemindersForNotification(userId: String, currentMonth: Int): List<BillReminderEntity>
    
    @Query("UPDATE bill_reminders SET lastNotifiedMonth = :month WHERE id = :id")
    suspend fun markAsNotified(id: Long, month: Int)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReminder(reminder: BillReminderEntity): Long
    
    @Update
    suspend fun updateReminder(reminder: BillReminderEntity)
    
    @Delete
    suspend fun deleteReminder(reminder: BillReminderEntity)
    
    @Query("UPDATE bill_reminders SET isActive = :isActive WHERE id = :id")
    suspend fun setActive(id: Long, isActive: Boolean)

    @Query("SELECT * FROM bill_reminders")
    suspend fun getAllRemindersRaw(): List<BillReminderEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReminderRaw(reminder: BillReminderEntity)
}
