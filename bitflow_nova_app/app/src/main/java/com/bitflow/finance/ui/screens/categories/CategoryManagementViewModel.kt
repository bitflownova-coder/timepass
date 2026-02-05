package com.bitflow.finance.ui.screens.categories

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.repository.TransactionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.bitflow.finance.domain.model.CategoryType

@HiltViewModel
class CategoryManagementViewModel @Inject constructor(
    private val transactionRepository: TransactionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(CategoryManagementUiState())
    val uiState: StateFlow<CategoryManagementUiState> = _uiState.asStateFlow()

    init {
        loadCategories()
    }

    private fun loadCategories() {
        viewModelScope.launch {
            transactionRepository.getAllCategories().collect { categories ->
                // Sort by usage count (most used first)
                val sortedCategories = categories.sortedWith(
                    compareByDescending<Category> { it.usageCount }
                        .thenByDescending { it.lastUsedAt ?: 0 }
                )
                
                _uiState.value = _uiState.value.copy(categories = sortedCategories)
            }
        }
    }

    fun showAddCategoryDialog() {
        _uiState.value = _uiState.value.copy(showAddEditDialog = true, categoryToEdit = null)
    }

    fun showEditDialog(category: Category) {
        _uiState.value = _uiState.value.copy(showAddEditDialog = true, categoryToEdit = category)
    }

    fun dismissAddEditDialog() {
        _uiState.value = _uiState.value.copy(showAddEditDialog = false, categoryToEdit = null)
    }

    fun saveCategory(name: String, icon: String, color: Int, type: CategoryType) {
        viewModelScope.launch {
            val currentEdit = _uiState.value.categoryToEdit
            if (currentEdit != null) {
                // Update
                transactionRepository.updateCategory(
                    currentEdit.copy(name = name, icon = icon, color = color, type = type)
                )
            } else {
                // Create
                transactionRepository.insertCategory(
                    Category(name = name, icon = icon, color = color, type = type)
                )
            }
            dismissAddEditDialog()
        }
    }

    fun showDeleteConfirmation(category: Category) {
        _uiState.value = _uiState.value.copy(
            showDeleteDialog = true,
            categoryToDelete = category
        )
    }

    fun dismissDeleteDialog() {
        _uiState.value = _uiState.value.copy(
            showDeleteDialog = false,
            categoryToDelete = null
        )
    }

    /**
     * Phase 5: Smart Delete with Merge Logic
     * "Don't Make Me Think" - Allow deletion of ANY category with data preservation
     */
    fun deleteCategoryWithMerge(categoryId: Long, targetMergeCategoryId: Long?) {
        viewModelScope.launch {
            if (targetMergeCategoryId != null) {
                // Merge: Move all activities to target category
                transactionRepository.mergeCategories(categoryId, targetMergeCategoryId)
            } else {
                // No merge target - move to "Uncategorized" (ID 0 or special category)
                transactionRepository.uncategorizeActivities(categoryId)
            }
            
            // Update any learning rules to point to new category
            // Note: This is handled inside mergeCategories() in the repository
            
            // Finally, delete the category itself
            transactionRepository.deleteCategory(categoryId)
            
            dismissDeleteDialog()
        }
    }
    
    fun deleteCategory(categoryId: Long, targetCategoryId: Long?) {
        // Wrapper for backward compatibility - calls the new method
        deleteCategoryWithMerge(categoryId, targetCategoryId)
    }

    fun toggleCategoryVisibility(category: Category) {
        viewModelScope.launch {
            transactionRepository.updateCategory(
                category.copy(isHidden = !category.isHidden)
            )
        }
    }
}

data class CategoryManagementUiState(
    val categories: List<Category> = emptyList(),
    val showDeleteDialog: Boolean = false,
    val categoryToDelete: Category? = null,
    val showAddEditDialog: Boolean = false,
    val categoryToEdit: Category? = null
)
