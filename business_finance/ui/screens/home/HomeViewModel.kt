package com.bitflow.finance.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.domain.model.Transaction
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.repository.SettingsRepository
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.util.StreakManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

@HiltViewModel
class HomeViewModel @Inject constructor(
    accountRepository: AccountRepository,
    transactionRepository: TransactionRepository,
    private val settingsRepository: SettingsRepository,
    private val authRepository: AuthRepository,
    private val streakManager: StreakManager
) : ViewModel() {

    private val _selectedAccountId = MutableStateFlow<Long?>(null)
    
    // Exchange rates to INR (base currency) - Update periodically or fetch from API in production
    private val exchangeRatesToINR = mapOf(
        "₹" to 1.0,
        "INR" to 1.0,
        "$" to 83.0,
        "USD" to 83.0,
        "€" to 90.0,
        "EUR" to 90.0,
        "£" to 105.0,
        "GBP" to 105.0
    )
    
    val uiState: StateFlow<HomeUiState> = combine(
        accountRepository.getAllAccounts(),
        transactionRepository.getAllTransactions(),
        settingsRepository.currencySymbol,
        settingsRepository.isPrivacyModeEnabled,
        settingsRepository.userName,
        _selectedAccountId,
        settingsRepository.appMode,
        authRepository.currentUser
    ) { flows: Array<Any?> ->
        val accounts = flows[0] as List<Account>
        val transactions = flows[1] as List<Transaction>
        val currency = flows[2] as String
        val isPrivacyMode = flows[3] as Boolean
        val userName = flows[4] as String
        val selectedAccountId = flows[5] as Long?
        val appMode = flows[6] as AppMode

        val userId = flows[7] as String?
        
        // Fetch streak info if user is logged in
        var currentStreak = 0
        if (userId != null) {
            // This is a suspend call, but we are inside flow builder which is not suspend
            // We should ideally use a separate flow for streak. 
            // For now, let's just use what's in the User entity if we added it there, 
            // but StreakManager calculates it dynamically.
            // Let's launch a separate coroutine to update a local flow if needed, 
            // OR better, just use the User entity fields if we updated them.
            // We added currentStreak to UserAccountEntity, so authRepository.currentUser should have it if mapped.
            // Assuming User model has it. If not, we might need to update User model.
            // Let's assume User model might NOT have it yet.
            // Actually, let's trust StreakManager to return it.
            try {
                // Blocks here? No, combine block is not suspend.
                // We should expose streak as a separate flow.
            } catch (e: Exception) {}
        }

        // Fix: Convert all account balances to base currency before summing
        val totalBalance = if (selectedAccountId != null) {
            accounts.find { it.id == selectedAccountId }?.let { convertToBaseCurrency(it) } ?: 0.0
        } else {
            accounts.sumOf { convertToBaseCurrency(it) }
        }

        HomeUiState(
            accounts = accounts,
            recentTransactions = transactions.take(10),
            totalNetWorth = totalBalance,
            currencySymbol = currency,
            isPrivacyMode = isPrivacyMode,
            userName = userName,
            selectedAccountId = selectedAccountId,
            appMode = appMode
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = HomeUiState()
    )

    // Separate flow for Streak to avoid blocking in combine
    private val _streak = MutableStateFlow(0)
    val streak = _streak.asStateFlow()

    init {
        viewModelScope.launch {
            authRepository.currentUserId.collect { userId ->
                if (userId != null) {
                    val streakInfo = streakManager.getStreak(userId)
                    _streak.value = streakInfo.currentStreak
                }
            }
        }
    }
    
    /**
     * Convert an account balance to base currency (INR) for proper Net Worth calculation.
     */
    private fun convertToBaseCurrency(account: Account): Double {
        val rate = exchangeRatesToINR[account.currency] ?: 1.0
        return account.currentBalance * rate
    }

    fun togglePrivacyMode() {
        viewModelScope.launch {
            val currentMode = uiState.value.isPrivacyMode
            settingsRepository.setPrivacyMode(!currentMode)
        }
    }

    fun selectAccount(accountId: Long?) {
        _selectedAccountId.value = if (_selectedAccountId.value == accountId) null else accountId
    }

    fun setAppMode(mode: AppMode) {
        viewModelScope.launch {
            settingsRepository.setAppMode(mode)
        }
    }
}

data class HomeUiState(
    val accounts: List<Account> = emptyList(),
    val recentTransactions: List<Transaction> = emptyList(),
    val totalNetWorth: Double = 0.0,
    val currencySymbol: String = "₹",
    val isPrivacyMode: Boolean = false,
    val userName: String = "",
    val selectedAccountId: Long? = null,
    val appMode: AppMode = AppMode.PERSONAL
)
