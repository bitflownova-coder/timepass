package com.bitflow.finance.ui.screens.tax

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject
import java.time.LocalDate

data class TaxHelperUiState(
    val totalTaxSavingInvestments: Double = 0.0,
    val limit: Double = 150000.0,
    val remainingLimit: Double = 150000.0,
    val progress: Float = 0f,
    val transactions: List<com.bitflow.finance.domain.model.Activity> = emptyList()
)

@HiltViewModel
class TaxHelperViewModel @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(TaxHelperUiState())
    val uiState: StateFlow<TaxHelperUiState> = _uiState.asStateFlow()

    init {
        loadTaxData()
    }

    private fun loadTaxData() {
        viewModelScope.launch {
            // Get transactions for current financial year
            // For India, April 1 to March 31
            val now = LocalDate.now()
            val currentYear = now.year
            val startYear = if (now.monthValue >= 4) currentYear else currentYear - 1
            val endYear = startYear + 1
            
            val startDate = LocalDate.of(startYear, 4, 1)
            val endDate = LocalDate.of(endYear, 3, 31)
            
            val limit = 150000.0
            
            transactionRepository.getTaxDeductibleTransactions(startDate, endDate).collect { transactions ->
                val totalInvested = transactions.sumOf { it.amount }
                val remaining = (limit - totalInvested).coerceAtLeast(0.0)
                val progress = (totalInvested / limit).toFloat().coerceIn(0f, 1f)
                
                _uiState.value = _uiState.value.copy(
                    totalTaxSavingInvestments = totalInvested,
                    remainingLimit = remaining,
                    progress = progress,
                    transactions = transactions
                )
            }
        }
    }
}
