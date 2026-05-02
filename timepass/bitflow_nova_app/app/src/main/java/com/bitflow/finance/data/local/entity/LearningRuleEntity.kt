package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.time.LocalDateTime

/**
 * Silent learning system: Maps merchant names to categories.
 * Auto-created when user manually categorizes transactions.
 */
@Entity(
    tableName = "learning_rules",
    indices = [Index(value = ["userId", "merchantPattern"])]
)
data class LearningRuleEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String, // Owner of this learning rule
    val merchantPattern: String, // Normalized merchant name
    val categoryId: Long,
    val confidenceScore: Float = 1.0f, // Increases with each confirmation
    val usageCount: Int = 1, // Times this rule has been applied
    val createdAt: LocalDateTime,
    val lastUsedAt: LocalDateTime
)
