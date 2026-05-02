package com.bitflow.finance.ui.screens.bills

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.BillReminder
import com.bitflow.finance.domain.repository.BillReminderRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class BillReminderViewModel @Inject constructor(
    private val repository: BillReminderRepository
) : ViewModel() {

    val reminders: StateFlow<List<BillReminder>> = repository.getActiveReminders()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun createReminder(
        name: String,
        amount: Double,
        dueDay: Int,
        reminderDaysBefore: Int = 3
    ) {
        viewModelScope.launch {
            repository.insertReminder(
                BillReminder(
                    name = name,
                    amount = amount,
                    dueDay = dueDay,
                    reminderDaysBefore = reminderDaysBefore
                )
            )
        }
    }

    fun deleteReminder(reminder: BillReminder) {
        viewModelScope.launch {
            repository.deleteReminder(reminder)
        }
    }

    fun toggleActive(reminder: BillReminder) {
        viewModelScope.launch {
            repository.setActive(reminder.id, !reminder.isActive)
        }
    }
}
