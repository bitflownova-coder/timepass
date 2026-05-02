package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.local.entity.CategoryEntity
import com.bitflow.finance.domain.model.FinancialPersona
import com.bitflow.finance.domain.repository.CategoryRepository
import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import java.time.LocalDate

class BehaviorAnalyzerUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val categoryRepository: CategoryRepository
) {

    operator fun invoke(userId: String): Flow<FinancialPersona> {
        // combine transactions and categories to analyze
        return combine(
            transactionRepository.getAllTransactions(), // This might be heavy, in real app use simpler query
            categoryRepository.getCategoriesStream(userId)
        ) { transactions, categories ->
            
            if (transactions.size < 10) return@combine FinancialPersona.UNCATEGORIZED
            
            val recentTxns = transactions.filter { 
                it.activityDate.isAfter(LocalDate.now().minusMonths(3)) && 
                it.type == com.bitflow.finance.domain.model.ActivityType.EXPENSE 
            }
            
            if (recentTxns.isEmpty()) return@combine FinancialPersona.UNCATEGORIZED

            val totalExpense = recentTxns.sumOf { it.amount }
            
            // Map Category ID to Essential/Discretionary
            val essentialCatIds = categories.filter { it.isEssential }.map { it.id }.toSet()
            
            val essentialSpend = recentTxns.filter { essentialCatIds.contains(it.categoryId ?: -1) }.sumOf { it.amount }
            val discretionarySpend = totalExpense - essentialSpend
            
            val discretionaryRatio = if (totalExpense > 0) discretionarySpend / totalExpense else 0.0
            
            // Simple logic for now
            when {
                discretionaryRatio > 0.6 -> FinancialPersona.IMPULSE_SPENDER
                discretionaryRatio < 0.2 -> FinancialPersona.CONSCIOUS_SAVER
                else -> FinancialPersona.BALANCED_BUILDER
            }
        }
    }
}
