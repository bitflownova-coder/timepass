package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.DebtEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface DebtDao {
    @Query("SELECT * FROM debts WHERE userId = :userId")
    fun getDebts(userId: String): Flow<List<DebtEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDebt(debt: DebtEntity)

    @Delete
    suspend fun deleteDebt(debt: DebtEntity)
    
    @Update
    suspend fun updateDebt(debt: DebtEntity)
}
