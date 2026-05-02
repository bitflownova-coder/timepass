package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.bitflow.finance.data.local.entity.InvoiceEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface InvoiceDao {
    @Query("SELECT * FROM invoices WHERE userId = :userId ORDER BY date DESC")
    fun getAllInvoices(userId: String): Flow<List<InvoiceEntity>>

    @Query("SELECT * FROM invoices WHERE id = :id AND userId = :userId")
    suspend fun getInvoiceById(id: Long, userId: String): InvoiceEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertInvoice(invoice: InvoiceEntity): Long

    @androidx.room.Update
    suspend fun updateInvoice(invoice: InvoiceEntity)

    @Query("DELETE FROM invoices WHERE id = :id AND userId = :userId")
    suspend fun deleteInvoice(id: Long, userId: String)
    
    // GST Summary queries
    @Query("SELECT COALESCE(SUM(cgst), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalCgst(userId: String, startDate: Long, endDate: Long): Double
    
    @Query("SELECT COALESCE(SUM(sgst), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalSgst(userId: String, startDate: Long, endDate: Long): Double
    
    @Query("SELECT COALESCE(SUM(igst), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalIgst(userId: String, startDate: Long, endDate: Long): Double
    
    @Query("SELECT COALESCE(SUM(subtotal), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalSubtotal(userId: String, startDate: Long, endDate: Long): Double
    
    @Query("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalAmount(userId: String, startDate: Long, endDate: Long): Double
    
    // TDS Summary
    @Query("SELECT COALESCE(SUM(tdsAmount), 0) FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate")
    suspend fun getTotalTds(userId: String, startDate: Long, endDate: Long): Double
    
    @Query("SELECT * FROM invoices WHERE userId = :userId AND date BETWEEN :startDate AND :endDate ORDER BY date DESC")
    fun getInvoicesInPeriod(userId: String, startDate: Long, endDate: Long): Flow<List<InvoiceEntity>>
}
