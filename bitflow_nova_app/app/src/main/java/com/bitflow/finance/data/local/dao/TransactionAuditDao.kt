package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import com.bitflow.finance.data.local.entity.TransactionAuditLogEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TransactionAuditDao {
    @Insert
    suspend fun insertLog(log: TransactionAuditLogEntity)

    @Query("SELECT * FROM transaction_audit_logs WHERE transactionId = :transactionId ORDER BY timestamp DESC")
    fun getLogsForTransaction(transactionId: Long): Flow<List<TransactionAuditLogEntity>>
    
    @Query("DELETE FROM transaction_audit_logs WHERE transactionId = :transactionId")
    suspend fun deleteLogsForTransaction(transactionId: Long)

    @Query("SELECT * FROM transaction_audit_logs")
    suspend fun getAllLogsRaw(): List<TransactionAuditLogEntity>
}
