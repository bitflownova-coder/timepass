package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "password_history")
data class PasswordHistoryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val password: String,
    val length: Int,
    val type: String,  // "random", "passphrase", "pronounceable"
    val strength: String,  // "weak", "medium", "strong", "very_strong"
    val label: String = "",  // Optional label for what it's used for
    val createdAt: Long = System.currentTimeMillis()
)
