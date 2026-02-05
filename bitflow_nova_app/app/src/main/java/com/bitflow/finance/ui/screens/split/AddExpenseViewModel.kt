package com.bitflow.finance.ui.screens.split

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.SplitGroupMemberEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.SplitRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AddExpenseUiState(
    val members: List<SplitGroupMemberEntity> = emptyList(),
    val selectedMemberIds: Set<String> = emptySet(), // Who to split with
    val description: String = "",
    val amount: String = "",
    val paidByUserId: String = "", // Default to current user
    val isSaving: Boolean = false,
    val isSaved: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AddExpenseViewModel @Inject constructor(
    private val splitRepository: SplitRepository,
    private val authRepository: AuthRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val groupId: String = checkNotNull(savedStateHandle["groupId"])
    private var currentUserId: String = ""

    private val _uiState = MutableStateFlow(AddExpenseUiState())
    val uiState: StateFlow<AddExpenseUiState> = _uiState.asStateFlow()

    init {
        loadMembers()
    }

    private fun loadMembers() {
        viewModelScope.launch {
            currentUserId = authRepository.currentUserId.first() ?: return@launch
            
            // Set default payer to current user
            _uiState.update { it.copy(paidByUserId = currentUserId) }
            
            splitRepository.getGroupMembers(groupId).collect { members ->
                _uiState.update { 
                    it.copy(
                        members = members,
                        // Default split with everyone
                        selectedMemberIds = members.map { m -> m.userId }.toSet()
                    ) 
                }
            }
        }
    }

    fun onDescriptionChange(value: String) {
        _uiState.update { it.copy(description = value) }
    }

    fun onAmountChange(value: String) {
        _uiState.update { it.copy(amount = value) }
    }

    fun toggleMemberSelection(userId: String) {
        _uiState.update { state ->
            val newSelection = state.selectedMemberIds.toMutableSet()
            if (newSelection.contains(userId)) {
                if (newSelection.size > 1) newSelection.remove(userId) // Prevent empty selection
            } else {
                newSelection.add(userId)
            }
            state.copy(selectedMemberIds = newSelection)
        }
    }

    fun saveExpense() {
        val state = _uiState.value
        val amountVal = state.amount.toDoubleOrNull()
        
        if (state.description.isBlank()) {
            _uiState.update { it.copy(error = "Enter description") }
            return
        }
        if (amountVal == null || amountVal <= 0) {
            _uiState.update { it.copy(error = "Enter valid amount") }
            return
        }
        
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, error = null) }
            
            val result = splitRepository.addExpense(
                groupId = groupId,
                description = state.description,
                totalAmount = amountVal,
                paidBy = state.paidByUserId,
                memberUserIds = state.selectedMemberIds.toList()
            )
            
            result.onSuccess {
                _uiState.update { it.copy(isSaving = false, isSaved = true) }
            }.onFailure { e ->
                _uiState.update { it.copy(isSaving = false, error = e.message ?: "Failed to save") }
            }
        }
    }
}
