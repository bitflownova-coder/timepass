package com.bitflow.finance.ui.screens.simple_finance

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.ClientDiscussionEntity
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SimpleFinanceDashboard(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    onNavigateToClients: () -> Unit,
    onNavigateToIncome: () -> Unit,
    onNavigateToExpenses: () -> Unit,
    onNavigateToReports: () -> Unit,
    onNavigateToInvoice: (Long?) -> Unit
) {
    val totalIncome by viewModel.totalIncome.collectAsState()
    val totalExpenses by viewModel.totalExpenses.collectAsState()
    val pendingTotal by viewModel.pendingTotal.collectAsState()
    val pendingDiscussions by viewModel.pendingDiscussions.collectAsState()
    val recentPayments by viewModel.incomePayments.collectAsState()
    val recentExpenses by viewModel.expenses.collectAsState()
    val subscriptions by viewModel.subscriptions.collectAsState()
    val expensesWithoutBill by viewModel.expensesWithoutBill.collectAsState()
    val paymentsWithoutInvoice by viewModel.paymentsWithoutInvoice.collectAsState()
    
    val profit = totalIncome - totalExpenses
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    // Combine and sort recent transactions (moved outside LazyColumn)
    val recentTransactions = remember(recentPayments, recentExpenses) {
        val incomeItems = recentPayments.take(5).map { TransactionItem.Income(it) }
        val expenseItems = recentExpenses.take(5).map { TransactionItem.Expense(it) }
        (incomeItems + expenseItems).sortedByDescending { it.date }.take(5)
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("BitFlow Finance", fontWeight = FontWeight.Bold)
                        Text(
                            "Simple Business Tracker",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent
                )
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Summary Cards
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    SummaryCard(
                        title = "Total Income",
                        value = currencyFormat.format(totalIncome),
                        icon = Icons.Default.TrendingUp,
                        color = Color(0xFF10B981),
                        modifier = Modifier.weight(1f)
                    )
                    SummaryCard(
                        title = "Total Expenses",
                        value = currencyFormat.format(totalExpenses),
                        icon = Icons.Default.TrendingDown,
                        color = Color(0xFFEF4444),
                        modifier = Modifier.weight(1f)
                    )
                }
            }
            
            // Profit & Pending Row
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    SummaryCard(
                        title = "Net Profit",
                        value = currencyFormat.format(profit),
                        icon = if (profit >= 0) Icons.Default.AccountBalance else Icons.Default.Warning,
                        color = if (profit >= 0) Color(0xFF3B82F6) else Color(0xFFF59E0B),
                        modifier = Modifier.weight(1f)
                    )
                    SummaryCard(
                        title = "Pending",
                        value = currencyFormat.format(pendingTotal),
                        icon = Icons.Default.Schedule,
                        color = Color(0xFF8B5CF6),
                        modifier = Modifier.weight(1f)
                    )
                }
            }
            
            // Quick Actions
            item {
                Text(
                    "Quick Actions",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(8.dp))
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    item {
                        QuickActionButton(
                            label = "Clients",
                            icon = Icons.Default.People,
                            color = Color(0xFF6366F1),
                            onClick = onNavigateToClients
                        )
                    }
                    item {
                        QuickActionButton(
                            label = "Income",
                            icon = Icons.Default.Add,
                            color = Color(0xFF10B981),
                            onClick = onNavigateToIncome
                        )
                    }
                    item {
                        QuickActionButton(
                            label = "Expense",
                            icon = Icons.Default.Remove,
                            color = Color(0xFFEF4444),
                            onClick = onNavigateToExpenses
                        )
                    }
                    item {
                        QuickActionButton(
                            label = "Invoice",
                            icon = Icons.Default.Receipt,
                            color = Color(0xFF3B82F6),
                            onClick = { onNavigateToInvoice(null) }
                        )
                    }
                    item {
                        QuickActionButton(
                            label = "Reports",
                            icon = Icons.Default.BarChart,
                            color = Color(0xFFF59E0B),
                            onClick = onNavigateToReports
                        )
                    }
                }
            }
            
            // Alerts Section
            if (expensesWithoutBill.isNotEmpty() || paymentsWithoutInvoice.isNotEmpty()) {
                item {
                    AlertSection(
                        expensesWithoutBill = expensesWithoutBill.size,
                        paymentsWithoutInvoice = paymentsWithoutInvoice.size,
                        onAttachBills = onNavigateToExpenses,
                        onGenerateInvoices = { onNavigateToInvoice(null) }
                    )
                }
            }
            
            // Pending Discussions
            if (pendingDiscussions.isNotEmpty()) {
                item {
                    SectionHeader(
                        title = "Pending Discussions",
                        count = pendingDiscussions.size,
                        onSeeAll = onNavigateToClients
                    )
                }
                items(pendingDiscussions.take(3)) { discussion ->
                    DiscussionCard(
                        discussion = discussion,
                        onConvert = { viewModel.convertToPayment(discussion) },
                        onUpdate = { /* Navigate to edit */ }
                    )
                }
            }
            
            // Active Subscriptions
            if (subscriptions.isNotEmpty()) {
                item {
                    SectionHeader(
                        title = "Active Subscriptions",
                        count = subscriptions.size,
                        onSeeAll = onNavigateToExpenses
                    )
                }
                items(subscriptions.take(3)) { subscription ->
                    SubscriptionCard(subscription = subscription)
                }
            }
            
            // Recent Transactions
            item {
                SectionHeader(
                    title = "Recent Activity",
                    count = recentPayments.size + recentExpenses.size,
                    onSeeAll = onNavigateToReports
                )
            }
            
            items(recentTransactions) { transaction ->
                when (transaction) {
                    is TransactionItem.Income -> IncomeCard(transaction.payment)
                    is TransactionItem.Expense -> ExpenseCard(transaction.expense)
                }
            }
            
            item { Spacer(Modifier.height(80.dp)) }
        }
    }
}

