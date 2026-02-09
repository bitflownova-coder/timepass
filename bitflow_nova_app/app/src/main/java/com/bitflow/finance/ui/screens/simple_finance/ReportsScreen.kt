package com.bitflow.finance.ui.screens.simple_finance

import android.content.Context
import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.dao.CategoryTotal
import com.bitflow.finance.data.local.dao.MonthlyTotal
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import java.io.File
import java.io.FileOutputStream
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportsScreen(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    val totalIncome by viewModel.totalIncome.collectAsState()
    val totalExpenses by viewModel.totalExpenses.collectAsState()
    val monthlyIncome by viewModel.monthlyIncome.collectAsState()
    val monthlyExpenses by viewModel.monthlyExpenses.collectAsState()
    val expensesByCategory by viewModel.expensesByCategory.collectAsState()
    val incomePayments by viewModel.incomePayments.collectAsState()
    val expenses by viewModel.expenses.collectAsState()
    
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val profit = totalIncome - totalExpenses
    
    var isExporting by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Reports & Analytics", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(
                        onClick = {
                            isExporting = true
                            exportReport(
                                context = context,
                                income = incomePayments,
                                expenses = expenses,
                                totalIncome = totalIncome,
                                totalExpenses = totalExpenses
                            )
                            isExporting = false
                        }
                    ) {
                        Icon(Icons.Default.FileDownload, contentDescription = "Export")
                    }
                }
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
            // Summary Section
            item {
                Text("Financial Summary", fontWeight = FontWeight.Bold, fontSize = 18.sp)
            }
            
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text("Total Income", style = MaterialTheme.typography.bodySmall)
                                Text(
                                    currencyFormat.format(totalIncome),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 20.sp,
                                    color = Color(0xFF10B981)
                                )
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text("Total Expenses", style = MaterialTheme.typography.bodySmall)
                                Text(
                                    currencyFormat.format(totalExpenses),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 20.sp,
                                    color = Color(0xFFEF4444)
                                )
                            }
                        }
                        
                        Divider(modifier = Modifier.padding(vertical = 12.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("Net Profit", style = MaterialTheme.typography.bodySmall)
                                Text(
                                    currencyFormat.format(profit),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 24.sp,
                                    color = if (profit >= 0) Color(0xFF3B82F6) else Color(0xFFEF4444)
                                )
                                if (totalIncome > 0) {
                                    val margin = (profit / totalIncome) * 100
                                    Text(
                                        "Margin: ${String.format("%.1f", margin)}%",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    }
                }
            }
            
            // Monthly Trend
            if (monthlyIncome.isNotEmpty() || monthlyExpenses.isNotEmpty()) {
                item {
                    Text("Monthly Trend", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                }
                
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                        shape = RoundedCornerShape(16.dp)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            // Combine monthly data
                            val allMonths = (monthlyIncome.map { it.month } + monthlyExpenses.map { it.month })
                                .distinct()
                                .sortedDescending()
                                .take(6)
                            
                            allMonths.forEach { month ->
                                val income = monthlyIncome.find { it.month == month }?.total ?: 0.0
                                val expense = monthlyExpenses.find { it.month == month }?.total ?: 0.0
                                
                                MonthRow(
                                    month = formatMonthYear(month),
                                    income = income,
                                    expense = expense
                                )
                            }
                        }
                    }
                }
            }
            
            // Expense by Category
            if (expensesByCategory.isNotEmpty()) {
                item {
                    Text("Expenses by Category", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                }
                
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                        shape = RoundedCornerShape(16.dp)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            expensesByCategory.take(8).forEach { category ->
                                CategoryRow(
                                    category = category,
                                    total = totalExpenses
                                )
                            }
                        }
                    }
                }
            }
            
            // Export Section
            item {
                Text("Export Data", fontWeight = FontWeight.Bold, fontSize = 18.sp)
            }
            
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    ExportButton(
                        label = "CSV Export",
                        icon = Icons.Default.TableChart,
                        color = Color(0xFF10B981),
                        modifier = Modifier.weight(1f),
                        onClick = {
                            exportToCsv(context, incomePayments, expenses)
                        }
                    )
                    ExportButton(
                        label = "PDF Report",
                        icon = Icons.Default.PictureAsPdf,
                        color = Color(0xFFEF4444),
                        modifier = Modifier.weight(1f),
                        onClick = {
                            exportReport(context, incomePayments, expenses, totalIncome, totalExpenses)
                        }
                    )
                }
            }
            
            // Statistics
            item {
                Text("Quick Stats", fontWeight = FontWeight.Bold, fontSize = 18.sp)
            }
            
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    StatCard(
                        title = "Payments",
                        value = "${incomePayments.size}",
                        subtitle = "Total received",
                        color = Color(0xFF10B981),
                        modifier = Modifier.weight(1f)
                    )
                    StatCard(
                        title = "Expenses",
                        value = "${expenses.size}",
                        subtitle = "Total recorded",
                        color = Color(0xFFEF4444),
                        modifier = Modifier.weight(1f)
                    )
                }
            }
            
            item {
                val avgIncome = if (incomePayments.isNotEmpty()) totalIncome / incomePayments.size else 0.0
                val avgExpense = if (expenses.isNotEmpty()) totalExpenses / expenses.size else 0.0
                
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    StatCard(
                        title = "Avg Income",
                        value = currencyFormat.format(avgIncome),
                        subtitle = "Per payment",
                        color = Color(0xFF3B82F6),
                        modifier = Modifier.weight(1f)
                    )
                    StatCard(
                        title = "Avg Expense",
                        value = currencyFormat.format(avgExpense),
                        subtitle = "Per record",
                        color = Color(0xFF8B5CF6),
                        modifier = Modifier.weight(1f)
                    )
                }
            }
            
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
}

