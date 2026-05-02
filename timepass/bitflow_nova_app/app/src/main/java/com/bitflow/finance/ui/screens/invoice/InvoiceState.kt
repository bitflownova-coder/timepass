package com.bitflow.finance.ui.screens.invoice

import java.time.LocalDate
import java.time.format.DateTimeFormatter

data class InvoiceItem(
    val id: Long = System.currentTimeMillis(),
    val description: String = "",
    val subDescription: String = "",
    val quantity: Int = 1,
    val rate: Double = 0.0
) {
    val amount: Double get() = quantity * rate
}

data class InvoiceState(
    val invoiceNumber: String = "INV-2025-001",
    val date: LocalDate = LocalDate.now(),
    val dueDate: LocalDate = LocalDate.now().plusDays(15),
    val clientName: String = "Tagore Group of Institutions",
    val clientAddress: String = "Vandalur–Kelambakkam Road,\nRathinamangalam, Chennai – 600127\nTamil Nadu, India",
    val items: List<InvoiceItem> = listOf(
        InvoiceItem(description = "Bitflow Nova Enterprise License", subDescription = "Per Student Annual Subscription", quantity = 3500, rate = 1200.0)
    ),
    val taxRate: Double = 18.0
) {
    val subtotal: Double get() = items.sumOf { it.amount }
    val taxAmount: Double get() = subtotal * (taxRate / 100)
    val grandTotal: Double get() = subtotal + taxAmount
    
    val formattedDate: String get() = date.format(DateTimeFormatter.ISO_DATE)
    val formattedDueDate: String get() = dueDate.format(DateTimeFormatter.ISO_DATE)
}
