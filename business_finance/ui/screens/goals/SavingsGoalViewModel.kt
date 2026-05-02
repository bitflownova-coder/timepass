package com.bitflow.finance.ui.screens.goals

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.SavingsGoal
import com.bitflow.finance.domain.repository.SavingsGoalRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SavingsGoalViewModel @Inject constructor(
    private val repository: SavingsGoalRepository
) : ViewModel() {

    val activeGoals: StateFlow<List<SavingsGoal>> = repository.getActiveGoals()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val allGoals: StateFlow<List<SavingsGoal>> = repository.getAllGoals()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun createGoal(
        name: String,
        targetAmount: Double,
        deadline: Long? = null,
        iconEmoji: String = "🎯",
        colorHex: String = "#3B82F6"
    ) {
        viewModelScope.launch {
            repository.insertGoal(
                SavingsGoal(
                    name = name,
                    targetAmount = targetAmount,
                    deadline = deadline,
                    iconEmoji = iconEmoji,
                    colorHex = colorHex
                )
            )
        }
    }

    fun addContribution(goalId: Long, amount: Double) {
        viewModelScope.launch {
            repository.addContribution(goalId, amount)
        }
    }

    fun deleteGoal(goal: SavingsGoal) {
        viewModelScope.launch {
            repository.deleteGoal(goal)
        }
    }
}
