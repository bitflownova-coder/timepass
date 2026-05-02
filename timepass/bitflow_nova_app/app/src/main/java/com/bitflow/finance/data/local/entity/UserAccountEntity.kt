package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * User account table for multi-user support
 * Username is UNIQUE - used for login
 * displayName is for UI display (can be same as username)
 * Security question provides extra verification for username conflicts
 */
@Entity(
    tableName = "user_accounts",
    indices = [Index(value = ["username"], unique = true)]
)
data class UserAccountEntity(
    @PrimaryKey val userId: String, // UUID - internal identifier
    val username: String, // UNIQUE - used for login
    val displayName: String, // Display name - shown in UI (can match username)
    val passwordHash: String,
    val securityQuestion: String, // e.g., "What is your mother's maiden name?"
    val securityAnswerHash: String, // Hashed answer
    val createdAt: Long = System.currentTimeMillis(),
    val lastLoginAt: Long = System.currentTimeMillis(),
    val isActive: Boolean = true, // For soft delete
    val isBusinessEnabled: Boolean = false, // Track if user has activated business features
    // Gamification - Streaks
    val currentStreak: Int = 0,
    val longestStreak: Int = 0,
    val lastLogDate: Long? = null // Last date a transaction was logged
)
