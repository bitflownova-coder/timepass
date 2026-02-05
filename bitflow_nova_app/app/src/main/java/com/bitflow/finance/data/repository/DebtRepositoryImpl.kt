package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.DebtDao
import com.bitflow.finance.data.local.entity.DebtEntity
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.DebtRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import javax.inject.Inject

class DebtRepositoryImpl @Inject constructor(
    private val debtDao: DebtDao,
    private val authRepository: AuthRepository
) : DebtRepository {

    override fun getDebts(): Flow<List<DebtEntity>> {
        return authRepository.currentUser
            .flatMapLatest { userId ->
                if (userId != null) {
                    debtDao.getDebts(userId)
                } else {
                    flowOf(emptyList())
                }
            }
    }

    override suspend fun insertDebt(debt: DebtEntity) {
        debtDao.insertDebt(debt)
    }

    override suspend fun deleteDebt(debt: DebtEntity) {
        debtDao.deleteDebt(debt)
    }

    override suspend fun updateDebt(debt: DebtEntity) {
        debtDao.updateDebt(debt)
    }
}
