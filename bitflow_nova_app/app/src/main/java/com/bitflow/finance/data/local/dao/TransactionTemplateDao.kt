package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bitflow.finance.data.local.entity.TransactionTemplateEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TransactionTemplateDao {
    
    @Query("SELECT * FROM transaction_templates WHERE userId = :userId ORDER BY createdAt DESC")
    fun getAllTemplates(userId: String): Flow<List<TransactionTemplateEntity>>
    
    @Query("SELECT * FROM transaction_templates WHERE id = :id AND userId = :userId")
    suspend fun getTemplateById(id: Long, userId: String): TransactionTemplateEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTemplate(template: TransactionTemplateEntity): Long
    
    @Delete
    suspend fun deleteTemplate(template: TransactionTemplateEntity)
}
