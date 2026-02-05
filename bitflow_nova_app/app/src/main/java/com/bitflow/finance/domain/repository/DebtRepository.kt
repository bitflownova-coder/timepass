package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.entity.DebtEntity
import kotlinx.coroutines.flow.Flow

interface DebtRepository {
    fun getDebts(): Flow<List<DebtEntity>>
    suspend fun insertDebt(debt: DebtEntity)
    suspend fun deleteDebt(debt: DebtEntity)
    suspend fun updateDebt(debt: DebtEntity)
}
