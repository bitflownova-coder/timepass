package com.bitflow.finance.ui.screens.gst

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.Calendar
import javax.inject.Inject
import kotlinx.coroutines.flow.first

data class GstSummary(
    val quarter: String,
    val startDate: Long,
    val endDate: Long,
    val subtotal: Double = 0.0,
    val cgst: Double = 0.0,
    val sgst: Double = 0.0,
    val igst: Double = 0.0,
    val totalGst: Double = 0.0,
    val totalAmount: Double = 0.0,
    val tdsCollected: Double = 0.0
)

@HiltViewModel
class GstSummaryViewModel @Inject constructor(
    private val invoiceDao: InvoiceDao,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _currentQuarter = MutableStateFlow(getCurrentQuarter())
    val currentQuarter: StateFlow<String> = _currentQuarter.asStateFlow()

    private val _summary = MutableStateFlow(GstSummary("", 0, 0))
    val summary: StateFlow<GstSummary> = _summary.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadSummary()
    }

    fun selectQuarter(quarter: String) {
        _currentQuarter.value = quarter
        loadSummary()
    }

    private fun loadSummary() {
        viewModelScope.launch {
            val userId = authRepository.currentUserId.first()
            val (start, end) = getQuarterDateRange(_currentQuarter.value)
            
            _isLoading.value = true
            val subtotal = invoiceDao.getTotalSubtotal(userId, start, end)
            val cgst = invoiceDao.getTotalCgst(userId, start, end)
            val sgst = invoiceDao.getTotalSgst(userId, start, end)
            val igst = invoiceDao.getTotalIgst(userId, start, end)
            val totalAmount = invoiceDao.getTotalAmount(userId, start, end)
            val tds = invoiceDao.getTotalTds(userId, start, end)
            
            _summary.value = GstSummary(
                quarter = _currentQuarter.value,
                startDate = start,
                endDate = end,
                subtotal = subtotal,
                cgst = cgst,
                sgst = sgst,
                igst = igst,
                totalGst = cgst + sgst + igst,
                totalAmount = totalAmount,
                tdsCollected = tds
            )
            _isLoading.value = false
        }
    }

    fun getAvailableQuarters(): List<String> {
        val cal = Calendar.getInstance()
        val currentYear = cal.get(Calendar.YEAR)
        val quarters = mutableListOf<String>()
        
        // Current FY quarters
        for (q in 1..4) {
            quarters.add("Q$q ${currentYear}-${(currentYear + 1) % 100}")
        }
        // Previous FY quarters
        for (q in 1..4) {
            quarters.add("Q$q ${currentYear - 1}-${currentYear % 100}")
        }
        return quarters
    }

    private fun getCurrentQuarter(): String {
        val cal = Calendar.getInstance()
        val month = cal.get(Calendar.MONTH)
        val year = cal.get(Calendar.YEAR)
        
        // Indian FY: April-March
        return when (month) {
            in 0..2 -> "Q4 ${year - 1}-${year % 100}" // Jan-Mar
            in 3..5 -> "Q1 $year-${(year + 1) % 100}" // Apr-Jun
            in 6..8 -> "Q2 $year-${(year + 1) % 100}" // Jul-Sep
            else -> "Q3 $year-${(year + 1) % 100}" // Oct-Dec
        }
    }

    private fun getQuarterDateRange(quarter: String): Pair<Long, Long> {
        val parts = quarter.split(" ")
        val q = parts[0].removePrefix("Q").toInt()
        val yearParts = parts[1].split("-")
        val startYear = yearParts[0].toInt()
        
        val cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        
        val (startMonth, endMonth, yearOffset) = when (q) {
            1 -> Triple(Calendar.APRIL, Calendar.JUNE, 0)
            2 -> Triple(Calendar.JULY, Calendar.SEPTEMBER, 0)
            3 -> Triple(Calendar.OCTOBER, Calendar.DECEMBER, 0)
            else -> Triple(Calendar.JANUARY, Calendar.MARCH, 1)
        }
        
        cal.set(Calendar.YEAR, startYear + yearOffset)
        cal.set(Calendar.MONTH, startMonth)
        cal.set(Calendar.DAY_OF_MONTH, 1)
        val start = cal.timeInMillis
        
        cal.set(Calendar.MONTH, endMonth)
        cal.set(Calendar.DAY_OF_MONTH, cal.getActualMaximum(Calendar.DAY_OF_MONTH))
        cal.set(Calendar.HOUR_OF_DAY, 23)
        cal.set(Calendar.MINUTE, 59)
        cal.set(Calendar.SECOND, 59)
        val end = cal.timeInMillis
        
        return Pair(start, end)
    }
}
