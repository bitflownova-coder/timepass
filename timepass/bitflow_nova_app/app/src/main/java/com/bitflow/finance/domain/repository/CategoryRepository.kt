package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.entity.CategoryEntity
import kotlinx.coroutines.flow.Flow

interface CategoryRepository {
    fun getCategoriesStream(userId: String): Flow<List<CategoryEntity>>
}
