package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.ClientDao
import com.bitflow.finance.data.local.dao.ClientDiscussionDao
import com.bitflow.finance.data.local.dao.IncomePaymentDao
import com.bitflow.finance.data.local.dao.ExpenseRecordDao
import com.bitflow.finance.data.local.dao.MonthlyTotal
import com.bitflow.finance.data.local.dao.CategoryTotal
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.ClientDiscussionEntity
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SimpleFinanceRepository @Inject constructor(
    private val clientDao: ClientDao,
    private val discussionDao: ClientDiscussionDao,
    private val incomeDao: IncomePaymentDao,
    private val expenseDao: ExpenseRecordDao
) {
    // ================== CLIENTS ==================
    fun getAllClients(userId: String): Flow<List<ClientEntity>> = clientDao.getAllClients(userId)
    
    fun searchClients(query: String, userId: String): Flow<List<ClientEntity>> = clientDao.searchClients(query, userId)
    
    suspend fun getClientById(id: Long, userId: String): ClientEntity? = clientDao.getClientById(id, userId)
    
    suspend fun insertClient(client: ClientEntity): Long = clientDao.insertClient(client)
    
    suspend fun updateClient(client: ClientEntity) = clientDao.updateClient(client)
    
    suspend fun deleteClient(client: ClientEntity) = clientDao.deleteClient(client)
    
    // ================== DISCUSSIONS ==================
    fun getAllDiscussions(userId: String): Flow<List<ClientDiscussionEntity>> = discussionDao.getAllDiscussions(userId)
    
    fun getDiscussionsByClient(clientId: Long, userId: String): Flow<List<ClientDiscussionEntity>> = 
        discussionDao.getDiscussionsByClient(clientId, userId)
    
    fun getDiscussionsByStatus(status: String, userId: String): Flow<List<ClientDiscussionEntity>> = 
        discussionDao.getDiscussionsByStatus(status, userId)
    
    suspend fun getDiscussionById(id: Long, userId: String): ClientDiscussionEntity? = 
        discussionDao.getDiscussionById(id, userId)
    
    fun getPendingTotal(userId: String): Flow<Double?> = discussionDao.getPendingTotal(userId)
    
    fun getFinalizedTotal(userId: String): Flow<Double?> = discussionDao.getFinalizedTotal(userId)
    
    suspend fun insertDiscussion(discussion: ClientDiscussionEntity): Long = 
        discussionDao.insertDiscussion(discussion)
    
    suspend fun updateDiscussion(discussion: ClientDiscussionEntity) = 
        discussionDao.updateDiscussion(discussion)
    
    suspend fun deleteDiscussion(discussion: ClientDiscussionEntity) = 
        discussionDao.deleteDiscussion(discussion)
    
    suspend fun updateDiscussionStatus(id: Long, newStatus: String) = 
        discussionDao.updateStatus(id, newStatus)
    
    suspend fun updateDiscussionAmount(id: Long, newAmount: Double, notes: String) = 
        discussionDao.updateAmount(id, newAmount, notes)
    
    // ================== INCOME/PAYMENTS ==================
    fun getAllPayments(userId: String): Flow<List<IncomePaymentEntity>> = incomeDao.getAllPayments(userId)
    
    fun getPaymentsByClient(clientId: Long, userId: String): Flow<List<IncomePaymentEntity>> = 
        incomeDao.getPaymentsByClient(clientId, userId)
    
    suspend fun getPaymentById(id: Long, userId: String): IncomePaymentEntity? = 
        incomeDao.getPaymentById(id, userId)
    
    fun getPaymentsWithoutInvoice(userId: String): Flow<List<IncomePaymentEntity>> = 
        incomeDao.getPaymentsWithoutInvoice(userId)
    
    fun getTotalIncome(userId: String): Flow<Double?> = incomeDao.getTotalIncome(userId)
    
    fun getIncomeForPeriod(startDate: Long, endDate: Long, userId: String): Flow<Double?> = 
        incomeDao.getIncomeForPeriod(startDate, endDate, userId)
    
    fun getTotalIncomeFromClient(clientId: Long, userId: String): Flow<Double?> = 
        incomeDao.getTotalIncomeFromClient(clientId, userId)
    
    fun getMonthlyIncome(userId: String): Flow<List<MonthlyTotal>> = incomeDao.getMonthlyIncome(userId)
    
    suspend fun insertPayment(payment: IncomePaymentEntity): Long = incomeDao.insertPayment(payment)
    
    suspend fun updatePayment(payment: IncomePaymentEntity) = incomeDao.updatePayment(payment)
    
    suspend fun deletePayment(payment: IncomePaymentEntity) = incomeDao.deletePayment(payment)
    
    suspend fun deletePaymentByDiscussionId(discussionId: Long, userId: String) = 
        incomeDao.deletePaymentByDiscussionId(discussionId, userId)
    
    suspend fun markInvoiceGenerated(id: Long, invoiceNumber: String, invoiceId: Long) = 
        incomeDao.markInvoiceGenerated(id, invoiceNumber, invoiceId)
    
    // Convert finalized discussion to income payment
    suspend fun convertDiscussionToPayment(
        discussion: ClientDiscussionEntity,
        userId: String,
        paymentMode: String = "bank",
        reference: String = ""
    ): Long {
        // Update discussion status to finalized
        discussionDao.updateStatus(discussion.id, "finalized")
        
        // Create income payment
        val payment = IncomePaymentEntity(
            userId = userId,
            clientId = discussion.clientId,
            discussionId = discussion.id,
            amount = discussion.expectedAmount,
            description = discussion.title,
            paymentDate = System.currentTimeMillis(),
            paymentMode = paymentMode,
            reference = reference,
            notes = "Converted from discussion: ${discussion.title}"
        )
        return incomeDao.insertPayment(payment)
    }
    
    // ================== EXPENSES ==================
    fun getAllExpenses(userId: String): Flow<List<ExpenseRecordEntity>> = expenseDao.getAllExpenses(userId)
    
    fun getExpensesByType(type: String, userId: String): Flow<List<ExpenseRecordEntity>> = 
        expenseDao.getExpensesByType(type, userId)
    
    fun getExpensesByCategory(category: String, userId: String): Flow<List<ExpenseRecordEntity>> = 
        expenseDao.getExpensesByCategory(category, userId)
    
    fun getSubscriptions(userId: String): Flow<List<ExpenseRecordEntity>> = expenseDao.getSubscriptions(userId)
    
    suspend fun getExpenseById(id: Long, userId: String): ExpenseRecordEntity? = 
        expenseDao.getExpenseById(id, userId)
    
    fun getTotalExpenses(userId: String): Flow<Double?> = expenseDao.getTotalExpenses(userId)
    
    fun getExpensesForPeriod(startDate: Long, endDate: Long, userId: String): Flow<Double?> = 
        expenseDao.getExpensesForPeriod(startDate, endDate, userId)
    
    fun getTotalSubscriptions(userId: String): Flow<Double?> = expenseDao.getTotalSubscriptions(userId)
    
    fun getTotalOneTime(userId: String): Flow<Double?> = expenseDao.getTotalOneTime(userId)
    
    fun getExpensesByCategories(userId: String): Flow<List<CategoryTotal>> = 
        expenseDao.getExpensesByCategories(userId)
    
    fun getMonthlyExpenses(userId: String): Flow<List<MonthlyTotal>> = expenseDao.getMonthlyExpenses(userId)
    
    fun getExpensesWithoutBill(userId: String): Flow<List<ExpenseRecordEntity>> = 
        expenseDao.getExpensesWithoutBill(userId)
    
    fun getUpcomingSubscriptions(date: Long, userId: String): Flow<List<ExpenseRecordEntity>> = 
        expenseDao.getUpcomingSubscriptions(date, userId)
    
    suspend fun insertExpense(expense: ExpenseRecordEntity): Long = expenseDao.insertExpense(expense)
    
    suspend fun updateExpense(expense: ExpenseRecordEntity) = expenseDao.updateExpense(expense)
    
    suspend fun deleteExpense(expense: ExpenseRecordEntity) = expenseDao.deleteExpense(expense)
    
    suspend fun attachBill(id: Long, billPath: String) = expenseDao.attachBill(id, billPath)
}
