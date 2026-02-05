package com.bitflow.finance.ui.screens.accounts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.model.AccountType
import com.bitflow.finance.domain.repository.AccountRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.bitflow.finance.domain.repository.SettingsRepository
import com.bitflow.finance.domain.model.AppMode

@HiltViewModel
class AccountsViewModel @Inject constructor(
    private val accountRepository: AccountRepository,
    settingsRepository: SettingsRepository
) : ViewModel() {

    val currentMode = settingsRepository.appMode
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), AppMode.PERSONAL)

    val accounts = accountRepository.getAllAccounts()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addAccount(name: String, type: AccountType, initialBalance: Double, currency: String = "₹", context: AppMode) {
        viewModelScope.launch {
            accountRepository.insertAccount(
                Account(
                    name = name,
                    type = type,
                    color = 0, // Default color
                    icon = "", // Default icon
                    initialBalance = initialBalance,
                    currentBalance = initialBalance,
                    currency = currency,
                    context = context
                )
            )
        }
    }

    fun updateAccount(account: Account) {
        viewModelScope.launch {
            accountRepository.updateAccount(account)
        }
    }
}
