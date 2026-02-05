package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.AccountEntity
import kotlinx.coroutines.flow.Flow
import com.bitflow.finance.domain.model.AppMode

@Dao
interface AccountDao {
    @Query("SELECT * FROM accounts WHERE userId = :userId AND context = :context")
    fun getAllAccounts(userId: String, context: AppMode): Flow<List<AccountEntity>>

    @Query("SELECT * FROM accounts")
    fun getAllAccountsSync(): List<AccountEntity>

    @Query("SELECT * FROM accounts WHERE id = :id AND userId = :userId")
    suspend fun getAccountById(id: Long, userId: String): AccountEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAccount(account: AccountEntity): Long

    @Update
    suspend fun updateAccount(account: AccountEntity)
    
    @Query("UPDATE accounts SET currentBalance = :newBalance WHERE id = :accountId AND userId = :userId")
    suspend fun updateBalance(accountId: Long, newBalance: Double, userId: String)
}
