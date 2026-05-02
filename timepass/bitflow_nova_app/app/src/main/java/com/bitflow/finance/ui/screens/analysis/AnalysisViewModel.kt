package com.bitflow.finance.ui.screens.analysis

import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.ui.components.TimeFilter
import com.bitflow.finance.ui.components.getDateRangeForFilter
import dagger.hilt.android.lifecycle.HiltViewModel
import com.patrykandpatrick.vico.core.entry.ChartEntryModelProducer
import com.patrykandpatrick.vico.core.entry.entryOf
import java.time.LocalDate
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

@HiltViewModel
class AnalysisViewModel @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val settingsRepository: com.bitflow.finance.domain.repository.SettingsRepository,
    private val accountRepository: com.bitflow.finance.domain.repository.AccountRepository
) : ViewModel() {

    private val selectedFilter = MutableStateFlow(TimeFilter.THIS_MONTH)
    private val selectedAccountId = MutableStateFlow<Long?>(null) // null = all accounts

    val uiState: StateFlow<AnalysisUiState> = combine(
        transactionRepository.getAllTransactions(),
        transactionRepository.getAllCategories(),
        settingsRepository.currencySymbol,
        selectedFilter,
        selectedAccountId,
        accountRepository.getAllAccounts()
    ) { args: Array<Any?> ->
        val transactions = args[0] as List<com.bitflow.finance.domain.model.Activity>
        val categories = args[1] as List<com.bitflow.finance.domain.model.Category>
        val currency = args[2] as String
        val filter = args[3] as TimeFilter
        val accountId = args[4] as Long?
        val accounts = args[5] as List<com.bitflow.finance.domain.model.Account>

            // Apply date filter
            val dateRange = getDateRangeForFilter(filter)
            var filteredTransactions = if (filter == TimeFilter.ALL || filter == TimeFilter.LAST_10) {
                transactions
            } else {
                transactions.filter { it.activityDate >= dateRange.first && it.activityDate <= dateRange.second }
            }
            
            // Apply account filter
            if (accountId != null) {
                filteredTransactions = filteredTransactions.filter { it.accountId == accountId }
            }
            
            val totalIncome = filteredTransactions
                .filter { it.type == ActivityType.INCOME }
                .sumOf { it.amount }
            val totalExpense = filteredTransactions
                .filter { it.type == ActivityType.EXPENSE }
                .sumOf { it.amount }

            // Calculate Category Breakdown
            val expenseTransactions = filteredTransactions.filter { it.type == ActivityType.EXPENSE }
            val categoryMap = categories.associateBy { it.id }
            
            val breakdown = expenseTransactions
                .groupBy { it.categoryId }
                .map { (catId, txns) ->
                    val amount = txns.sumOf { it.amount }
                    val category = categoryMap[catId]
                    CategoryBreakdown(
                        categoryName = category?.name ?: "Uncategorized",
                        icon = category?.icon ?: "📁",
                        amount = amount,
                        percentage = if (totalExpense > 0) (amount / totalExpense).toFloat() else 0f,
                        color = Color.Gray // Placeholder, UI will assign colors
                    )
                }
                .sortedByDescending { it.amount }

            // Prepare Chart Data (Keep existing logic for now if needed, or remove if replacing with Donut)
            // The prompt asks for Donut Chart, so we might not need the bar chart data anymore.
            // But let's keep it just in case or for a secondary view.
            
            AnalysisUiState(
                totalIncome = totalIncome,
                totalExpense = totalExpense,
                netSavings = totalIncome - totalExpense,
                categoryBreakdown = breakdown,
                currencySymbol = currency,
                accounts = accounts,
                selectedAccountId = accountId,
                transactionCount = filteredTransactions.size
            )
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = AnalysisUiState()
        )
    
    fun loadAnalysis(filter: TimeFilter) {
        selectedFilter.value = filter
    }
    
    fun setAccountFilter(accountId: Long?) {
        selectedAccountId.value = accountId
    }
}

data class AnalysisUiState(
    val totalIncome: Double = 0.0,
    val totalExpense: Double = 0.0,
    val netSavings: Double = 0.0,
    val categoryBreakdown: List<CategoryBreakdown> = emptyList(),
    val currencySymbol: String = "₹",
    val accounts: List<com.bitflow.finance.domain.model.Account> = emptyList(),
    val selectedAccountId: Long? = null,
    val transactionCount: Int = 0
)

data class CategoryBreakdown(
    val categoryName: String,
    val icon: String,
    val amount: Double,
    val percentage: Float,
    val color: Color
)
