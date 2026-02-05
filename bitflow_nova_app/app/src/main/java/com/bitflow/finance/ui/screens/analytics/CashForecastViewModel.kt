package com.bitflow.finance.ui.screens.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.usecase.CashForecastUseCase
import com.bitflow.finance.domain.usecase.DailyBalanceProjection
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

data class CashForecastUiState(
    val projections: List<DailyBalanceProjection> = emptyList(),
    val minBalance: Double = 0.0,
    val maxBalance: Double = 0.0,
    val lowBalanceDate: LocalDate? = null,
    val daysUntilLowBalance: Int? = null,
    val isLoading: Boolean = true,
    val safeToSpendDaily: Double = 0.0
)

@HiltViewModel
class CashForecastViewModel @Inject constructor(
    private val cashForecastUseCase: CashForecastUseCase,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(CashForecastUiState())
    val uiState: StateFlow<CashForecastUiState> = _uiState.asStateFlow()

    init {
        loadForecast()
    }

    private fun loadForecast() {
        viewModelScope.launch {
            authRepository.currentUserId.flatMapLatest { userId ->
                if (userId != null) {
                    cashForecastUseCase(userId, daysToProject = 30)
                } else {
                    flowOf(emptyList())
                }
            }.collect { projections ->
                if (projections.isNotEmpty()) {
                    val minBalance = projections.minOf { it.endingBalance }
                    val maxBalance = projections.maxOf { it.endingBalance }
                    
                    // Simple "Low Balance" threshold (hardcoded 5000 for now, should be setting)
                    val LOW_BALANCE_THRESHOLD = 5000.0
                    val firstLowDate = projections.firstOrNull { it.endingBalance < LOW_BALANCE_THRESHOLD }?.date
                    val daysUntil = firstLowDate?.let { 
                        java.time.temporal.ChronoUnit.DAYS.between(LocalDate.now(), it).toInt() 
                    }

                    // Safe to Spend: (MinBalance - Threshold) / 30 ?? 
                    // Or more conservatively: Using logic from "DailyPulse"
                    // If minBalance > Threshold, surplus = minBalance - Threshold.
                    // Safe daily = surplus / 30.
                    val surplus = (minBalance - LOW_BALANCE_THRESHOLD).coerceAtLeast(0.0)
                    val safeDaily = surplus / 30.0

                    _uiState.value = CashForecastUiState(
                        projections = projections,
                        minBalance = minBalance,
                        maxBalance = maxBalance,
                        lowBalanceDate = firstLowDate,
                        daysUntilLowBalance = daysUntil,
                        safeToSpendDaily = safeDaily,
                        isLoading = false
                    )
                } else {
                     _uiState.value = _uiState.value.copy(isLoading = false)
                }
            }
        }
    }
}
