package com.bitflow.finance.ui.screens.simple_finance

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IncomeScreen(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    onBackClick: () -> Unit,
    onGenerateInvoice: (Long) -> Unit
) {
    val incomePayments by viewModel.incomePayments.collectAsState()
    val totalIncome by viewModel.totalIncome.collectAsState()
    val clients by viewModel.clients.collectAsState()
    val paymentsWithoutInvoice by viewModel.paymentsWithoutInvoice.collectAsState()
    
    var showAddIncomeDialog by remember { mutableStateOf(false) }
    var selectedFilter by remember { mutableStateOf("all") }
    
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    val filteredPayments = when (selectedFilter) {
        "with_invoice" -> incomePayments.filter { it.invoiceGenerated }
        "without_invoice" -> incomePayments.filter { !it.invoiceGenerated }
        else -> incomePayments
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Income", fontWeight = FontWeight.Bold)
                        Text(
                            "Total: ${currencyFormat.format(totalIncome)}",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF10B981)
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
                onClick = { showAddIncomeDialog = true },
                containerColor = Color(0xFF10B981)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Income")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Summary Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.1f)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${incomePayments.size}",
                            fontWeight = FontWeight.Bold,
                            fontSize = 24.sp,
                            color = Color(0xFF10B981)
                        )
                        Text("Payments", style = MaterialTheme.typography.bodySmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "${paymentsWithoutInvoice.size}",
                            fontWeight = FontWeight.Bold,
                            fontSize = 24.sp,
                            color = Color(0xFFF59E0B)
                        )
                        Text("Need Invoice", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            
            // Filter Chips
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    selected = selectedFilter == "all",
                    onClick = { selectedFilter = "all" },
                    label = { Text("All") }
                )
                FilterChip(
                    selected = selectedFilter == "without_invoice",
                    onClick = { selectedFilter = "without_invoice" },
                    label = { Text("Need Invoice") }
                )
                FilterChip(
                    selected = selectedFilter == "with_invoice",
                    onClick = { selectedFilter = "with_invoice" },
                    label = { Text("Invoiced") }
                )
            }
            
            Spacer(Modifier.height(8.dp))
            
            // Payments List
            if (filteredPayments.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            Icons.Default.AccountBalanceWallet,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                        )
                        Spacer(Modifier.height(16.dp))
                        Text(
                            "No income records yet",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            "Add your first payment to start tracking",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                        )
                    }
                }
            } else {
                LazyColumn(
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(filteredPayments) { payment ->
                        val client = payment.clientId?.let { clientId ->
                            clients.find { it.id == clientId }
                        }
                        
                        IncomePaymentCard(
                            payment = payment,
                            clientName = client?.name,
                            onGenerateInvoice = { onGenerateInvoice(payment.id) },
                            onDelete = { viewModel.deleteIncome(payment) }
                        )
                    }
                }
            }
        }
    }
    
    // Add Income Dialog
    if (showAddIncomeDialog) {
        AddIncomeDialog(
            clients = clients,
            onDismiss = { showAddIncomeDialog = false },
            onAdd = { amount, description, clientId, paymentMode, reference ->
                viewModel.addIncome(amount, description, clientId, paymentMode, reference)
                showAddIncomeDialog = false
            }
        )
    }
}