@Composable
fun MonthRow(month: String, income: Double, expense: Double) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(month, fontWeight = FontWeight.Medium)
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(
                "+${currencyFormat.format(income)}",
                color = Color(0xFF10B981),
                fontSize = 13.sp
            )
            Text(
                "-${currencyFormat.format(expense)}",
                color = Color(0xFFEF4444),
                fontSize = 13.sp
            )
        }
    }
}

@Composable
fun CategoryRow(category: CategoryTotal, total: Double) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val percentage = if (total > 0) (category.total / total) * 100 else 0.0
    
    Column(modifier = Modifier.padding(vertical = 6.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(category.category, fontWeight = FontWeight.Medium)
            Text(currencyFormat.format(category.total))
        }
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = (percentage / 100).toFloat().coerceIn(0f, 1f),
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp),
            color = Color(0xFFEF4444),
            trackColor = Color(0xFFEF4444).copy(alpha = 0.1f)
        )
        Text(
            "${String.format("%.1f", percentage)}%",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun ExportButton(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier.height(56.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = color)
    ) {
        Icon(icon, null)
        Spacer(Modifier.width(8.dp))
        Text(label)
    }
}

@Composable
fun StatCard(
    title: String,
    value: String,
    subtitle: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(title, style = MaterialTheme.typography.bodySmall, color = color)
            Text(value, fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun formatMonthYear(monthStr: String): String {
    return try {
        val inputFormat = SimpleDateFormat("yyyy-MM", Locale.getDefault())
        val outputFormat = SimpleDateFormat("MMM yyyy", Locale.getDefault())
        val date = inputFormat.parse(monthStr)
        date?.let { outputFormat.format(it) } ?: monthStr
    } catch (e: Exception) {
        monthStr
    }
}

private fun exportToCsv(
    context: Context,
    income: List<IncomePaymentEntity>,
    expenses: List<ExpenseRecordEntity>
) {
    val dateFormat = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
    
    val csv = StringBuilder()
    
    // Income section
    csv.appendLine("=== INCOME ===")
    csv.appendLine("Date,Description,Amount,Payment Mode,Reference")
    income.forEach { payment ->
        csv.appendLine(
            "${dateFormat.format(Date(payment.paymentDate))},\"${payment.description}\",${payment.amount},${payment.paymentMode},${payment.reference}"
        )
    }
    
    csv.appendLine()
    
    // Expenses section
    csv.appendLine("=== EXPENSES ===")
    csv.appendLine("Date,Description,Amount,Category,Type,Vendor,Has Bill")
    expenses.forEach { expense ->
        csv.appendLine(
            "${dateFormat.format(Date(expense.expenseDate))},\"${expense.description}\",${expense.amount},${expense.category},${expense.expenseType},\"${expense.vendor}\",${if (expense.billAttached) "Yes" else "No"}"
        )
    }
    
    shareFile(context, csv.toString(), "finance_report.csv", "text/csv")
}

private fun exportReport(
    context: Context,
    income: List<IncomePaymentEntity>,
    expenses: List<ExpenseRecordEntity>,
    totalIncome: Double,
    totalExpenses: Double
) {
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    val html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Financial Report</title>
    <style>
        body { font-family: system-ui; padding: 20px; }
        h1 { color: #1e293b; }
        .summary { background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .row { display: flex; justify-content: space-between; padding: 8px 0; }
        .income { color: #10B981; }
        .expense { color: #EF4444; }
        .profit { font-size: 24px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background: #f1f5f9; }
    </style>
</head>
<body>
    <h1>Financial Report</h1>
    <p>Generated on ${dateFormat.format(Date())}</p>
    
    <div class="summary">
        <div class="row">
            <span>Total Income:</span>
            <span class="income">${currencyFormat.format(totalIncome)}</span>
        </div>
        <div class="row">
            <span>Total Expenses:</span>
            <span class="expense">${currencyFormat.format(totalExpenses)}</span>
        </div>
        <hr>
        <div class="row">
            <span>Net Profit:</span>
            <span class="profit ${if (totalIncome - totalExpenses >= 0) "income" else "expense"}">${currencyFormat.format(totalIncome - totalExpenses)}</span>
        </div>
    </div>
    
    <h2>Income (${income.size} records)</h2>
    <table>
        <tr><th>Date</th><th>Description</th><th>Amount</th></tr>
        ${income.take(20).joinToString("") { 
            "<tr><td>${dateFormat.format(Date(it.paymentDate))}</td><td>${it.description}</td><td class='income'>${currencyFormat.format(it.amount)}</td></tr>"
        }}
    </table>
    
    <h2>Expenses (${expenses.size} records)</h2>
    <table>
        <tr><th>Date</th><th>Description</th><th>Category</th><th>Amount</th></tr>
        ${expenses.take(20).joinToString("") { 
            "<tr><td>${dateFormat.format(Date(it.expenseDate))}</td><td>${it.description}</td><td>${it.category}</td><td class='expense'>${currencyFormat.format(it.amount)}</td></tr>"
        }}
    </table>
    
    <p style="text-align: center; color: #64748b; margin-top: 40px;">Generated by BitFlow Nova Finance</p>
</body>
</html>
    """.trimIndent()
    
    shareFile(context, html, "financial_report.html", "text/html")
}

private fun shareFile(context: Context, content: String, filename: String, mimeType: String) {
    try {
        val file = File(context.cacheDir, filename)
        FileOutputStream(file).use { it.write(content.toByteArray()) }
        
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.provider",
            file
        )
        
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = mimeType
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, "Financial Report")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        
        context.startActivity(Intent.createChooser(intent, "Share Report"))
    } catch (e: Exception) {
        e.printStackTrace()
    }
}
