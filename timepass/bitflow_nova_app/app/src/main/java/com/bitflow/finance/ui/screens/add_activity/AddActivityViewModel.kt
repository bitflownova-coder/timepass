package com.bitflow.finance.ui.screens.add_activity

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.usecase.AutoLearnCategoryUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

@HiltViewModel
class AddActivityViewModel @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val autoLearnUseCase: AutoLearnCategoryUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(AddActivityUiState())
    val uiState: StateFlow<AddActivityUiState> = _uiState.asStateFlow()

    init {
        loadCategories()
    }

    private fun loadCategories() {
        viewModelScope.launch {
            transactionRepository.getAllCategories().collect { categories ->
                // Sort by usage count (most used first) and take top 8
                val sortedCategories = categories
                    .filter { !it.isHidden }
                    .sortedWith(
                        compareByDescending<Category> { it.usageCount }
                            .thenByDescending { it.lastUsedAt ?: 0 }
                    )
                
                _uiState.value = _uiState.value.copy(
                    topCategories = sortedCategories.take(8),
                    allCategories = sortedCategories
                )
            }
        }
    }

    fun updateAmount(amount: String) {
        _uiState.value = _uiState.value.copy(amount = amount)
    }

    fun appendToAmount(digit: String) {
        val currentAmount = _uiState.value.amount
        
        // Prevent multiple decimals
        if (digit == "." && currentAmount.contains(".")) return
        
        // Prevent leading zeros (except for decimal)
        if (currentAmount == "0" && digit != ".") {
            _uiState.value = _uiState.value.copy(amount = digit)
            return
        }
        
        _uiState.value = _uiState.value.copy(amount = currentAmount + digit)
    }

    fun removeLastDigit() {
        val currentAmount = _uiState.value.amount
        if (currentAmount.isNotEmpty()) {
            _uiState.value = _uiState.value.copy(
                amount = currentAmount.dropLast(1)
            )
        }
    }

    fun toggleActivityType() {
        val newType = when (_uiState.value.activityType) {
            ActivityType.EXPENSE -> ActivityType.INCOME
            ActivityType.INCOME -> ActivityType.EXPENSE
            ActivityType.TRANSFER -> ActivityType.EXPENSE
        }
        _uiState.value = _uiState.value.copy(activityType = newType)
    }

    fun selectCategory(category: Category) {
        _uiState.value = _uiState.value.copy(selectedCategoryId = category.id)
    }

    fun updateNote(note: String) {
        _uiState.value = _uiState.value.copy(note = note)
        
        // Phase 4: Auto-predict category when user enters merchant name
        if (note.isNotBlank() && _uiState.value.selectedCategoryId == null) {
            predictCategoryFromNote(note)
        }
    }
    
    /**
     * Phase 4: Invisible Intelligence - Predict category from note/merchant name
     */
    private fun predictCategoryFromNote(merchantName: String) {
        viewModelScope.launch {
            val suggestion = autoLearnUseCase.suggestCategory(merchantName)
            if (suggestion != null && suggestion.second >= 0.7f) {
                // High confidence - auto-select category
                _uiState.value = _uiState.value.copy(
                    selectedCategoryId = suggestion.first,
                    isAutoCategorized = true
                )
            }
        }
    }

    fun showDatePicker() {
        // TODO: Implement date picker dialog
    }

    fun showAllCategories() {
        _uiState.value = _uiState.value.copy(showAllCategoriesDialog = true)
    }

    fun dismissAllCategories() {
        _uiState.value = _uiState.value.copy(showAllCategoriesDialog = false)
    }

    fun saveActivity() {
        val state = _uiState.value
        val amount = state.amount.toDoubleOrNull() ?: return
        val categoryId = state.selectedCategoryId ?: return

        viewModelScope.launch {
            val merchantName = extractMerchantName(state.note)
            
            val activity = Activity(
                accountId = 1L, // TODO: Get from selected account
                activityDate = state.activityDate,
                valueDate = state.activityDate,
                description = merchantName.ifEmpty { state.note.ifEmpty { "Manual entry" } },
                reference = null,
                amount = amount,
                type = state.activityType,
                categoryId = categoryId,
                notes = state.note.ifEmpty { null },
                isAutoCategorized = state.isAutoCategorized
            )

            transactionRepository.insertTransaction(activity)
            
            // Update category usage count
            transactionRepository.incrementCategoryUsage(categoryId)
            
            // Phase 4: Learn from user's manual category selection
            if (!state.isAutoCategorized && merchantName.isNotBlank()) {
                autoLearnUseCase.learnFromUserCorrection(
                    activity = activity,
                    oldCategoryId = null,
                    newCategoryId = categoryId
                )
            }
            
            _uiState.value = _uiState.value.copy(isActivitySaved = true)
        }
    }
    
    /**
     * Extract merchant name from note for learning
     */
    private fun extractMerchantName(note: String): String {
        return note.trim().take(50).ifEmpty { "" }
    }
}

data class AddActivityUiState(
    val amount: String = "",
    val activityType: ActivityType = ActivityType.EXPENSE,
    val selectedCategoryId: Long? = null,
    val note: String = "",
    val activityDate: LocalDate = LocalDate.now(),
    val topCategories: List<Category> = emptyList(),
    val allCategories: List<Category> = emptyList(),
    val showAllCategoriesDialog: Boolean = false,
    val isActivitySaved: Boolean = false,
    val currencySymbol: String = "₹",
    val isAutoCategorized: Boolean = false // Track if AI suggested the category
)
