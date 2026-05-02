package com.bitflow.finance.ui.screens.add_transaction

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.util.StreakManager
import com.bitflow.finance.util.VoiceInputHelper
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

@HiltViewModel
class AddTransactionViewModel @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val accountRepository: AccountRepository,
    private val streakManager: StreakManager,
    private val authRepository: AuthRepository,
    private val savingsGoalDao: com.bitflow.finance.data.local.dao.SavingsGoalDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(AddTransactionUiState())
    val uiState: StateFlow<AddTransactionUiState> = _uiState.asStateFlow()

    init {
        loadCategories()
        loadAccounts()
        loadSavingsGoals()
    }

    private fun loadCategories() {
        viewModelScope.launch {
            transactionRepository.getAllCategories().collect { categories ->
                _uiState.value = _uiState.value.copy(
                    categories = categories.filter { !it.isHidden }
                )
            }
        }
    }

    private fun loadAccounts() {
        viewModelScope.launch {
            accountRepository.getAllAccounts().collect { accounts ->
                _uiState.value = _uiState.value.copy(
                    accounts = accounts,
                    selectedAccount = accounts.firstOrNull()
                )
            }
        }
    }
    
    private fun loadSavingsGoals() {
        viewModelScope.launch {
            authRepository.currentUserId.collect { userId ->
                savingsGoalDao.getAllGoals(userId).collect { goals ->
                    // Convert Entity to Domain if needed, or if DAO returns Entity
                    // Since we don't have a Repository for Goals yet, using DAO directly
                    // Assuming DAO returns Entities, we map manually or use them if simple
                    // Let's assume DAO uses Entities, so we'll map them
                    val domainGoals = goals.map { 
                        com.bitflow.finance.domain.model.SavingsGoal(
                            id = it.id,
                            name = it.name,
                            targetAmount = it.targetAmount,
                            currentAmount = it.currentAmount,
                            deadline = it.deadline,
                            iconEmoji = it.iconEmoji,
                            colorHex = it.colorHex,
                            isCompleted = it.isCompleted
                        )
                    }
                    _uiState.value = _uiState.value.copy(savingsGoals = domainGoals)
                }
            }
        }
    }

    fun setType(type: ActivityType) {
        _uiState.value = _uiState.value.copy(type = type)
    }

    fun setAmount(amount: String) {
        _uiState.value = _uiState.value.copy(amount = amount)
    }

    fun selectCategory(category: Category) {
        _uiState.value = _uiState.value.copy(selectedCategory = category)
    }

    fun selectAccount(account: Account) {
        _uiState.value = _uiState.value.copy(selectedAccount = account)
    }
    
    fun selectGoal(goal: com.bitflow.finance.domain.model.SavingsGoal?) {
        _uiState.value = _uiState.value.copy(selectedGoal = goal)
    }

    fun setDescription(description: String) {
        _uiState.value = _uiState.value.copy(description = description)
    }

    fun setNotes(notes: String) {
        _uiState.value = _uiState.value.copy(notes = notes)
    }

    fun setBillPhoto(uri: String?) {
        _uiState.value = _uiState.value.copy(billPhotoUri = uri)
    }
    
    fun processVoiceInput(text: String) {
        val parsed = VoiceInputHelper.parseSpokenText(text)
        
        val updates = _uiState.value.copy(
            amount = parsed.amount?.toString() ?: _uiState.value.amount,
            description = parsed.description ?: text,
            type = if (parsed.isExpense) ActivityType.EXPENSE else ActivityType.INCOME
        )
        
        // Try to match category by name
        parsed.category?.let { categoryName ->
            val matchedCategory = _uiState.value.categories.find { 
                it.name.contains(categoryName, ignoreCase = true) 
            }
            if (matchedCategory != null) {
                _uiState.value = updates.copy(selectedCategory = matchedCategory)
            } else {
                _uiState.value = updates
            }
        } ?: run {
            _uiState.value = updates
        }
    }

    fun saveTransaction() {
        viewModelScope.launch {
            val state = _uiState.value
            val amountValue = state.amount.toDoubleOrNull() ?: return@launch
            val accountId = state.selectedAccount?.id ?: return@launch
            val userId = authRepository.currentUserId.first()

            val activity = Activity(
                accountId = accountId,
                activityDate = LocalDate.now(),
                valueDate = LocalDate.now(),
                description = state.description,
                reference = null,
                amount = amountValue,
                type = state.type,
                categoryId = state.selectedCategory?.id,
                tags = emptyList(),
                billPhotoUri = state.billPhotoUri,
                createdAt = java.time.LocalDateTime.now(),
                notes = state.notes,
                linkedGoalId = state.selectedGoal?.id
            )

            transactionRepository.insertTransaction(activity)
            
            // Phase 4: Intent-Based Finance - Auto-update Goal Amount
            if (state.selectedGoal != null) {
                if (state.type == ActivityType.INCOME || state.type == ActivityType.TRANSFER) {
                    // Contribution: Add to goal
                    savingsGoalDao.addContribution(state.selectedGoal.id, amountValue, userId)
                } else if (state.type == ActivityType.EXPENSE) {
                     // Expense linked to goal: Spending FROM the goal
                     // Should we subtract? Let's assume yes, using negative amount to 'addContribution'
                     savingsGoalDao.addContribution(state.selectedGoal.id, -amountValue, userId)
                }
            }
            
            // Update Streak
            streakManager.onTransactionLogged(userId)
            
            _uiState.value = _uiState.value.copy(saved = true)
        }
    }
}

data class AddTransactionUiState(
    val type: ActivityType = ActivityType.EXPENSE,
    val amount: String = "",
    val selectedCategory: Category? = null,
    val categories: List<Category> = emptyList(),
    val selectedAccount: Account? = null,
    val accounts: List<Account> = emptyList(),
    val selectedGoal: com.bitflow.finance.domain.model.SavingsGoal? = null,
    val savingsGoals: List<com.bitflow.finance.domain.model.SavingsGoal> = emptyList(),
    val description: String = "",
    val notes: String = "",
    val billPhotoUri: String? = null,
    val saved: Boolean = false,
    val showAccountSheet: Boolean = false,
    val showBillPhotoOptions: Boolean = false
)
