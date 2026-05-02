package com.bitflow.finance.ui.screens.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.YearMonth
import javax.inject.Inject
import kotlinx.coroutines.flow.first

data class HeatmapData(
    val month: YearMonth,
    val days: List<DaySpending>,
    val maxSpending: Double,
    val totalSpending: Double
)

data class DaySpending(
    val date: LocalDate,
    val amount: Double,
    val intensity: Float // 0.0 to 1.0
)

@HiltViewModel
class SpendingHeatmapViewModel @Inject constructor(
    private val transactionDao: TransactionDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _heatmapData = MutableStateFlow<HeatmapData?>(null)
    val heatmapData: StateFlow<HeatmapData?> = _heatmapData.asStateFlow()

    private val _selectedMonth = MutableStateFlow(YearMonth.now())
    val selectedMonth: StateFlow<YearMonth> = _selectedMonth.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadHeatmap()
    }

    fun previousMonth() {
        _selectedMonth.value = _selectedMonth.value.minusMonths(1)
        loadHeatmap()
    }

    fun nextMonth() {
        _selectedMonth.value = _selectedMonth.value.plusMonths(1)
        loadHeatmap()
    }

    private fun loadHeatmap() {
        // val userId = authRepository.currentUserId.value ?: return

        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            _isLoading.value = true
            
            val month = _selectedMonth.value
            val startDate = month.atDay(1)
            val endDate = month.atEndOfMonth()
            
            val transactions = transactionDao.getTransactionsInPeriod(
                startDate, endDate, userId, AppMode.PERSONAL
            ).first()
            
            // Group by date and sum expenses
            val dailySpending = transactions
                .filter { it.direction.name == "EXPENSE" }
                .groupBy { it.txnDate }
                .mapValues { (_, txns) -> txns.sumOf { it.amount } }
            
            val maxSpending = dailySpending.values.maxOrNull() ?: 1.0
            val totalSpending = dailySpending.values.sum()
            
            // Build day list for the month
            val days = (1..month.lengthOfMonth()).map { day ->
                val date = month.atDay(day)
                val amount = dailySpending[date] ?: 0.0
                val intensity = if (maxSpending > 0) (amount / maxSpending).toFloat() else 0f
                
                DaySpending(
                    date = date,
                    amount = amount,
                    intensity = intensity
                )
            }
            
            _heatmapData.value = HeatmapData(
                month = month,
                days = days,
                maxSpending = maxSpending,
                totalSpending = totalSpending
            )
            
            _isLoading.value = false
        }
    }
}
