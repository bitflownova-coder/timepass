package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.HoldingDao
import com.bitflow.finance.data.local.entity.HoldingEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.InvestmentRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import javax.inject.Inject

class InvestmentRepositoryImpl @Inject constructor(
    private val holdingDao: HoldingDao,
    private val authRepository: AuthRepository
) : InvestmentRepository {

    override fun getHoldings(): Flow<List<HoldingEntity>> {
        return authRepository.currentUser.flatMapLatest { userId ->
            if (userId != null) {
                holdingDao.getHoldings(userId)
            } else {
                flowOf(emptyList())
            }
        }
    }

    override fun getTotalPortfolioValue(): Flow<Double?> {
        return authRepository.currentUser.flatMapLatest { userId ->
            if (userId != null) {
                holdingDao.getTotalPortfolioValue(userId)
            } else {
                flowOf(0.0)
            }
        }
    }

    override suspend fun insertHolding(holding: HoldingEntity) {
        holdingDao.insertHolding(holding)
    }

    override suspend fun deleteHolding(holding: HoldingEntity) {
        holdingDao.deleteHolding(holding)
    }

    override suspend fun updateHolding(holding: HoldingEntity) {
        holdingDao.updateHolding(holding)
    }
}
