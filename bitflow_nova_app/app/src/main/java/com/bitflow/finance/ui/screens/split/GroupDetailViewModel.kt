package com.bitflow.finance.ui.screens.split

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.SplitExpenseEntity
import com.bitflow.finance.data.local.entity.SplitGroupEntity
import com.bitflow.finance.data.local.entity.SplitGroupMemberEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.SplitRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class GroupDetailUiState(
    val group: SplitGroupEntity? = null,
    val members: List<SplitGroupMemberEntity> = emptyList(),
    val expenses: List<SplitExpenseEntity> = emptyList(),
    val currentUserBalance: Double = 0.0, // Amount user owes (<0) or is owed (>0) in this group
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class GroupDetailViewModel @Inject constructor(
    private val splitRepository: SplitRepository,
    private val authRepository: AuthRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val groupId: String = checkNotNull(savedStateHandle["groupId"])

    private val _uiState = MutableStateFlow(GroupDetailUiState(isLoading = true))
    val uiState: StateFlow<GroupDetailUiState> = _uiState.asStateFlow()

    init {
        loadGroupDetails()
    }

    private fun loadGroupDetails() {
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            
            combine(
                splitRepository.getGroupDetails(groupId),
                splitRepository.getGroupMembers(groupId),
                splitRepository.getGroupExpenses(groupId)
            ) { group, members, expenses ->
                
                // Calculate balance for this group
                val balance = splitRepository.getGroupBalance(groupId, userId)
                val netBalance = (balance?.owedAmount ?: 0.0) - (balance?.owingAmount ?: 0.0)
                
                GroupDetailUiState(
                    group = group,
                    members = members,
                    expenses = expenses,
                    currentUserBalance = netBalance,
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
    
    fun settleUp() {
        // TODO: Implement settle up logic (mark shares as paid)
    }
}
