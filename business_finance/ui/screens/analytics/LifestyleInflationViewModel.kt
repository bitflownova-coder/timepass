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
import javax.inject.Inject
import kotlinx.coroutines.flow.first

data class InflationAnalysis(
    val recentAverage: Double,      // Last 6 months average
    val previousAverage: Double,    // Previous 6 months average
    val percentageChange: Double,
    val monthlyData: List<MonthlySpending>,
    val alertLevel: AlertLevel
)

data class MonthlySpending(
    val month: String,
    val amount: Double,
    val isRecent: Boolean
)

enum class AlertLevel {
    SAFE,       // < 10% increase
    WARNING,    // 10-20% increase
    DANGER      // > 20% increase
}

@HiltViewModel
class LifestyleInflationViewModel @Inject constructor(
    private val transactionDao: TransactionDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _analysis = MutableStateFlow<InflationAnalysis?>(null)
    val analysis: StateFlow<InflationAnalysis?> = _analysis.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadAnalysis()
    }

    private fun loadAnalysis() {
        // val userId = authRepository.currentUserId.value ?: return

        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            _isLoading.value = true
            
            val today = LocalDate.now()
            val monthlyData = mutableListOf<MonthlySpending>()
            
            // Get spending for last 12 months
            for (i in 11 downTo 0) {
                val monthStart = today.minusMonths(i.toLong()).withDayOfMonth(1)
                val monthEnd = monthStart.plusMonths(1).minusDays(1)
                
                val transactions = transactionDao.getTransactionsInPeriod(
                    monthStart, monthEnd, userId, AppMode.PERSONAL
                ).first()
                
                val spending = transactions
                    .filter { it.direction.name == "EXPENSE" }
                    .sumOf { it.amount }
                
                monthlyData.add(
                    MonthlySpending(
                        month = monthStart.month.name.take(3),
                        amount = spending,
                        isRecent = i < 6
                    )
                )
            }
            
            // Calculate averages
            val recentMonths = monthlyData.filter { it.isRecent }
            val previousMonths = monthlyData.filter { !it.isRecent }
            
            val recentAverage = if (recentMonths.isNotEmpty()) 
                recentMonths.sumOf { it.amount } / recentMonths.size else 0.0
            val previousAverage = if (previousMonths.isNotEmpty()) 
                previousMonths.sumOf { it.amount } / previousMonths.size else 0.0
            
            val percentageChange = if (previousAverage > 0) {
                ((recentAverage - previousAverage) / previousAverage) * 100
            } else 0.0
            
            val alertLevel = when {
                percentageChange > 20 -> AlertLevel.DANGER
                percentageChange > 10 -> AlertLevel.WARNING
                else -> AlertLevel.SAFE
            }
            
            _analysis.value = InflationAnalysis(
                recentAverage = recentAverage,
                previousAverage = previousAverage,
                percentageChange = percentageChange,
                monthlyData = monthlyData,
                alertLevel = alertLevel
            )
            
            _isLoading.value = false
        }
    }
}
