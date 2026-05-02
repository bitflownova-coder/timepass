package com.bitflow.finance.ui.screens.templates

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.TransactionTemplateDao
import com.bitflow.finance.data.local.entity.TransactionTemplateEntity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TransactionTemplate(
    val id: Long = 0,
    val name: String,
    val amount: Double,
    val type: ActivityType,
    val categoryId: Long,
    val description: String = "",
    val context: AppMode = AppMode.PERSONAL,
    val icon: String = "💳"
)

@HiltViewModel
class TemplateViewModel @Inject constructor(
    private val templateDao: TransactionTemplateDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    @OptIn(ExperimentalCoroutinesApi::class)
    val templates: StateFlow<List<TransactionTemplateEntity>> = authRepository.currentUserId
        .filterNotNull()
        .flatMapLatest { userId ->
            templateDao.getAllTemplates(userId)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun createTemplate(
        name: String,
        amount: Double,
        type: ActivityType,
        categoryId: Long,
        description: String = "",
        icon: String = "💳"
    ) {

        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            templateDao.insertTemplate(
                TransactionTemplateEntity(
                    userId = userId,
                    name = name,
                    amount = amount,
                    type = type,
                    categoryId = categoryId,
                    description = description,
                    icon = icon
                )
            )
        }
    }

    fun deleteTemplate(template: TransactionTemplateEntity) {
        viewModelScope.launch {
            templateDao.deleteTemplate(template)
        }
    }
}
