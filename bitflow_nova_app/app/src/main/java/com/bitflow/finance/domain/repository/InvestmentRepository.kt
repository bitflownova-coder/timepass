package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.entity.HoldingEntity
import kotlinx.coroutines.flow.Flow

interface InvestmentRepository {
    fun getHoldings(): Flow<List<HoldingEntity>>
    fun getTotalPortfolioValue(): Flow<Double?>
    suspend fun insertHolding(holding: HoldingEntity)
    suspend fun deleteHolding(holding: HoldingEntity)
    suspend fun updateHolding(holding: HoldingEntity)
}
