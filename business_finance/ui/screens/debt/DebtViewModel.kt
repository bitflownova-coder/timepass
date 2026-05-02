package com.bitflow.finance.ui.screens.debt

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.DebtEntity
import com.bitflow.finance.data.local.entity.DebtStrategy
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.DebtRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DebtUiState(
    val debts: List<DebtEntity> = emptyList(),
    val totalDebt: Double = 0.0,
    val totalMinimumMonthlyPayment: Double = 0.0,
    val payoffDateSnowball: String = "", // Estimated
    val payoffDateAvalanche: String = "", // Estimated
    val showAddDialog: Boolean = false,
    val extraPayment: Double = 0.0 // User input for simulation
)

@HiltViewModel
class DebtViewModel @Inject constructor(
    private val debtRepository: DebtRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(DebtUiState())
    val uiState: StateFlow<DebtUiState> = _uiState.asStateFlow()

    init {
        loadDebts()
    }

    private fun loadDebts() {
        viewModelScope.launch {
            debtRepository.getDebts().collect { debts ->
                val totalDebt = debts.sumOf { it.currentBalance }
                val totalMin = debts.sumOf { it.minimumPayment }
                
                // Sort based on global strategy or individually?
                // For simulator, we assume user follows one strategy for all.
                // Let's just store the list and let UI/Logic sort it.
                
                _uiState.value = _uiState.value.copy(
                    debts = debts,
                    totalDebt = totalDebt,
                    totalMinimumMonthlyPayment = totalMin
                )
                calculatePayoff()
            }
        }
    }

    fun addDebt(name: String, balance: Double, rate: Double, minPay: Double, dueDay: Int) {
        viewModelScope.launch {
            val userId = authRepository.currentUser.first() ?: return@launch
            val newDebt = DebtEntity(
                userId = userId,
                name = name,
                currentBalance = balance,
                interestRate = rate,
                minimumPayment = minPay,
                dueDay = dueDay
            )
            debtRepository.insertDebt(newDebt)
        }
    }
    
    fun deleteDebt(debt: DebtEntity) {
        viewModelScope.launch {
            debtRepository.deleteDebt(debt)
        }
    }

    fun updateExtraPayment(amount: Double) {
        _uiState.value = _uiState.value.copy(extraPayment = amount)
        calculatePayoff()
    }

    fun toggleAddDialog(show: Boolean) {
        _uiState.value = _uiState.value.copy(showAddDialog = show)
    }

    private fun calculatePayoff() {
        // Simple payoff calculation logic placeholder
        // TODO: Implement full amortization schedule calculation
        _uiState.value = _uiState.value.copy(
            payoffDateSnowball = "Calculating...",
            payoffDateAvalanche = "Calculating..."
        )
    }
}
