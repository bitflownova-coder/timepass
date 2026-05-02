package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.local.dao.TransactionAuditDao
import com.bitflow.finance.data.local.entity.AuditAction
import com.bitflow.finance.data.local.entity.TransactionAuditLogEntity
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class AuditManagerUseCase @Inject constructor(
    private val auditDao: TransactionAuditDao,
    private val authRepository: AuthRepository
) {
    suspend fun logTransactionCreation(transaction: Activity) {
        val currentUser = authRepository.currentUserId.first()
        auditDao.insertLog(
            TransactionAuditLogEntity(
                transactionId = transaction.id,
                userId = currentUser,
                action = AuditAction.CREATE,
                fieldName = null,
                oldValue = null,
                newValue = "Transaction Created: ${transaction.amount} - ${transaction.description}"
            )
        )
    }

    suspend fun logTransactionDeletion(transaction: Activity) {
        val currentUser = authRepository.currentUserId.first()
        auditDao.insertLog(
            TransactionAuditLogEntity(
                transactionId = transaction.id,
                userId = currentUser,
                action = AuditAction.DELETE,
                fieldName = null,
                oldValue = "Deleted Transaction: ${transaction.amount} - ${transaction.description}",
                newValue = null
            )
        )
    }

    suspend fun logTransactionUpdate(oldTransaction: Activity, newTransaction: Activity) {
        val currentUser = authRepository.currentUserId.first()
        val transactionId = newTransaction.id

        if (oldTransaction.amount != newTransaction.amount) {
            auditDao.insertLog(
                TransactionAuditLogEntity(
                    transactionId = transactionId,
                    userId = currentUser,
                    action = AuditAction.UPDATE,
                    fieldName = "amount",
                    oldValue = oldTransaction.amount.toString(),
                    newValue = newTransaction.amount.toString()
                )
            )
        }

        if (oldTransaction.description != newTransaction.description) {
            auditDao.insertLog(
                TransactionAuditLogEntity(
                    transactionId = transactionId,
                    userId = currentUser,
                    action = AuditAction.UPDATE,
                    fieldName = "description",
                    oldValue = oldTransaction.description,
                    newValue = newTransaction.description
                )
            )
        }

        if (oldTransaction.activityDate != newTransaction.activityDate) {
            auditDao.insertLog(
                TransactionAuditLogEntity(
                    transactionId = transactionId,
                    userId = currentUser,
                    action = AuditAction.UPDATE,
                    fieldName = "date",
                    oldValue = oldTransaction.activityDate.toString(),
                    newValue = newTransaction.activityDate.toString()
                )
            )
        }
        
         if (oldTransaction.categoryId != newTransaction.categoryId) {
            auditDao.insertLog(
                TransactionAuditLogEntity(
                    transactionId = transactionId,
                    userId = currentUser,
                    action = AuditAction.UPDATE,
                    fieldName = "category",
                    oldValue = oldTransaction.categoryId.toString(),
                    newValue = newTransaction.categoryId.toString()
                )
            )
        }
    }

    fun getAuditLogs(transactionId: Long): Flow<List<TransactionAuditLogEntity>> {
        return auditDao.getLogsForTransaction(transactionId)
    }
}
