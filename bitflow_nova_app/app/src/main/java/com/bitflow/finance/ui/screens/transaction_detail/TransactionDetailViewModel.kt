package com.bitflow.finance.ui.screens.transaction_detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.model.CategoryLearningRule
import com.bitflow.finance.domain.repository.TransactionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TransactionDetailUiState(
    val isLoading: Boolean = false,
    val transaction: Activity? = null,
    val linkedGoal: com.bitflow.finance.domain.model.SavingsGoal? = null,
    val categories: List<Category> = emptyList(),
    val error: String? = null,
    val showLearningPrompt: Boolean = false,
    val learningPromptMessage: String = "",
    val auditLogs: List<com.bitflow.finance.data.local.entity.TransactionAuditLogEntity> = emptyList()
)

@HiltViewModel
class TransactionDetailViewModel @Inject constructor(
    private val repository: TransactionRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val transactionId: Long = checkNotNull(savedStateHandle["transactionId"])

    private val _uiState = MutableStateFlow(TransactionDetailUiState(isLoading = true))
    val uiState: StateFlow<TransactionDetailUiState> = _uiState.asStateFlow()

    private var pendingRuleDescription: String? = null
    private var pendingRuleCategoryId: Long? = null
    
    // Inject Dao
    @Inject lateinit var savingsGoalDao: com.bitflow.finance.data.local.dao.SavingsGoalDao
    @Inject lateinit var authRepository: com.bitflow.finance.domain.repository.AuthRepository

    init {
        loadData()
    }

    private fun loadData() {
        viewModelScope.launch {
            try {
                val transaction = repository.getTransactionById(transactionId)
                
                 // Fetch linked goal if exists
                 var linkedGoal: com.bitflow.finance.domain.model.SavingsGoal? = null
                 if (transaction?.linkedGoalId != null) {
                     val userId = authRepository.currentUserId.first()
                     val goalEntity = savingsGoalDao.getGoalById(transaction.linkedGoalId, userId)
                     if (goalEntity != null) {
                         linkedGoal = com.bitflow.finance.domain.model.SavingsGoal(
                             id = goalEntity.id,
                             name = goalEntity.name,
                             targetAmount = goalEntity.targetAmount,
                             currentAmount = goalEntity.currentAmount,
                             deadline = goalEntity.deadline,
                             iconEmoji = goalEntity.iconEmoji,
                             colorHex = goalEntity.colorHex,
                             isCompleted = goalEntity.isCompleted
                         )
                     }
                 }
                
                val auditLogs = repository.getAuditLogs(transactionId).first()

                repository.getAllCategories().collect { categories ->
                    _uiState.value = _uiState.value.copy(
                        transaction = transaction,
                        linkedGoal = linkedGoal,
                        categories = categories.filter { !it.isHidden },
                        isLoading = false,
                        auditLogs = auditLogs
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(isLoading = false, error = e.message)
            }
        }
    }

    fun updateBillPhoto(uri: String?) {
        val currentTransaction = _uiState.value.transaction ?: return
        viewModelScope.launch {
            try {
                val finalUri = if (uri.isNullOrBlank()) null else uri
                val updatedTransaction = currentTransaction.copy(billPhotoUri = finalUri)
                repository.updateTransaction(updatedTransaction)
                _uiState.value = _uiState.value.copy(transaction = updatedTransaction)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "Failed to update transaction: ${e.message}")
            }
        }
    }

    fun updateCategory(category: Category) {
        val currentTransaction = _uiState.value.transaction ?: return
        viewModelScope.launch {
            try {
                val updatedTransaction = currentTransaction.copy(categoryId = category.id)
                repository.updateTransaction(updatedTransaction)
                _uiState.value = _uiState.value.copy(transaction = updatedTransaction)

                // Check for auto-learning opportunity
                checkLearningOpportunity(currentTransaction.description, category)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "Failed to update category: ${e.message}")
            }
        }
    }

    private suspend fun checkLearningOpportunity(description: String, category: Category) {
        // Simple heuristic: use the first word or the whole description if short
        // For now, let's use the whole description as the pattern
        val pattern = description.trim()
        
        if (pattern.isBlank()) return

        val existingRule = repository.findLearningRule(pattern)
        if (existingRule == null) {
            pendingRuleDescription = pattern
            pendingRuleCategoryId = category.id
            _uiState.value = _uiState.value.copy(
                showLearningPrompt = true,
                learningPromptMessage = "Always categorize '$pattern' as '${category.name}'?"
            )
        }
    }

    fun confirmLearningRule() {
        val description = pendingRuleDescription ?: return
        val categoryId = pendingRuleCategoryId ?: return

        viewModelScope.launch {
            val rule = CategoryLearningRule(
                descriptionPattern = description,
                categoryId = categoryId,
                confidenceScore = 1.0f
            )
            repository.insertLearningRule(rule)
            dismissLearningRule()
        }
    }

    fun dismissLearningRule() {
        _uiState.value = _uiState.value.copy(showLearningPrompt = false)
        pendingRuleDescription = null
        pendingRuleCategoryId = null
    }
}
