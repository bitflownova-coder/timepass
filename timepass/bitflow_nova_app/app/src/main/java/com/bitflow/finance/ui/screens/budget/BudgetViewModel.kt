package com.bitflow.finance.ui.screens.budget

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.CategoryDao
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.Calendar
import javax.inject.Inject

data class CategoryBudgetInfo(
    val categoryId: Long,
    val categoryName: String,
    val icon: String,
    val color: Int,
    val monthlyBudget: Double,
    val spent: Double,
    val progress: Float,
    val isOverBudget: Boolean,
    val isNearLimit: Boolean // 80%+ threshold
)

@HiltViewModel
class BudgetViewModel @Inject constructor(
    private val categoryDao: CategoryDao,
    private val transactionDao: TransactionDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    @OptIn(ExperimentalCoroutinesApi::class)
    val budgetedCategories: StateFlow<List<CategoryBudgetInfo>> = authRepository.currentUserId
        .filterNotNull()
        .flatMapLatest { userId ->
            categoryDao.getCategoriesWithBudget(userId).map { categories ->
                val startOfMonth = getStartOfMonth()
                val endOfMonth = getEndOfMonth()
                
                categories.mapNotNull { cat ->
                    val budget = cat.monthlyBudget ?: return@mapNotNull null
                    val spent = transactionDao.getTotalSpentInCategory(
                        categoryId = cat.id,
                        userId = userId,
                        startDate = startOfMonth,
                        endDate = endOfMonth
                    )
                    val progress = (spent / budget).toFloat().coerceIn(0f, 1f)
                    
                    CategoryBudgetInfo(
                        categoryId = cat.id,
                        categoryName = cat.name,
                        icon = cat.icon,
                        color = cat.color,
                        monthlyBudget = budget,
                        spent = spent,
                        progress = progress,
                        isOverBudget = spent > budget,
                        isNearLimit = progress >= 0.8f
                    )
                }
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    @OptIn(ExperimentalCoroutinesApi::class)
    val allCategories = authRepository.currentUserId
        .filterNotNull()
        .flatMapLatest { userId ->
            categoryDao.getAllCategories(userId)
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun setBudget(categoryId: Long, budget: Double?) {
        viewModelScope.launch {
            categoryDao.updateBudget(categoryId, budget)
        }
    }

    private fun getStartOfMonth(): Long {
        return Calendar.getInstance().apply {
            set(Calendar.DAY_OF_MONTH, 1)
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.timeInMillis
    }

    private fun getEndOfMonth(): Long {
        return Calendar.getInstance().apply {
            set(Calendar.DAY_OF_MONTH, getActualMaximum(Calendar.DAY_OF_MONTH))
            set(Calendar.HOUR_OF_DAY, 23)
            set(Calendar.MINUTE, 59)
            set(Calendar.SECOND, 59)
            set(Calendar.MILLISECOND, 999)
        }.timeInMillis
    }
}
