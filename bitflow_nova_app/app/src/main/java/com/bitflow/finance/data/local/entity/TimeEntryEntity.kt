package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "time_entries")
data class TimeEntryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val projectName: String,
    val clientId: Long? = null,  // Optional link to client
    val clientName: String = "",  // Cached client name for quick display
    val taskDescription: String = "",
    val tags: String = "",  // Comma-separated tags: "coding,meeting,research"
    val hourlyRate: Double = 0.0,
    val startTime: Long,  // Timestamp when started
    val endTime: Long? = null,  // Null if timer is still running
    val durationMinutes: Int = 0,  // Cached duration for completed entries
    val isManualEntry: Boolean = false,
    val notes: String = "",
    val createdAt: Long = System.currentTimeMillis()
)
