package com.bitflow.finance.ui.screens.split

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.SplitGroupEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.SplitRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SplitDashboardUiState(
    val groups: List<SplitGroupEntity> = emptyList(),
    val totalYouOwe: Double = 0.0,
    val totalYouAreOwed: Double = 0.0,
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class SplitDashboardViewModel @Inject constructor(
    private val splitRepository: SplitRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(SplitDashboardUiState(isLoading = true))
    val uiState: StateFlow<SplitDashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboard()
    }

    private fun loadDashboard() {
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            
            combine(
                splitRepository.getUserGroups(userId),
                splitRepository.getUserBalance(userId)
            ) { groups, balances ->
                // balances is Map<GroupId, Balance>
                // Positive balance means user is owed money
                // Negative balance means user owes money
                
                var totalOwe = 0.0
                var totalOwed = 0.0
                
                balances.values.forEach { balance ->
                    if (balance > 0) {
                        totalOwed += balance
                    } else {
                        totalOwe += Math.abs(balance)
                    }
                }
                
                SplitDashboardUiState(
                    groups = groups,
                    totalYouOwe = totalOwe,
                    totalYouAreOwed = totalOwed,
                    isLoading = false
                )
            }.catch { e ->
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "Unknown error"
                )
            }.collect { state ->
                _uiState.value = state
            }
        }
    }
    
    fun refresh() {
        loadDashboard()
    }
}
