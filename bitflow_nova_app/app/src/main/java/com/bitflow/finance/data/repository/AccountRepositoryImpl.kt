package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.AccountDao
import com.bitflow.finance.data.local.entity.AccountEntity
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import com.bitflow.finance.domain.repository.SettingsRepository
import kotlinx.coroutines.flow.combine
import com.bitflow.finance.domain.model.AppMode

class AccountRepositoryImpl @Inject constructor(
    private val dao: AccountDao,
    private val authRepository: AuthRepository,
    private val settingsRepository: SettingsRepository
) : AccountRepository {

    override fun getAllAccounts(): Flow<List<Account>> {
        return combine(authRepository.currentUserId, settingsRepository.appMode) { userId, mode ->
            Pair(userId, mode)
        }.flatMapLatest { (userId, mode) ->
            dao.getAllAccounts(userId, mode).map { entities -> entities.map { it.toDomain() } }
        }
    }

    override suspend fun getAccountById(id: Long): Account? {
        val userId = authRepository.currentUserId.first()
        return dao.getAccountById(id, userId)?.toDomain()
    }

    override suspend fun insertAccount(account: Account): Long {
        val userId = authRepository.currentUserId.first()
        return dao.insertAccount(account.toEntity(userId))
    }

    override suspend fun updateAccount(account: Account) {
        val userId = authRepository.currentUserId.first()
        dao.updateAccount(account.toEntity(userId))
    }
    
    override suspend fun updateBalance(accountId: Long, newBalance: Double) {
        val userId = authRepository.currentUserId.first()
        dao.updateBalance(accountId, newBalance, userId)
    }

    private fun AccountEntity.toDomain(): Account {
        return Account(
            id = id,
            name = name,
            type = type,
            color = color,
            icon = icon,
            initialBalance = initialBalance,
            currentBalance = currentBalance,
            currency = currency,
            context = context
        )
    }

    private fun Account.toEntity(userId: String): AccountEntity {
        return AccountEntity(
            id = id,
            userId = userId,
            name = name,
            type = type,
            color = color,
            icon = icon,
            initialBalance = initialBalance,
            currentBalance = currentBalance,
            currency = currency,
            context = context
        )
    }
}
