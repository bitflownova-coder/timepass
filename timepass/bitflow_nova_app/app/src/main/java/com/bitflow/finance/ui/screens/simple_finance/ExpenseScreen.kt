package com.bitflow.finance.ui.screens.simple_finance

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExpenseScreen(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    onBackClick: () -> Unit
) {
    val expenses by viewModel.expenses.collectAsState()
    val totalExpenses by viewModel.totalExpenses.collectAsState()
    val subscriptions by viewModel.subscriptions.collectAsState()
    val expensesWithoutBill by viewModel.expensesWithoutBill.collectAsState()
    val expensesByCategory by viewModel.expensesByCategory.collectAsState()
    
    var showAddExpenseDialog by remember { mutableStateOf(false) }
    var selectedFilter by remember { mutableStateOf("all") }
    var selectedCategory by remember { mutableStateOf<String?>(null) }
    
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    val filteredExpenses = expenses.filter { expense ->
        val matchesFilter = when (selectedFilter) {
            "one_time" -> expense.expenseType == "one_time"
            "subscription" -> expense.expenseType == "subscription"
            "without_bill" -> !expense.billAttached
            else -> true
        }
        val matchesCategory = selectedCategory == null || expense.category == selectedCategory
        matchesFilter && matchesCategory
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Expenses", fontWeight = FontWeight.Bold)
                        Text(
                            "Total: ${currencyFormat.format(totalExpenses)}",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFFEF4444)
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddExpenseDialog = true },
                containerColor = Color(0xFFEF4444)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Expense")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Summary Cards Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(Icons.Default.Receipt, null, tint = Color(0xFFEF4444))
                        Text("${expenses.size}", fontWeight = FontWeight.Bold)
                        Text("Total", style = MaterialTheme.typography.bodySmall)
                    }
                }
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF8B5CF6).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(Icons.Default.Autorenew, null, tint = Color(0xFF8B5CF6))
                        Text("${subscriptions.size}", fontWeight = FontWeight.Bold)
                        Text("Subscriptions", style = MaterialTheme.typography.bodySmall)
                    }
                }
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF59E0B).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(Icons.Default.Warning, null, tint = Color(0xFFF59E0B))
                        Text("${expensesWithoutBill.size}", fontWeight = FontWeight.Bold)
                        Text("No Bill", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            
            // Filter Chips
            LazyRow(
                modifier = Modifier.padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                item {
                    FilterChip(
                        selected = selectedFilter == "all",
                        onClick = { selectedFilter = "all" },
                        label = { Text("All") }
                    )
                }
                item {
                    FilterChip(
                        selected = selectedFilter == "one_time",
                        onClick = { selectedFilter = "one_time" },
                        label = { Text("One-time") }
                    )
                }
                item {
                    FilterChip(
                        selected = selectedFilter == "subscription",
                        onClick = { selectedFilter = "subscription" },
                        label = { Text("Subscription") }
                    )
                }
                item {
                    FilterChip(
                        selected = selectedFilter == "without_bill",
                        onClick = { selectedFilter = "without_bill" },
                        label = { Text("No Bill") },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Color(0xFFF59E0B).copy(alpha = 0.2f)
                        )
                    )
                }
            }
            
            // Category Filter
            if (expensesByCategory.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                LazyRow(
                    modifier = Modifier.padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    item {
                        AssistChip(
                            onClick = { selectedCategory = null },
                            label = { Text("All Categories") },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = if (selectedCategory == null) 
                                    MaterialTheme.colorScheme.primary.copy(alpha = 0.1f) 
                                else Color.Transparent
                            )
                        )
                    }
                    items(expensesByCategory.take(5)) { cat ->
                        AssistChip(
                            onClick = { selectedCategory = cat.category },
                            label = { Text(cat.category) },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = if (selectedCategory == cat.category) 
                                    MaterialTheme.colorScheme.primary.copy(alpha = 0.1f) 
                                else Color.Transparent
                            )
                        )
                    }
                }
            }
            
            Spacer(Modifier.height(8.dp))
            
            // Expenses List
            if (filteredExpenses.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            Icons.Default.ReceiptLong,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                        )
                        Spacer(Modifier.height(16.dp))
                        Text(
                            "No expenses found",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(filteredExpenses) { expense ->
                        ExpenseCard(
                            expense = expense,
                            onAttachBill = { billPath -> 
                                viewModel.attachBillToExpense(expense.id, billPath)
                            },
                            onDelete = { viewModel.deleteExpense(expense) }
                        )
                    }
                }
            }
        }
    }
    
    // Add Expense Dialog
    if (showAddExpenseDialog) {
        AddExpenseDialog(
            onDismiss = { showAddExpenseDialog = false },
            onAdd = { amount, description, reason, expenseType, category, paymentMode, vendor, isRecurring, recurringPeriod ->
                viewModel.addExpense(
                    amount = amount,
                    description = description,
                    reason = reason,
                    expenseType = expenseType,
                    category = category,
                    paymentMode = paymentMode,
                    vendor = vendor,
                    isRecurring = isRecurring,
                    recurringPeriod = recurringPeriod
                )
                showAddExpenseDialog = false
            }
        )
    }
}

