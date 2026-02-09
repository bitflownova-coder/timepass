package com.bitflow.finance.ui.screens.simple_finance

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.ClientDiscussionEntity
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClientsScreen(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    onBackClick: () -> Unit,
    onClientClick: (Long) -> Unit
) {
    val clients by viewModel.clients.collectAsState()
    val discussions by viewModel.discussions.collectAsState()
    
    var showAddClientDialog by remember { mutableStateOf(false) }
    var showAddDiscussionDialog by remember { mutableStateOf(false) }
    var selectedClientForDiscussion by remember { mutableStateOf<ClientEntity?>(null) }
    var selectedTab by remember { mutableStateOf(0) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Clients & Discussions", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { 
                    if (selectedTab == 0) showAddClientDialog = true 
                    else if (clients.isNotEmpty()) showAddDiscussionDialog = true
                },
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Tabs
            TabRow(selectedTabIndex = selectedTab) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("Clients (${clients.size})") }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("Discussions (${discussions.size})") }
                )
            }
            
            when (selectedTab) {
                0 -> ClientsList(
                    clients = clients,
                    discussions = discussions,
                    onClientClick = onClientClick,
                    onAddDiscussion = { client ->
                        selectedClientForDiscussion = client
                        showAddDiscussionDialog = true
                    },
                    viewModel = viewModel
                )
                1 -> DiscussionsList(
                    discussions = discussions,
                    clients = clients,
                    viewModel = viewModel
                )
            }
        }
    }
    
    // Add Client Dialog
    if (showAddClientDialog) {
        AddClientDialog(
            onDismiss = { showAddClientDialog = false },
            onAdd = { name, email, phone, address, gstin ->
                viewModel.addClient(name, email, phone, address, gstin)
                showAddClientDialog = false
            }
        )
    }
    
    // Add Discussion Dialog
    if (showAddDiscussionDialog) {
        AddDiscussionDialog(
            clients = clients,
            preselectedClient = selectedClientForDiscussion,
            onDismiss = { 
                showAddDiscussionDialog = false
                selectedClientForDiscussion = null
            },
            onAdd = { clientId, title, description, amount ->
                viewModel.addDiscussion(clientId, title, description, amount)
                showAddDiscussionDialog = false
                selectedClientForDiscussion = null
            }
        )
    }
}

