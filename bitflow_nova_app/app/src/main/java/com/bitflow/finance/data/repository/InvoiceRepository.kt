package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.data.local.entity.InvoiceEntity
import com.bitflow.finance.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InvoiceRepository @Inject constructor(
    private val invoiceDao: InvoiceDao,
    private val authRepository: AuthRepository
) {
    fun getAllInvoices(): Flow<List<InvoiceEntity>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            invoiceDao.getAllInvoices(userId)
        }
    }

    suspend fun getInvoiceById(id: Long): InvoiceEntity? {
        val userId = authRepository.currentUserId.first()
        return invoiceDao.getInvoiceById(id, userId)
    }

    suspend fun saveInvoice(invoice: InvoiceEntity): Long {
        val userId = authRepository.currentUserId.first()
        return invoiceDao.insertInvoice(invoice.copy(userId = userId))
    }

    suspend fun updateInvoice(invoice: InvoiceEntity) {
        invoiceDao.updateInvoice(invoice)
    }

    suspend fun deleteInvoice(id: Long) {
        val userId = authRepository.currentUserId.first()
        invoiceDao.deleteInvoice(id, userId)
    }
}
