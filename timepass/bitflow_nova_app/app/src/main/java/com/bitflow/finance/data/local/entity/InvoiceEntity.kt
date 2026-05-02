package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "invoices")
data class InvoiceEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String, // Owner of this invoice
    val invoiceNumber: String,
    val clientName: String,
    val clientAddress: String = "",
    val clientGstin: String = "", // Client's GSTIN
    val date: Long, // Timestamp
    val dueDate: Long = 0,
    val itemsJson: String = "[]",
    val subtotal: Double = 0.0, // Base amount before tax
    val taxRate: Double = 0.0, // GST rate (5, 12, 18, 28%)
    val cgst: Double = 0.0, // Central GST
    val sgst: Double = 0.0, // State GST (intrastate)
    val igst: Double = 0.0, // Integrated GST (interstate)
    val tdsRate: Double = 0.0, // TDS rate (usually 1%, 2%, 10%)
    val tdsAmount: Double = 0.0, // TDS deducted
    val amount: Double, // Final amount after tax
    val isPaid: Boolean = false,
    val pdfPath: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)