sealed class TransactionItem {
    abstract val date: Long
    
    data class Income(val payment: IncomePaymentEntity) : TransactionItem() {
        override val date = payment.paymentDate
    }
    data class Expense(val expense: ExpenseRecordEntity) : TransactionItem() {
        override val date = expense.expenseDate
    }
}

@Composable
fun SummaryCard(
    title: String,
    value: String,
    icon: ImageVector,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = color
            )
        }
    }
}

@Composable
fun QuickActionButton(
    label: String,
    icon: ImageVector,
    color: Color,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .clickable(onClick = onClick)
            .padding(8.dp)
    ) {
        Box(
            modifier = Modifier
                .size(56.dp)
                .background(color.copy(alpha = 0.1f), CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                tint = color,
                modifier = Modifier.size(28.dp)
            )
        }
        Spacer(Modifier.height(4.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun AlertSection(
    expensesWithoutBill: Int,
    paymentsWithoutInvoice: Int,
    onAttachBills: () -> Unit,
    onGenerateInvoices: () -> Unit
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF78350F)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Warning,
                    contentDescription = null,
                    tint = Color(0xFFFCD34D),
                    modifier = Modifier.size(20.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "Attention Required", 
                    fontWeight = FontWeight.Bold, 
                    fontSize = 14.sp,
                    color = Color(0xFFFEF3C7)
                )
            }
            Spacer(Modifier.height(8.dp))
            if (expensesWithoutBill > 0) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(onClick = onAttachBills)
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "$expensesWithoutBill expenses need bills", 
                        fontSize = 13.sp,
                        color = Color(0xFFFDE68A)
                    )
                    Icon(Icons.Default.ArrowForward, null, Modifier.size(16.dp), tint = Color(0xFFFDE68A))
                }
            }
            if (paymentsWithoutInvoice > 0) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(onClick = onGenerateInvoices)
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "$paymentsWithoutInvoice payments without invoice", 
                        fontSize = 13.sp,
                        color = Color(0xFFFDE68A)
                    )
                    Icon(Icons.Default.ArrowForward, null, Modifier.size(16.dp), tint = Color(0xFFFDE68A))
                }
            }
        }
    }
}

@Composable
fun SectionHeader(title: String, count: Int, onSeeAll: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            "$title ($count)",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        TextButton(onClick = onSeeAll) {
            Text("See All")
        }
    }
}

@Composable
fun DiscussionCard(
    discussion: ClientDiscussionEntity,
    onConvert: () -> Unit,
    onUpdate: () -> Unit
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF8B5CF6).copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        discussion.title,
                        fontWeight = FontWeight.Bold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        "Last updated: ${dateFormat.format(Date(discussion.lastUpdated))}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(
                    currencyFormat.format(discussion.expectedAmount),
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF8B5CF6)
                )
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = onUpdate,
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(8.dp)
                ) {
                    Text("Update", fontSize = 12.sp)
                }
                Button(
                    onClick = onConvert,
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("Convert to Payment", fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun SubscriptionCard(subscription: ExpenseRecordEntity) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Autorenew,
                    contentDescription = null,
                    tint = Color(0xFFEF4444),
                    modifier = Modifier.size(24.dp)
                )
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(subscription.description, fontWeight = FontWeight.Medium)
                    Text(
                        "${subscription.recurringPeriod ?: "Monthly"} • ${subscription.category}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Text(
                currencyFormat.format(subscription.amount),
                fontWeight = FontWeight.Bold,
                color = Color(0xFFEF4444)
            )
        }
    }
}

@Composable
fun IncomeCard(payment: IncomePaymentEntity) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM", Locale.getDefault())
    
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.05f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(Color(0xFF10B981).copy(alpha = 0.1f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        Icons.Default.ArrowDownward,
                        contentDescription = null,
                        tint = Color(0xFF10B981),
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(
                        payment.description,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        dateFormat.format(Date(payment.paymentDate)),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Text(
                "+${currencyFormat.format(payment.amount)}",
                fontWeight = FontWeight.Bold,
                color = Color(0xFF10B981)
            )
        }
    }
}

@Composable
fun ExpenseCard(expense: ExpenseRecordEntity) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM", Locale.getDefault())
    
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.05f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(Color(0xFFEF4444).copy(alpha = 0.1f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        Icons.Default.ArrowUpward,
                        contentDescription = null,
                        tint = Color(0xFFEF4444),
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(
                        expense.description,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Row {
                        Text(
                            expense.category,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        if (!expense.billAttached) {
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "• No bill",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFFF59E0B)
                            )
                        }
                    }
                }
            }
            Text(
                "-${currencyFormat.format(expense.amount)}",
                fontWeight = FontWeight.Bold,
                color = Color(0xFFEF4444)
            )
        }
    }
}