@Composable
fun ClientsList(
    clients: List<ClientEntity>,
    discussions: List<ClientDiscussionEntity>,
    onClientClick: (Long) -> Unit,
    onAddDiscussion: (ClientEntity) -> Unit,
    viewModel: SimpleFinanceViewModel
) {
    if (clients.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    Icons.Default.People,
                    contentDescription = null,
                    modifier = Modifier.size(64.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                )
                Spacer(Modifier.height(16.dp))
                Text(
                    "No clients yet",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    "Add your first client to start tracking",
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
            items(clients) { client ->
                val clientDiscussions = discussions.filter { it.clientId == client.id }
                val pendingAmount = clientDiscussions
                    .filter { it.status == "pending" }
                    .sumOf { it.expectedAmount }
                
                ClientCard(
                    client = client,
                    pendingDiscussions = clientDiscussions.filter { it.status == "pending" }.size,
                    pendingAmount = pendingAmount,
                    onClick = { onClientClick(client.id) },
                    onAddDiscussion = { onAddDiscussion(client) },
                    onDelete = { viewModel.deleteClient(client) }
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClientCard(
    client: ClientEntity,
    pendingDiscussions: Int,
    pendingAmount: Double,
    onClick: () -> Unit,
    onAddDiscussion: () -> Unit,
    onDelete: () -> Unit
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    var showMenu by remember { mutableStateOf(false) }
    
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .background(
                                Color(0xFF6366F1).copy(alpha = 0.1f),
                                CircleShape
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = client.name.take(2).uppercase(),
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF6366F1)
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text(
                            client.name,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        if (client.email.isNotEmpty()) {
                            Text(
                                client.email,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
                
                Box {
                    IconButton(onClick = { showMenu = true }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "Menu")
                    }
                    DropdownMenu(
                        expanded = showMenu,
                        onDismissRequest = { showMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("Add Discussion") },
                            onClick = { 
                                showMenu = false
                                onAddDiscussion()
                            },
                            leadingIcon = { Icon(Icons.Default.Add, null) }
                        )
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
            
            if (pendingDiscussions > 0) {
                Spacer(Modifier.height(12.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            Color(0xFF8B5CF6).copy(alpha = 0.1f),
                            RoundedCornerShape(8.dp)
                        )
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "$pendingDiscussions pending discussions",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF8B5CF6)
                    )
                    Text(
                        currencyFormat.format(pendingAmount),
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF8B5CF6),
                        fontSize = 14.sp
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiscussionsList(
    discussions: List<ClientDiscussionEntity>,
    clients: List<ClientEntity>,
    viewModel: SimpleFinanceViewModel
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    
    var selectedFilter by remember { mutableStateOf("all") }
    val filteredDiscussions = when (selectedFilter) {
        "pending" -> discussions.filter { it.status == "pending" }
        "finalized" -> discussions.filter { it.status == "finalized" }
        else -> discussions
    }
    
    if (discussions.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    Icons.Default.Chat,
                    contentDescription = null,
                    modifier = Modifier.size(64.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                )
                Spacer(Modifier.height(16.dp))
                Text(
                    "No discussions yet",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    "Add a discussion from a client card",
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
            // Filter chips
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(
                        selected = selectedFilter == "all",
                        onClick = { selectedFilter = "all" },
                        label = { Text("All") }
                    )
                    FilterChip(
                        selected = selectedFilter == "pending",
                        onClick = { selectedFilter = "pending" },
                        label = { Text("Pending") }
                    )
                    FilterChip(
                        selected = selectedFilter == "finalized",
                        onClick = { selectedFilter = "finalized" },
                        label = { Text("Finalized") }
                    )
                }
            }
            
            items(filteredDiscussions) { discussion ->
                val client = clients.find { it.id == discussion.clientId }
                var showUpdateDialog by remember { mutableStateOf(false) }
                var showConvertDialog by remember { mutableStateOf(false) }
                var showRevertDialog by remember { mutableStateOf(false) }
                
                DiscussionDetailCard(
                    discussion = discussion,
                    clientName = client?.name ?: "Unknown",
                    onUpdate = { showUpdateDialog = true },
                    onConvert = { showConvertDialog = true },
                    onDelete = { viewModel.deleteDiscussion(discussion) },
                    onRevert = { showRevertDialog = true }
                )
                
                if (showUpdateDialog) {
                    UpdateDiscussionDialog(
                        discussion = discussion,
                        onDismiss = { showUpdateDialog = false },
                        onUpdate = { newAmount, notes ->
                            viewModel.updateDiscussionAmount(discussion.id, newAmount, notes)
                            showUpdateDialog = false
                        }
                    )
                }
                
                if (showConvertDialog) {
                    ConvertToPaymentDialog(
                        discussion = discussion,
                        onDismiss = { showConvertDialog = false },
                        onConvert = { paymentMode, reference ->
                            viewModel.convertToPayment(discussion, paymentMode, reference)
                            showConvertDialog = false
                        }
                    )
                }
                
                if (showRevertDialog) {
                    AlertDialog(
                        onDismissRequest = { showRevertDialog = false },
                        title = { Text("Revert to Pending?", fontWeight = FontWeight.Bold) },
                        text = {
                            Text("This will change the discussion status back to pending and delete the associated income payment. You can then re-negotiate this discussion.")
                        },
                        confirmButton = {
                            Button(
                                onClick = {
                                    viewModel.revertDiscussion(discussion.id)
                                    showRevertDialog = false
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF59E0B))
                            ) {
                                Text("Revert")
                            }
                        },
                        dismissButton = {
                            TextButton(onClick = { showRevertDialog = false }) {
                                Text("Cancel")
                            }
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun DiscussionDetailCard(
    discussion: ClientDiscussionEntity,
    clientName: String,
    onUpdate: () -> Unit,
    onConvert: () -> Unit,
    onDelete: () -> Unit,
    onRevert: () -> Unit = {}
) {
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    val statusColor = when (discussion.status) {
        "pending" -> Color(0xFFF59E0B)
        "finalized" -> Color(0xFF10B981)
        "cancelled" -> Color(0xFFEF4444)
        else -> Color(0xFF6B7280)
    }
    
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        discussion.title,
                        fontWeight = FontWeight.Bold,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        clientName,
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF6366F1)
                    )
                }
                Surface(
                    color = statusColor.copy(alpha = 0.1f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        discussion.status.replaceFirstChar { it.uppercase() },
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        color = statusColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
            
            Spacer(Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        "Expected Amount",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        currencyFormat.format(discussion.expectedAmount),
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                        color = Color(0xFF8B5CF6)
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "Last Updated",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        dateFormat.format(Date(discussion.lastUpdated)),
                        fontWeight = FontWeight.Medium
                    )
                }
            }
            
            if (discussion.notes.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                Text(
                    "Notes: ${discussion.notes}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2
                )
            }
            
            if (discussion.status == "pending") {
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(
                        onClick = onUpdate,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Update Amount")
                    }
                    Button(
                        onClick = onConvert,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                    ) {
                        Text("Convert")
                    }
                }
            }
            
            if (discussion.status == "finalized") {
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = onRevert,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFF59E0B))
                ) {
                    Icon(Icons.Default.Undo, null, Modifier.size(16.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Revert to Pending")
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddClientDialog(
    onDismiss: () -> Unit,
    onAdd: (name: String, email: String, phone: String, address: String, gstin: String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var address by remember { mutableStateOf("") }
    var gstin by remember { mutableStateOf("") }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Client", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Client Name *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text("Email") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
                )
                OutlinedTextField(
                    value = phone,
                    onValueChange = { phone = it },
                    label = { Text("Phone") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone)
                )
                OutlinedTextField(
                    value = address,
                    onValueChange = { address = it },
                    label = { Text("Address") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 2
                )
                OutlinedTextField(
                    value = gstin,
                    onValueChange = { gstin = it },
                    label = { Text("GSTIN") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onAdd(name, email, phone, address, gstin) },
                enabled = name.isNotBlank()
            ) {
                Text("Add Client")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddDiscussionDialog(
    clients: List<ClientEntity>,
    preselectedClient: ClientEntity?,
    onDismiss: () -> Unit,
    onAdd: (clientId: Long, title: String, description: String, amount: Double) -> Unit
) {
    var selectedClient by remember { mutableStateOf(preselectedClient) }
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var clientDropdownExpanded by remember { mutableStateOf(false) }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Discussion", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                // Client Dropdown
                ExposedDropdownMenuBox(
                    expanded = clientDropdownExpanded,
                    onExpandedChange = { clientDropdownExpanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedClient?.name ?: "",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Select Client *") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = clientDropdownExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = clientDropdownExpanded,
                        onDismissRequest = { clientDropdownExpanded = false }
                    ) {
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
                
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Work/Project Title *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Description") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3
                )
                
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("Expected Amount *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    leadingIcon = { Text("₹") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { 
                    selectedClient?.let { client ->
                        onAdd(client.id, title, description, amount.toDoubleOrNull() ?: 0.0)
                    }
                },
                enabled = selectedClient != null && title.isNotBlank() && amount.isNotBlank()
            ) {
                Text("Add Discussion")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@Composable
fun UpdateDiscussionDialog(
    discussion: ClientDiscussionEntity,
    onDismiss: () -> Unit,
    onUpdate: (newAmount: Double, notes: String) -> Unit
) {
    var amount by remember { mutableStateOf(discussion.expectedAmount.toString()) }
    var notes by remember { mutableStateOf("") }
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Update Discussion", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    "Current: ${currencyFormat.format(discussion.expectedAmount)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("New Amount") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    leadingIcon = { Text("₹") }
                )
                
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Update Notes") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3,
                    placeholder = { Text("Reason for change") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onUpdate(amount.toDoubleOrNull() ?: discussion.expectedAmount, notes) },
                enabled = amount.isNotBlank()
            ) {
                Text("Update")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConvertToPaymentDialog(
    discussion: ClientDiscussionEntity,
    onDismiss: () -> Unit,
    onConvert: (paymentMode: String, reference: String) -> Unit
) {
    var paymentMode by remember { mutableStateOf("bank") }
    var reference by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    val paymentModes = listOf("bank", "upi", "cash", "cheque", "other")
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Convert to Payment", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.1f))
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Amount to be recorded", style = MaterialTheme.typography.bodySmall)
                        Text(
                            currencyFormat.format(discussion.expectedAmount),
                            fontWeight = FontWeight.Bold,
                            fontSize = 24.sp,
                            color = Color(0xFF10B981)
                        )
                    }
                }
                
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    OutlinedTextField(
                        value = paymentMode.replaceFirstChar { it.uppercase() },
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Payment Mode") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        paymentModes.forEach { mode ->
                            DropdownMenuItem(
                                text = { Text(mode.replaceFirstChar { it.uppercase() }) },
                                onClick = {
                                    paymentMode = mode
                                    expanded = false
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
                onClick = { onConvert(paymentMode, reference) },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
            ) {
                Text("Confirm Payment")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
