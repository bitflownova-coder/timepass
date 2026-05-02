package com.bitflow.finance.ui.screens.simple_finance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.ClientDiscussionEntity
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import com.bitflow.finance.data.local.dao.MonthlyTotal
import com.bitflow.finance.data.local.dao.CategoryTotal
import com.bitflow.finance.data.repository.SimpleFinanceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SimpleFinanceViewModel @Inject constructor(
    private val repository: SimpleFinanceRepository
) : ViewModel() {
    
    // Current user ID - in real app, get from auth
    private val userId = "local_user"
    
    // ================== UI STATE ==================
    private val _uiState = MutableStateFlow(SimpleFinanceUiState())
    val uiState: StateFlow<SimpleFinanceUiState> = _uiState.asStateFlow()
    
    // ================== DATA FLOWS ==================
    val clients: StateFlow<List<ClientEntity>> = repository.getAllClients(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val discussions: StateFlow<List<ClientDiscussionEntity>> = repository.getAllDiscussions(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val pendingDiscussions: StateFlow<List<ClientDiscussionEntity>> = repository.getDiscussionsByStatus("pending", userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val incomePayments: StateFlow<List<IncomePaymentEntity>> = repository.getAllPayments(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val expenses: StateFlow<List<ExpenseRecordEntity>> = repository.getAllExpenses(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val subscriptions: StateFlow<List<ExpenseRecordEntity>> = repository.getSubscriptions(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val totalIncome: StateFlow<Double> = repository.getTotalIncome(userId)
        .map { it ?: 0.0 }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)
    
    val totalExpenses: StateFlow<Double> = repository.getTotalExpenses(userId)
        .map { it ?: 0.0 }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)
    
    val pendingTotal: StateFlow<Double> = repository.getPendingTotal(userId)
        .map { it ?: 0.0 }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)
    
    val monthlyIncome: StateFlow<List<MonthlyTotal>> = repository.getMonthlyIncome(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val monthlyExpenses: StateFlow<List<MonthlyTotal>> = repository.getMonthlyExpenses(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val expensesByCategory: StateFlow<List<CategoryTotal>> = repository.getExpensesByCategories(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val paymentsWithoutInvoice: StateFlow<List<IncomePaymentEntity>> = repository.getPaymentsWithoutInvoice(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    val expensesWithoutBill: StateFlow<List<ExpenseRecordEntity>> = repository.getExpensesWithoutBill(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    
    // ================== CLIENT OPERATIONS ==================
    fun addClient(name: String, email: String = "", phone: String = "", address: String = "", gstin: String = "") {
        viewModelScope.launch {
            val client = ClientEntity(
                userId = userId,
                name = name,
                email = email,
                phone = phone,
                address = address,
                gstin = gstin
            )
            repository.insertClient(client)
        }
    }
    
    fun updateClient(client: ClientEntity) {
        viewModelScope.launch {
            repository.updateClient(client)
        }
    }
    
    fun deleteClient(client: ClientEntity) {
        viewModelScope.launch {
            repository.deleteClient(client)
        }
    }
    
    // ================== DISCUSSION OPERATIONS ==================
    fun addDiscussion(
        clientId: Long,
        title: String,
        description: String = "",
        expectedAmount: Double
    ) {
        viewModelScope.launch {
            val discussion = ClientDiscussionEntity(
                userId = userId,
                clientId = clientId,
                title = title,
                description = description,
                expectedAmount = expectedAmount
            )
            repository.insertDiscussion(discussion)
        }
    }
    
    fun updateDiscussionAmount(discussionId: Long, newAmount: Double, notes: String) {
        viewModelScope.launch {
            repository.updateDiscussionAmount(discussionId, newAmount, notes)
        }
    }
    
    fun updateDiscussionStatus(discussionId: Long, status: String) {
        viewModelScope.launch {
            repository.updateDiscussionStatus(discussionId, status)
        }
    }
    
    fun revertDiscussion(discussionId: Long) {
        viewModelScope.launch {
            // Delete the associated payment first
            repository.deletePaymentByDiscussionId(discussionId, userId)
            // Then revert status to pending
            repository.updateDiscussionStatus(discussionId, "pending")
        }
    }
    
    fun convertToPayment(discussion: ClientDiscussionEntity, paymentMode: String = "bank", reference: String = "") {
        viewModelScope.launch {
            repository.convertDiscussionToPayment(discussion, userId, paymentMode, reference)
        }
    }
    
    fun deleteDiscussion(discussion: ClientDiscussionEntity) {
        viewModelScope.launch {
            repository.deleteDiscussion(discussion)
        }
    }
    
    // ================== INCOME OPERATIONS ==================
    fun addIncome(
        amount: Double,
        description: String,
        clientId: Long? = null,
        paymentMode: String = "bank",
        reference: String = ""
    ) {
        viewModelScope.launch {
            val payment = IncomePaymentEntity(
                userId = userId,
                clientId = clientId,
                amount = amount,
                description = description,
                paymentMode = paymentMode,
                reference = reference
            )
            repository.insertPayment(payment)
        }
    }
    
    fun deleteIncome(payment: IncomePaymentEntity) {
        viewModelScope.launch {
            repository.deletePayment(payment)
        }
    }
    
    suspend fun getPaymentForInvoice(paymentId: Long): IncomePaymentEntity? {
        return repository.getPaymentById(paymentId, userId)
    }
    
    suspend fun getClientForPayment(clientId: Long): ClientEntity? {
        return repository.getClientById(clientId, userId)
    }
    
    fun markInvoiceGenerated(paymentId: Long, invoiceNumber: String, invoiceId: Long) {
        viewModelScope.launch {
            repository.markInvoiceGenerated(paymentId, invoiceNumber, invoiceId)
        }
    }
    
    // ================== EXPENSE OPERATIONS ==================
    fun addExpense(
        amount: Double,
        description: String,
        reason: String,
        expenseType: String,
        category: String,
        paymentMode: String = "bank",
        vendor: String = "",
        isRecurring: Boolean = false,
        recurringPeriod: String? = null,
        nextDueDate: Long? = null
    ) {
        viewModelScope.launch {
            val expense = ExpenseRecordEntity(
                userId = userId,
                amount = amount,
                description = description,
                reason = reason,
                expenseType = expenseType,
                category = category,
                paymentMode = paymentMode,
                vendor = vendor,
                isRecurring = isRecurring,
                recurringPeriod = recurringPeriod,
                nextDueDate = nextDueDate
            )
            repository.insertExpense(expense)
        }
    }
    
    fun updateExpense(expense: ExpenseRecordEntity) {
        viewModelScope.launch {
            repository.updateExpense(expense)
        }
    }
    
    fun deleteExpense(expense: ExpenseRecordEntity) {
        viewModelScope.launch {
            repository.deleteExpense(expense)
        }
    }
    
    fun attachBillToExpense(expenseId: Long, billPath: String) {
        viewModelScope.launch {
            repository.attachBill(expenseId, billPath)
        }
    }
    
    // Get discussions for a specific client
    fun getDiscussionsForClient(clientId: Long): Flow<List<ClientDiscussionEntity>> {
        return repository.getDiscussionsByClient(clientId, userId)
    }
    
    // Get payments for a specific client
    fun getPaymentsForClient(clientId: Long): Flow<List<IncomePaymentEntity>> {
        return repository.getPaymentsByClient(clientId, userId)
    }
    
    // Get total income from a specific client
    fun getTotalFromClient(clientId: Long): Flow<Double?> {
        return repository.getTotalIncomeFromClient(clientId, userId)
    }
}

data class SimpleFinanceUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedTab: Int = 0
)
