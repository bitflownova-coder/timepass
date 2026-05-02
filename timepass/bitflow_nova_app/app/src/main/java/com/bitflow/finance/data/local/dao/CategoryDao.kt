package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bitflow.finance.data.local.entity.CategoryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CategoryDao {
    @Query("SELECT * FROM categories WHERE (userId IS NULL OR userId = :userId) AND isHidden = 0 ORDER BY usageCount DESC, name ASC")
    fun getAllCategories(userId: String): Flow<List<CategoryEntity>>
    
    @Query("SELECT * FROM categories WHERE (userId IS NULL OR userId = :userId) AND isHidden = 0 ORDER BY usageCount DESC LIMIT :limit")
    fun getTopCategories(limit: Int = 8, userId: String): Flow<List<CategoryEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategory(category: CategoryEntity): Long
    
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertCategories(categories: List<CategoryEntity>)
    
    @Query("UPDATE categories SET usageCount = usageCount + 1 WHERE id = :categoryId")
    suspend fun incrementUsageCount(categoryId: Long)
    
    @Query("UPDATE categories SET isHidden = :isHidden WHERE id = :categoryId AND (userId IS NULL OR userId = :userId)")
    suspend fun updateVisibility(categoryId: Long, isHidden: Boolean, userId: String)
    
    @Query("DELETE FROM categories WHERE id = :categoryId AND userId = :userId AND isUserDeletable = 1")
    suspend fun deleteCategory(categoryId: Long, userId: String)
    
    @Query("SELECT * FROM categories WHERE id = :categoryId AND (userId IS NULL OR userId = :userId)")
    suspend fun getCategoryById(categoryId: Long, userId: String): CategoryEntity?
    
    @Query("SELECT * FROM categories WHERE (userId IS NULL OR userId = :userId) AND isHidden = 0 AND monthlyBudget IS NOT NULL ORDER BY name ASC")
    fun getCategoriesWithBudget(userId: String): Flow<List<CategoryEntity>>
    
    @Query("UPDATE categories SET monthlyBudget = :budget WHERE id = :categoryId")
    suspend fun updateBudget(categoryId: Long, budget: Double?)
    @Query("SELECT * FROM categories")
    suspend fun getAllCategoriesRaw(): List<CategoryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategoryRaw(category: CategoryEntity)
}