@Composable
fun IncomePaymentCard(
    payment: IncomePaymentEntity,
    clientName: String?,
    onGenerateInvoice: () -> Unit,
    onDelete: () -> Unit
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    var showMenu by remember { mutableStateOf(false) }
    
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (payment.invoiceGenerated) 
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            else Color(0xFF10B981).copy(alpha = 0.05f)
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
                            .background(Color(0xFF10B981).copy(alpha = 0.1f), CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            Icons.Default.ArrowDownward,
                            contentDescription = null,
                            tint = Color(0xFF10B981),
                            modifier = Modifier.size(24.dp)
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text(
                            payment.description,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        if (clientName != null) {
                            Text(
                                clientName,
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF6366F1)
                            )
                        }
                        Text(
                            dateFormat.format(Date(payment.paymentDate)),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "+${currencyFormat.format(payment.amount)}",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = Color(0xFF10B981)
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            payment.paymentMode.uppercase(),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Box {
                            IconButton(onClick = { showMenu = true }, modifier = Modifier.size(24.dp)) {
                                Icon(Icons.Default.MoreVert, null, Modifier.size(16.dp))
                            }
                            DropdownMenu(
                                expanded = showMenu,
                                onDismissRequest = { showMenu = false }
                            ) {
                                if (!payment.invoiceGenerated) {
                                    DropdownMenuItem(
                                        text = { Text("Generate Invoice") },
                                        onClick = { 
                                            showMenu = false
                                            onGenerateInvoice()
                                        },
                                        leadingIcon = { Icon(Icons.Default.Receipt, null) }
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
            
            // Invoice Status
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (payment.reference.isNotEmpty()) {
                    Text(
                        "Ref: ${payment.reference}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                if (payment.invoiceGenerated) {
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
                                "Invoice: ${payment.invoiceNumber}",
                                fontSize = 11.sp,
                                color = Color(0xFF10B981)
                            )
                        }
                    }
                } else {
                    Surface(
                        color = Color(0xFFF59E0B).copy(alpha = 0.1f),
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Warning,
                                contentDescription = null,
                                tint = Color(0xFFF59E0B),
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "Need Invoice",
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
fun AddIncomeDialog(
    clients: List<ClientEntity>,
    onDismiss: () -> Unit,
    onAdd: (amount: Double, description: String, clientId: Long?, paymentMode: String, reference: String) -> Unit
) {
    var amount by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var selectedClient by remember { mutableStateOf<ClientEntity?>(null) }
    var paymentMode by remember { mutableStateOf("bank") }
    var reference by remember { mutableStateOf("") }
    var clientDropdownExpanded by remember { mutableStateOf(false) }
    var modeDropdownExpanded by remember { mutableStateOf(false) }
    
    val paymentModes = listOf("bank", "upi", "cash", "cheque", "other")
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Income", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("Amount *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    leadingIcon = { Text("₹") }
                )
                
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Description *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    placeholder = { Text("What was this payment for?") }
                )
                
                // Client Dropdown (optional)
                ExposedDropdownMenuBox(
                    expanded = clientDropdownExpanded,
                    onExpandedChange = { clientDropdownExpanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedClient?.name ?: "No client (direct income)",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Client (Optional)") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = clientDropdownExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = clientDropdownExpanded,
                        onDismissRequest = { clientDropdownExpanded = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("No client (direct income)") },
                            onClick = {
                                selectedClient = null
                                clientDropdownExpanded = false
                            }
                        )
                        clients.forEach { client ->
                            DropdownMenuItem(
                                text = { Text(client.name) },
                                onClick = {
                                    selectedClient = client
                                    clientDropdownExpanded = false
                                }
                            )
                        }
                    }
                }
                
                // Payment Mode Dropdown
                ExposedDropdownMenuBox(
                    expanded = modeDropdownExpanded,
                    onExpandedChange = { modeDropdownExpanded = it }
                ) {
                    OutlinedTextField(
                        value = paymentMode.replaceFirstChar { it.uppercase() },
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Payment Mode") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = modeDropdownExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = modeDropdownExpanded,
                        onDismissRequest = { modeDropdownExpanded = false }
                    ) {
                        paymentModes.forEach { mode ->
                            DropdownMenuItem(
                                text = { Text(mode.replaceFirstChar { it.uppercase() }) },
                                onClick = {
                                    paymentMode = mode
                                    modeDropdownExpanded = false
                                }
                            )
                        }
                    }
                }
                
                OutlinedTextField(
                    value = reference,
                    onValueChange = { reference = it },
                    label = { Text("Reference/UTR Number") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    placeholder = { Text("Optional") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { 
                    onAdd(
                        amount.toDoubleOrNull() ?: 0.0,
                        description,
                        selectedClient?.id,
                        paymentMode,
                        reference
                    )
                },
                enabled = amount.isNotBlank() && description.isNotBlank(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
            ) {
                Text("Add Income")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
