package com.bitflow.finance.ui.screens.reports

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.time.LocalDate
import java.util.Calendar
import java.util.Date
import java.util.Locale
import javax.inject.Inject

data class PnLStatement(
    val period: String,
    val revenue: Double,
    val cogs: Double, // Cost of Goods Sold
    val grossProfit: Double,
    val operatingExpenses: Double,
    val netProfit: Double,
    val invoiceCount: Int,
    val expenseCount: Int
)

@HiltViewModel
class PnLViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val invoiceDao: InvoiceDao,
    private val transactionDao: TransactionDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _statement = MutableStateFlow<PnLStatement?>(null)
    val statement: StateFlow<PnLStatement?> = _statement.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _selectedPeriod = MutableStateFlow("This Month")
    val selectedPeriod: StateFlow<String> = _selectedPeriod.asStateFlow()

    init {
        loadStatement()
    }

    fun selectPeriod(period: String) {
        _selectedPeriod.value = period
        loadStatement()
    }

    private fun loadStatement() {
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
        val (startDate, endDate) = getPeriodDates(_selectedPeriod.value)
        

            _isLoading.value = true
            
            // Get revenue from invoices
            val revenue = invoiceDao.getTotalAmount(userId, startDate, endDate)
            val invoices = invoiceDao.getInvoicesInPeriod(userId, startDate, endDate).first()
            
            // Get expenses from transactions
            val transactions = transactionDao.getTransactionsInPeriod(
                LocalDate.ofEpochDay(startDate / 86400000),
                LocalDate.ofEpochDay(endDate / 86400000),
                userId,
                AppMode.BUSINESS
            ).first()
            
            val expenses = transactions.filter { it.direction.name == "EXPENSE" }.sumOf { it.amount }
            
            _statement.value = PnLStatement(
                period = _selectedPeriod.value,
                revenue = revenue,
                cogs = 0.0, // Can be tracked separately if needed
                grossProfit = revenue,
                operatingExpenses = expenses,
                netProfit = revenue - expenses,
                invoiceCount = invoices.size,
                expenseCount = transactions.count { it.direction.name == "EXPENSE" }
            )
            _isLoading.value = false
        }
    }

    fun exportToPdf(): Intent? {
        val stmt = _statement.value ?: return null
        
        val document = PdfDocument()
        val pageInfo = PdfDocument.PageInfo.Builder(595, 842, 1).create() // A4
        val page = document.startPage(pageInfo)
        val canvas = page.canvas
        
        val titlePaint = Paint().apply {
            color = Color.BLACK
            textSize = 24f
            isFakeBoldText = true
        }
        val headerPaint = Paint().apply {
            color = Color.DKGRAY
            textSize = 16f
            isFakeBoldText = true
        }
        val textPaint = Paint().apply {
            color = Color.BLACK
            textSize = 14f
        }
        val valuePaint = Paint().apply {
            color = Color.BLACK
            textSize = 14f
            textAlign = Paint.Align.RIGHT
        }
        
        var y = 60f
        
        // Title
        canvas.drawText("Profit & Loss Statement", 50f, y, titlePaint)
        y += 30f
        canvas.drawText("Period: ${stmt.period}", 50f, y, textPaint)
        y += 10f
        canvas.drawText("Generated: ${SimpleDateFormat("dd MMM yyyy", Locale.getDefault()).format(Date())}", 50f, y, textPaint)
        y += 40f
        
        // Revenue Section
        canvas.drawText("REVENUE", 50f, y, headerPaint)
        y += 25f
        canvas.drawText("Invoice Revenue", 70f, y, textPaint)
        canvas.drawText("₹${"%,.2f".format(stmt.revenue)}", 545f, y, valuePaint)
        y += 20f
        canvas.drawLine(50f, y, 545f, y, textPaint)
        y += 25f
        canvas.drawText("Gross Profit", 50f, y, headerPaint)
        canvas.drawText("₹${"%,.2f".format(stmt.grossProfit)}", 545f, y, valuePaint)
        y += 40f
        
        // Expenses Section  
        canvas.drawText("OPERATING EXPENSES", 50f, y, headerPaint)
        y += 25f
        canvas.drawText("Business Expenses", 70f, y, textPaint)
        canvas.drawText("₹${"%,.2f".format(stmt.operatingExpenses)}", 545f, y, valuePaint)
        y += 20f
        canvas.drawLine(50f, y, 545f, y, textPaint)
        y += 25f
        
        // Net Profit
        val profitPaint = Paint().apply {
            color = if (stmt.netProfit >= 0) Color.parseColor("#10B981") else Color.RED
            textSize = 18f
            isFakeBoldText = true
        }
        val profitValuePaint = Paint().apply {
            color = if (stmt.netProfit >= 0) Color.parseColor("#10B981") else Color.RED
            textSize = 18f
            isFakeBoldText = true
            textAlign = Paint.Align.RIGHT
        }
        canvas.drawText("NET PROFIT", 50f, y, profitPaint)
        canvas.drawText("₹${"%,.2f".format(stmt.netProfit)}", 545f, y, profitValuePaint)
        
        document.finishPage(page)
        
        // Save PDF
        val file = File(context.cacheDir, "PnL_${System.currentTimeMillis()}.pdf")
        FileOutputStream(file).use { document.writeTo(it) }
        document.close()
        
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.provider", file)
        return Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/pdf")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    private fun getPeriodDates(period: String): Pair<Long, Long> {
        val cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        
        val end = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 23)
            set(Calendar.MINUTE, 59)
            set(Calendar.SECOND, 59)
        }.timeInMillis
        
        val start = when (period) {
            "This Month" -> {
                cal.set(Calendar.DAY_OF_MONTH, 1)
                cal.timeInMillis
            }
            "Last Month" -> {
                cal.add(Calendar.MONTH, -1)
                cal.set(Calendar.DAY_OF_MONTH, 1)
                cal.timeInMillis
            }
            "This Quarter" -> {
                val month = cal.get(Calendar.MONTH)
                cal.set(Calendar.MONTH, (month / 3) * 3)
                cal.set(Calendar.DAY_OF_MONTH, 1)
                cal.timeInMillis
            }
            "This Year" -> {
                cal.set(Calendar.MONTH, Calendar.JANUARY)
                cal.set(Calendar.DAY_OF_MONTH, 1)
                cal.timeInMillis
            }
            else -> cal.timeInMillis
        }
        
        return Pair(start, end)
    }

    fun getAvailablePeriods() = listOf("This Month", "Last Month", "This Quarter", "This Year")
}
