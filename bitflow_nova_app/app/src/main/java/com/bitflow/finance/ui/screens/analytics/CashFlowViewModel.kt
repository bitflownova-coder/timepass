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
import java.time.temporal.ChronoUnit
import javax.inject.Inject
import kotlinx.coroutines.flow.first

data class CashFlowForecast(
    val currentBalance: Double,
    val projectedBalance: Double,
    val dailyIncome: Double,
    val dailyExpense: Double,
    val netDailyFlow: Double,
    val forecastDays: Int,
    val dataPoints: List<ForecastPoint>
)

data class ForecastPoint(
    val day: Int,
    val projectedBalance: Double
)

@HiltViewModel
class CashFlowViewModel @Inject constructor(
    private val transactionDao: TransactionDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _forecast = MutableStateFlow<CashFlowForecast?>(null)
    val forecast: StateFlow<CashFlowForecast?> = _forecast.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _forecastDays = MutableStateFlow(30)
    val forecastDays: StateFlow<Int> = _forecastDays.asStateFlow()

    init {
        loadForecast()
    }

    fun setForecastDays(days: Int) {
        _forecastDays.value = days
        loadForecast()
    }

    private fun loadForecast() {
        // val userId = authRepository.currentUserId.value ?: return
        
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            _isLoading.value = true
            
            val today = LocalDate.now()
            val thirtyDaysAgo = today.minusDays(30)
            
            // Get last 30 days of transactions to calculate averages
            val transactions = transactionDao.getTransactionsInPeriod(
                thirtyDaysAgo, today, userId, AppMode.PERSONAL
            ).first()
            
            // Calculate daily averages
            val totalIncome = transactions
                .filter { it.direction.name == "INCOME" }
                .sumOf { it.amount }
            val totalExpense = transactions
                .filter { it.direction.name == "EXPENSE" }
                .sumOf { it.amount }
            
            val daysAnalyzed = ChronoUnit.DAYS.between(thirtyDaysAgo, today).toInt().coerceAtLeast(1)
            val dailyIncome = totalIncome / daysAnalyzed
            val dailyExpense = totalExpense / daysAnalyzed
            val netDailyFlow = dailyIncome - dailyExpense
            
            // Get current balance (sum of all transactions)
            val allTransactions = transactionDao.getTransactionsInPeriod(
                LocalDate.of(2000, 1, 1), today, userId, AppMode.PERSONAL
            ).first()
            
            val currentBalance = allTransactions.sumOf { 
                if (it.direction.name == "INCOME") it.amount else -it.amount 
            }
            
            // Generate forecast data points
            val days = _forecastDays.value
            val dataPoints = (0..days).map { day ->
                ForecastPoint(
                    day = day,
                    projectedBalance = currentBalance + (netDailyFlow * day)
                )
            }
            
            _forecast.value = CashFlowForecast(
                currentBalance = currentBalance,
                projectedBalance = currentBalance + (netDailyFlow * days),
                dailyIncome = dailyIncome,
                dailyExpense = dailyExpense,
                netDailyFlow = netDailyFlow,
                forecastDays = days,
                dataPoints = dataPoints
            )
            
            _isLoading.value = false
        }
    }
}
