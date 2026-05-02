package com.bitflow.finance.domain.usecase

import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.model.CategoryLearningRule
import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import java.time.LocalDateTime

/**
 * The "Magic" - Invisible Auto-Learning System
 * 
 * Philosophy: Never ask user to create rules. Learn silently from corrections.
 * When user changes category on an activity, we automatically create a learning rule.
 */
class AutoLearnCategoryUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository
) {
    /**
     * Called when user manually changes category on an activity
     * This is the feedback loop that makes the system smarter
     */
    suspend fun learnFromUserCorrection(
        activity: Activity,
        oldCategoryId: Long?,
        newCategoryId: Long
    ) {
        // Extract learning pattern from description
        val pattern = extractPattern(activity.description)
        
        if (pattern.isNotBlank()) {
            // Check if a rule already exists
            val existingRule = transactionRepository.findLearningRule(pattern)
            
            if (existingRule != null) {
                // Update existing rule - increase confidence if user confirms same category
                val updatedRule = if (existingRule.categoryId == newCategoryId) {
                    existingRule.copy(
                        confidenceScore = minOf(1.0f, existingRule.confidenceScore + 0.1f),
                        usageCount = existingRule.usageCount + 1,
                        lastAppliedAt = LocalDateTime.now()
                    )
                } else {
                    // User chose different category - update the rule
                    existingRule.copy(
                        categoryId = newCategoryId,
                        confidenceScore = 0.6f, // Reset confidence
                        usageCount = existingRule.usageCount + 1,
                        lastAppliedAt = LocalDateTime.now()
                    )
                }
                transactionRepository.updateLearningRule(updatedRule)
            } else {
                // Create new learning rule
                val newRule = CategoryLearningRule(
                    descriptionPattern = pattern,
                    categoryId = newCategoryId,
                    confidenceScore = 0.8f, // Start with high confidence
                    usageCount = 1,
                    createdByUserCorrection = true
                )
                transactionRepository.insertLearningRule(newRule)
            }
        }
    }

    /**
     * Auto-categorize new activities based on learned patterns
     * Returns suggested category ID and confidence score
     */
    suspend fun suggestCategory(description: String): Pair<Long?, Float>? {
        val pattern = extractPattern(description)
        if (pattern.isBlank()) return null
        
        // Find matching rule with highest confidence
        val matchingRule = transactionRepository.findLearningRule(pattern)
        
        return if (matchingRule != null && matchingRule.confidenceScore > 0.5f) {
            Pair(matchingRule.categoryId, matchingRule.confidenceScore)
        } else {
            null
        }
    }

    /**
     * Apply auto-learning to batch of activities (e.g., after import)
     */
    suspend fun autoCategorizeBatch(activities: List<Activity>): List<Activity> {
        val rules = transactionRepository.getAllLearningRules().first()
        
        return activities.map { activity ->
            if (activity.categoryId == null) {
                val suggestion = findBestMatch(activity.description, rules)
                if (suggestion != null) {
                    activity.copy(
                        categoryId = suggestion.first,
                        isAutoCategorized = true,
                        confidenceScore = suggestion.second
                    )
                } else {
                    activity
                }
            } else {
                activity
            }
        }
    }

    private fun findBestMatch(
        description: String,
        rules: List<CategoryLearningRule>
    ): Pair<Long, Float>? {
        val pattern = extractPattern(description)
        
        return rules
            .filter { description.contains(it.descriptionPattern, ignoreCase = true) }
            .maxByOrNull { it.confidenceScore }
            ?.let { Pair(it.categoryId, it.confidenceScore) }
    }

    /**
     * Extract key pattern from description
     * E.g., "UPI/DR/203290292730/NETFLIX/BKID/..." -> "netflix"
     */
    private fun extractPattern(description: String): String {
        // Remove common UPI prefixes and transaction IDs
        val cleaned = description
            .replace(Regex("UPI/(CR|DR)/\\d+/"), "")
            .replace(Regex("/BKID/.*"), "")
            .replace(Regex("/PYTM/.*"), "")
            .replace(Regex("/HDFC/.*"), "")
            .replace(Regex("/SBIN/.*"), "")
            .replace(Regex("/YESB/.*"), "")
            .replace(Regex("/IBKL/.*"), "")
            .replace(Regex("/UBIN/.*"), "")
            .replace(Regex("/FDRL/.*"), "")
            .replace(Regex("/AIRP/.*"), "")
            .replace(Regex("/UTIB/.*"), "")
            .trim()
            .split("/")
            .firstOrNull { it.length > 3 } // Take first meaningful word
            ?: ""
        
        return cleaned.lowercase().take(20) // Limit pattern length
    }
}
