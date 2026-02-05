package com.bitflow.finance.domain.usecase

import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Detects duplicate transactions using multiple strategies
 */
class DetectDuplicatesUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository
) {
    
    /**
     * Check if a transaction already exists
     * Uses multiple matching strategies:
     * 1. Exact match: date + amount + description
     * 2. Close match: date ± 1 day + amount + similar description
     * 3. Reference match: same reference number (if available)
     */
    suspend operator fun invoke(
        accountId: Long,
        date: java.time.LocalDate,
        amount: Double,
        description: String,
        reference: String?
    ): DuplicateCheckResult = withContext(Dispatchers.IO) {
        
        // Strategy 1: Exact match
        val existingTransactions = transactionRepository.getAllTransactionsForDeduplication(accountId)
        
        val exactKey = "$date|$amount|$description"
        val hasExactMatch = existingTransactions.any { 
            "${it.activityDate}|${it.amount}|${it.description}" == exactKey
        }
        
        if (hasExactMatch) {
            return@withContext DuplicateCheckResult(
                isDuplicate = true,
                matchType = MatchType.EXACT,
                confidence = 1.0
            )
        }
        
        // Strategy 2: Reference number match (high confidence)
        if (!reference.isNullOrBlank()) {
            val hasReferenceMatch = existingTransactions.any { txn ->
                !txn.reference.isNullOrBlank() && 
                txn.reference.equals(reference, ignoreCase = true)
            }
            
            if (hasReferenceMatch) {
                return@withContext DuplicateCheckResult(
                    isDuplicate = true,
                    matchType = MatchType.REFERENCE,
                    confidence = 0.95
                )
            }
        }
        
        // Strategy 3: Close match (date ± 1 day, same amount, similar description)
        val closeMatches = existingTransactions.filter { txn ->
            val daysDiff = Math.abs(java.time.temporal.ChronoUnit.DAYS.between(txn.activityDate, date))
            val amountMatch = Math.abs(txn.amount - amount) < 0.01 // Account for floating point
            val descSimilarity = calculateSimilarity(txn.description, description)
            
            daysDiff <= 1 && amountMatch && descSimilarity > 0.8
        }
        
        if (closeMatches.isNotEmpty()) {
            return@withContext DuplicateCheckResult(
                isDuplicate = true,
                matchType = MatchType.CLOSE,
                confidence = 0.85
            )
        }
        
        // No duplicate found
        DuplicateCheckResult(
            isDuplicate = false,
            matchType = null,
            confidence = 0.0
        )
    }
    
    private fun calculateSimilarity(s1: String, s2: String): Double {
        val str1 = s1.lowercase().trim()
        val str2 = s2.lowercase().trim()
        
        if (str1 == str2) return 1.0
        if (str1.isEmpty() || str2.isEmpty()) return 0.0
        
        // Levenshtein distance similarity
        val maxLen = maxOf(str1.length, str2.length)
        val distance = levenshteinDistance(str1, str2)
        return 1.0 - (distance.toDouble() / maxLen)
    }
    
    private fun levenshteinDistance(s1: String, s2: String): Int {
        val dp = Array(s1.length + 1) { IntArray(s2.length + 1) }
        
        for (i in 0..s1.length) dp[i][0] = i
        for (j in 0..s2.length) dp[0][j] = j
        
        for (i in 1..s1.length) {
            for (j in 1..s2.length) {
                val cost = if (s1[i - 1] == s2[j - 1]) 0 else 1
                dp[i][j] = minOf(
                    dp[i - 1][j] + 1,      // deletion
                    dp[i][j - 1] + 1,      // insertion
                    dp[i - 1][j - 1] + cost // substitution
                )
            }
        }
        
        return dp[s1.length][s2.length]
    }
    
    data class DuplicateCheckResult(
        val isDuplicate: Boolean,
        val matchType: MatchType?,
        val confidence: Double
    )
    
    enum class MatchType {
        EXACT,      // 100% match
        REFERENCE,  // Same reference number
        CLOSE       // Similar transaction within 1 day
    }
}
