package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "bill_reminders")
data class BillReminderEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String,
    val amount: Double,
    val dueDay: Int,                    // Day of month (1-31)
    val reminderDaysBefore: Int = 3,    // Remind 3 days before
    val isRecurring: Boolean = true,
    val categoryId: Long? = null,
    val isActive: Boolean = true,
    val lastNotifiedMonth: Int? = null, // Track which month we last notified
    val createdAt: Long = System.currentTimeMillis()
)
