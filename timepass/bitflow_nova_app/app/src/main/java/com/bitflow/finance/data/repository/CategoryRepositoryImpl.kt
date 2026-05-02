package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.CategoryDao
import com.bitflow.finance.data.local.entity.CategoryEntity
import com.bitflow.finance.domain.repository.CategoryRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class CategoryRepositoryImpl @Inject constructor(
    private val categoryDao: CategoryDao
) : CategoryRepository {
    override fun getCategoriesStream(userId: String): Flow<List<CategoryEntity>> {
        return categoryDao.getAllCategories(userId)
    }
}
