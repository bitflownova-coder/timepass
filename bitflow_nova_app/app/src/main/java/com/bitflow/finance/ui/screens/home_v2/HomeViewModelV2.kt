package com.bitflow.finance.ui.screens.home_v2

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.DailyPulse
import com.bitflow.finance.domain.model.PulseStatus
import com.bitflow.finance.domain.model.SubscriptionDetectionCard
import com.bitflow.finance.domain.repository.TransactionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalTime
import javax.inject.Inject

@HiltViewModel
class HomeViewModelV2 @Inject constructor(
    private val transactionRepository: TransactionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiStateV2())
    val uiState: StateFlow<HomeUiStateV2> = _uiState.asStateFlow()

    init {
        loadDashboardData()
    }

    private fun loadDashboardData() {
        viewModelScope.launch {
            // Load recent activities
            transactionRepository.getRecentTransactions(limit = 10).collect { activities ->
                _uiState.value = _uiState.value.copy(recentActivities = activities)
            }

            // Calculate Daily Pulse
            val dailyPulse = calculateDailyPulse()
            _uiState.value = _uiState.value.copy(dailyPulse = dailyPulse)

            // Load detected subscriptions
            val subscriptions = transactionRepository.getUnconfirmedSubscriptions()
            _uiState.value = _uiState.value.copy(detectedSubscriptions = subscriptions)

            // Set greeting
            val greeting = getGreeting()
            _uiState.value = _uiState.value.copy(greeting = greeting)
        }
    }

    private suspend fun calculateDailyPulse(): DailyPulse {
        // Simple logic: Calculate how much user can spend today based on:
        // 1. Monthly income
        // 2. Fixed expenses (subscriptions, bills)
        // 3. Savings goal (default 20%)
        // 4. Days remaining in month
        
        val monthlyIncome = transactionRepository.getMonthlyIncome()
        val fixedExpenses = transactionRepository.getMonthlyFixedExpenses()
        val savingsGoal = monthlyIncome * 0.20 // 20% savings
        
        val availableForSpending = monthlyIncome - fixedExpenses - savingsGoal
        val daysInMonth = 30 // Simplified
        val dailyBudget = availableForSpending / daysInMonth
        
        val todaySpent = transactionRepository.getTodayExpenses()
        val safeToSpend = (dailyBudget - todaySpent).coerceAtLeast(0.0)
        
        val progress = if (dailyBudget > 0) (todaySpent / dailyBudget).toFloat() else 0f
        
        val status = when {
            progress < 0.5f -> PulseStatus.GREAT
            progress < 0.75f -> PulseStatus.GOOD
            progress < 1.0f -> PulseStatus.CAUTION
            else -> PulseStatus.SLOW_DOWN
        }
        
        val message = when (status) {
            PulseStatus.GREAT -> "You can spend ₹${safeToSpend.toInt()} today and still save money"
            PulseStatus.GOOD -> "On track! ₹${safeToSpend.toInt()} left for today"
            PulseStatus.CAUTION -> "Getting close to your daily limit"
            PulseStatus.SLOW_DOWN -> "You've used your daily budget"
        }
        
        return DailyPulse(
            safeToSpendToday = safeToSpend,
            pulseStatus = status,
            message = message,
            progressPercentage = progress.coerceIn(0f, 1f)
        )
    }

    private fun getGreeting(): String {
        val hour = LocalTime.now().hour
        return when {
            hour < 12 -> "Good Morning"
            hour < 17 -> "Good Afternoon"
            else -> "Good Evening"
        }
    }

    fun togglePrivacyMode() {
        _uiState.value = _uiState.value.copy(isPrivacyMode = !_uiState.value.isPrivacyMode)
    }

    fun confirmSubscription(patternId: Long) {
        viewModelScope.launch {
            transactionRepository.confirmSubscription(patternId)
            // Reload subscriptions
            val subscriptions = transactionRepository.getUnconfirmedSubscriptions()
            _uiState.value = _uiState.value.copy(detectedSubscriptions = subscriptions)
        }
    }

    fun dismissSubscription(patternId: Long) {
        viewModelScope.launch {
            transactionRepository.dismissSubscription(patternId)
            // Reload subscriptions
            val subscriptions = transactionRepository.getUnconfirmedSubscriptions()
            _uiState.value = _uiState.value.copy(detectedSubscriptions = subscriptions)
        }
    }
}

data class HomeUiStateV2(
    val greeting: String = "Good Day",
    val userName: String = "User",
    val dailyPulse: DailyPulse = DailyPulse(
        safeToSpendToday = 0.0,
        pulseStatus = PulseStatus.GOOD,
        message = "",
        progressPercentage = 0f
    ),
    val recentActivities: List<Activity> = emptyList(),
    val detectedSubscriptions: List<SubscriptionDetectionCard> = emptyList(),
    val isPrivacyMode: Boolean = false,
    val currencySymbol: String = "₹"
)
