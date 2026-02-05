package com.bitflow.finance.ui.screens.bitflow

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.repository.InvoiceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.model.ActivityType
import kotlinx.coroutines.flow.combine
import javax.inject.Inject

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

@HiltViewModel
class BitflowViewModel @Inject constructor(
    invoiceRepository: InvoiceRepository,
    transactionRepository: TransactionRepository
) : ViewModel() {

    val uiState: StateFlow<BitflowUiState> = combine(
        invoiceRepository.getAllInvoices(),
        transactionRepository.getAllTransactions()
    ) { invoices, transactions ->
            val totalRevenue = invoices.sumOf { it.amount }
            val paidAmount = invoices.filter { it.isPaid }.sumOf { it.amount }
            val unpaidAmount = invoices.filter { !it.isPaid }.sumOf { it.amount }
            val totalInvoices = invoices.size
            val paidInvoicesCount = invoices.count { it.isPaid }
            val unpaidInvoicesCount = invoices.count { !it.isPaid }

            // Calculate Business Expenses (filtered by repo context)
            val businessExpenses = transactions
                .filter { it.type == ActivityType.EXPENSE }
                .sumOf { it.amount }
                
            val netProfit = totalRevenue - businessExpenses

            // Calculate monthly revenue for the last 6 months
            val monthlyRevenue = invoices
                .groupBy { invoice ->
                    val date = Instant.ofEpochMilli(invoice.date)
                        .atZone(ZoneId.systemDefault())
                        .toLocalDate()
                    date.format(DateTimeFormatter.ofPattern("MMM", Locale.ENGLISH))
                }
                .mapValues { entry -> entry.value.sumOf { it.amount } }
                .toList()
                .sortedBy { 
                    // Simple sort by month index is tricky with just "MMM", 
                    // but for now let's just take the data as is or rely on the query order if it was time based.
                    // Since the query is ORDER BY date DESC, the list will be reverse chronological.
                    // We want chronological for the chart.
                    // Let's do it properly.
                    0 
                } 
            
            // Re-doing the monthly logic to ensure correct order
            val now = java.time.LocalDate.now()
            val last6Months = (0..5).map { i ->
                now.minusMonths(i.toLong())
            }.reversed()
            
            val chartData = last6Months.map { month ->
                val monthName = month.format(DateTimeFormatter.ofPattern("MMM", Locale.ENGLISH))
                val monthRevenue = invoices.filter { 
                    val invoiceDate = Instant.ofEpochMilli(it.date).atZone(ZoneId.systemDefault()).toLocalDate()
                    invoiceDate.month == month.month && invoiceDate.year == month.year
                }.sumOf { it.amount }
                monthName to monthRevenue.toFloat()
            }

            BitflowUiState(
                totalRevenue = totalRevenue,
                paidAmount = paidAmount,
                unpaidAmount = unpaidAmount,
                totalInvoices = totalInvoices,
                paidInvoicesCount = paidInvoicesCount,
                unpaidInvoicesCount = unpaidInvoicesCount,
                monthlyRevenue = chartData,
                totalExpenses = businessExpenses,
                netProfit = netProfit
            )
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = BitflowUiState()
        )
}

data class BitflowUiState(
    val totalRevenue: Double = 0.0,
    val paidAmount: Double = 0.0,
    val unpaidAmount: Double = 0.0,
    val totalInvoices: Int = 0,
    val paidInvoicesCount: Int = 0,
    val unpaidInvoicesCount: Int = 0,
    val monthlyRevenue: List<Pair<String, Float>> = emptyList(),
    val totalExpenses: Double = 0.0,
    val netProfit: Double = 0.0
)
