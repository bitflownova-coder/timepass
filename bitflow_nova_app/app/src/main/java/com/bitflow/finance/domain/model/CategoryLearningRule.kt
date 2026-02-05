package com.bitflow.finance.domain.model

import java.time.LocalDateTime

/**
 * Invisible auto-learning rule created when user corrects a category
 * Never shown to user - works silently in the background
 */
data class CategoryLearningRule(
    val id: Long = 0,
    val descriptionPattern: String, // e.g., "uber", "netflix"
    val categoryId: Long,
    val confidenceScore: Float = 1.0f, // 0.0 to 1.0
    val usageCount: Int = 0,
    val lastAppliedAt: LocalDateTime? = null,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val createdByUserCorrection: Boolean = true
)