@Composable
fun ExpenseCard(
    expense: ExpenseRecordEntity,
    onAttachBill: (String) -> Unit,
    onDelete: () -> Unit
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    var showMenu by remember { mutableStateOf(false) }
    
    // File picker for bill attachment
    val context = LocalContext.current
    val pickImage = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let { 
            onAttachBill(it.toString())
        }
    }
    
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (expense.billAttached) 
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            else Color(0xFFF59E0B).copy(alpha = 0.05f)
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .background(
                                if (expense.isRecurring) Color(0xFF8B5CF6).copy(alpha = 0.1f)
                                else Color(0xFFEF4444).copy(alpha = 0.1f),
                                CircleShape
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            if (expense.isRecurring) Icons.Default.Autorenew else Icons.Default.ArrowUpward,
                            contentDescription = null,
                            tint = if (expense.isRecurring) Color(0xFF8B5CF6) else Color(0xFFEF4444),
                            modifier = Modifier.size(24.dp)
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text(
                            expense.description,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Row {
                            Surface(
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    expense.category,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    fontSize = 10.sp,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                            Spacer(Modifier.width(4.dp))
                            Text(
                                dateFormat.format(Date(expense.expenseDate)),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
                
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "-${currencyFormat.format(expense.amount)}",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = Color(0xFFEF4444)
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        if (expense.isRecurring) {
                            Text(
                                expense.recurringPeriod ?: "Monthly",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF8B5CF6)
                            )
                        }
                        Box {
                            IconButton(onClick = { showMenu = true }, modifier = Modifier.size(24.dp)) {
                                Icon(Icons.Default.MoreVert, null, Modifier.size(16.dp))
                            }
                            DropdownMenu(
                                expanded = showMenu,
                                onDismissRequest = { showMenu = false }
                            ) {
                                if (!expense.billAttached) {
                                    DropdownMenuItem(
                                        text = { Text("Attach Bill") },
                                        onClick = { 
                                            showMenu = false
                                            pickImage.launch("image/*")
                                        },
                                        leadingIcon = { Icon(Icons.Default.AttachFile, null) }
                                    )
                                }
                                DropdownMenuItem(
                                    text = { Text("Delete", color = Color(0xFFEF4444)) },
                                    onClick = { 
                                        showMenu = false
                                        onDelete()
                                    },
                                    leadingIcon = { Icon(Icons.Default.Delete, null, tint = Color(0xFFEF4444)) }
                                )
                            }
                        }
                    }
                }
            }
            
            // Reason
            if (expense.reason.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                Text(
                    "Reason: ${expense.reason}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2
                )
            }
            
            // Bill Status & Vendor
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (expense.vendor.isNotEmpty()) {
                    Text(
                        "Vendor: ${expense.vendor}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                if (expense.billAttached) {
                    Surface(
                        color = Color(0xFF10B981).copy(alpha = 0.1f),
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Check,
                                contentDescription = null,
                                tint = Color(0xFF10B981),
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "Bill Attached",
                                fontSize = 11.sp,
                                color = Color(0xFF10B981)
                            )
                        }
                    }
                } else {
                    Surface(
                        color = Color(0xFFF59E0B).copy(alpha = 0.1f),
                        shape = RoundedCornerShape(4.dp),
                        modifier = Modifier.clickable { pickImage.launch("image/*") }
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.AttachFile,
                                contentDescription = null,
                                tint = Color(0xFFF59E0B),
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "Attach Bill",
                                fontSize = 11.sp,
                                color = Color(0xFFF59E0B)
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddExpenseDialog(
    onDismiss: () -> Unit,
    onAdd: (
        amount: Double,
        description: String,
        reason: String,
        expenseType: String,
        category: String,
        paymentMode: String,
        vendor: String,
        isRecurring: Boolean,
        recurringPeriod: String?
    ) -> Unit
) {
    var amount by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var reason by remember { mutableStateOf("") }
    var expenseType by remember { mutableStateOf("one_time") }
    var category by remember { mutableStateOf(ExpenseRecordEntity.EXPENSE_CATEGORIES.first()) }
    var paymentMode by remember { mutableStateOf("bank") }
    var vendor by remember { mutableStateOf("") }
    var recurringPeriod by remember { mutableStateOf("monthly") }
    
    var categoryExpanded by remember { mutableStateOf(false) }
    var modeExpanded by remember { mutableStateOf(false) }
    var periodExpanded by remember { mutableStateOf(false) }
    
    val paymentModes = listOf("bank", "upi", "cash", "card", "other")
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Expense", fontWeight = FontWeight.Bold) },
        text = {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                item {
                    OutlinedTextField(
                        value = amount,
                        onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                        label = { Text("Amount *") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        leadingIcon = { Text("₹") }
                    )
                }
                
                item {
                    OutlinedTextField(
                        value = description,
                        onValueChange = { description = it },
                        label = { Text("What was purchased? *") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                }
                
                item {
                    OutlinedTextField(
                        value = reason,
                        onValueChange = { reason = it },
                        label = { Text("Why was it needed? *") },
                        modifier = Modifier.fillMaxWidth(),
                        maxLines = 2
                    )
                }
                
                // Expense Type (One-time vs Subscription)
                item {
                    Text("Expense Type", style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(4.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilterChip(
                            selected = expenseType == "one_time",
                            onClick = { expenseType = "one_time" },
                            label = { Text("One-time") },
                            leadingIcon = if (expenseType == "one_time") {
                                { Icon(Icons.Default.Check, null, Modifier.size(16.dp)) }
                            } else null
                        )
                        FilterChip(
                            selected = expenseType == "subscription",
                            onClick = { expenseType = "subscription" },
                            label = { Text("Subscription") },
                            leadingIcon = if (expenseType == "subscription") {
                                { Icon(Icons.Default.Autorenew, null, Modifier.size(16.dp)) }
                            } else null
                        )
                    }
                }
                
                // Recurring Period (only if subscription)
                if (expenseType == "subscription") {
                    item {
                        ExposedDropdownMenuBox(
                            expanded = periodExpanded,
                            onExpandedChange = { periodExpanded = it }
                        ) {
                            OutlinedTextField(
                                value = recurringPeriod.replaceFirstChar { it.uppercase() },
                                onValueChange = {},
                                readOnly = true,
                                label = { Text("Billing Period") },
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = periodExpanded) },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .menuAnchor()
                            )
                            ExposedDropdownMenu(
                                expanded = periodExpanded,
                                onDismissRequest = { periodExpanded = false }
                            ) {
                                ExpenseRecordEntity.RECURRING_PERIODS.forEach { period ->
                                    DropdownMenuItem(
                                        text = { Text(period.replaceFirstChar { it.uppercase() }) },
                                        onClick = {
                                            recurringPeriod = period
                                            periodExpanded = false
                                        }
                                    )
                                }
                            }
                        }
                    }
                }
                
                // Category Dropdown
                item {
                    ExposedDropdownMenuBox(
                        expanded = categoryExpanded,
                        onExpandedChange = { categoryExpanded = it }
                    ) {
                        OutlinedTextField(
                            value = category,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Category") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = categoryExpanded) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor()
                        )
                        ExposedDropdownMenu(
                            expanded = categoryExpanded,
                            onDismissRequest = { categoryExpanded = false }
                        ) {
                            ExpenseRecordEntity.EXPENSE_CATEGORIES.forEach { cat ->
                                DropdownMenuItem(
                                    text = { Text(cat) },
                                    onClick = {
                                        category = cat
                                        categoryExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }
                
                // Payment Mode Dropdown
                item {
                    ExposedDropdownMenuBox(
                        expanded = modeExpanded,
                        onExpandedChange = { modeExpanded = it }
                    ) {
                        OutlinedTextField(
                            value = paymentMode.replaceFirstChar { it.uppercase() },
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Payment Mode") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = modeExpanded) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor()
                        )
                        ExposedDropdownMenu(
                            expanded = modeExpanded,
                            onDismissRequest = { modeExpanded = false }
                        ) {
                            paymentModes.forEach { mode ->
                                DropdownMenuItem(
                                    text = { Text(mode.replaceFirstChar { it.uppercase() }) },
                                    onClick = {
                                        paymentMode = mode
                                        modeExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }
                
                item {
                    OutlinedTextField(
                        value = vendor,
                        onValueChange = { vendor = it },
                        label = { Text("Vendor/Paid to") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        placeholder = { Text("Optional") }
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = { 
                    onAdd(
                        amount.toDoubleOrNull() ?: 0.0,
                        description,
                        reason,
                        expenseType,
                        category,
                        paymentMode,
                        vendor,
                        expenseType == "subscription",
                        if (expenseType == "subscription") recurringPeriod else null
                    )
                },
                enabled = amount.isNotBlank() && description.isNotBlank() && reason.isNotBlank(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEF4444))
            ) {
                Text("Add Expense")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
