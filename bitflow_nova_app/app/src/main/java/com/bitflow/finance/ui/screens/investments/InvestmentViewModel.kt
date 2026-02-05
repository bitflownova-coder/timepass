package com.bitflow.finance.ui.screens.investments

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.AssetType
import com.bitflow.finance.data.local.entity.HoldingEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.InvestmentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

data class InvestmentUiState(
    val holdings: List<HoldingEntity> = emptyList(),
    val totalInvested: Double = 0.0,
    val totalCurrentValue: Double = 0.0,
    val totalProfitLoss: Double = 0.0,
    val returnsPercentage: Double = 0.0,
    val showAddDialog: Boolean = false
)

@HiltViewModel
class InvestmentViewModel @Inject constructor(
    private val investmentRepository: InvestmentRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(InvestmentUiState())
    val uiState: StateFlow<InvestmentUiState> = _uiState.asStateFlow()

    init {
        loadHoldings()
    }

    private fun loadHoldings() {
        viewModelScope.launch {
            investmentRepository.getHoldings().collect { holdings ->
                val totalInvested = holdings.sumOf { it.totalInvested }
                val totalCurrentValue = holdings.sumOf { it.currentValue }
                val totalProfitLoss = totalCurrentValue - totalInvested
                val returnsPercentage = if (totalInvested > 0) (totalProfitLoss / totalInvested) * 100 else 0.0

                _uiState.value = _uiState.value.copy(
                    holdings = holdings,
                    totalInvested = totalInvested,
                    totalCurrentValue = totalCurrentValue,
                    totalProfitLoss = totalProfitLoss,
                    returnsPercentage = returnsPercentage
                )
            }
        }
    }

    fun addHolding(name: String, type: AssetType, quantity: Double, avgPrice: Double, marketPrice: Double) {
        viewModelScope.launch {
            val userId = authRepository.currentUser.first() ?: return@launch
            val newHolding = HoldingEntity(
                userId = userId,
                name = name,
                type = type,
                quantity = quantity,
                averageBuyPrice = avgPrice,
                currentMarketPrice = marketPrice
            )
            investmentRepository.insertHolding(newHolding)
        }
    }

    fun deleteHolding(holding: HoldingEntity) {
        viewModelScope.launch {
            investmentRepository.deleteHolding(holding)
        }
    }

    fun toggleAddDialog(show: Boolean) {
        _uiState.value = _uiState.value.copy(showAddDialog = show)
    }
}
