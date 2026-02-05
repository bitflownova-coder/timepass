package com.bitflow.finance.ui.screens.accounts

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.outlined.AccountBalance
import androidx.compose.material.icons.outlined.AccountBalanceWallet
import androidx.compose.material.icons.outlined.CreditCard
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.model.AccountType
import com.bitflow.finance.domain.model.AppMode

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountsScreen(
    viewModel: AccountsViewModel = hiltViewModel()
) {
    val accounts by viewModel.accounts.collectAsState()
    val currentMode by viewModel.currentMode.collectAsState()
    var showDialog by remember { mutableStateOf(false) }
    var accountToEdit by remember { mutableStateOf<Account?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        "Accounts",
                        fontWeight = FontWeight.Bold
                    ) 
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { 
                    accountToEdit = null
                    showDialog = true 
                },
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Account")
            }
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        if (accounts.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Outlined.AccountBalanceWallet,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "No accounts yet",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Tap + to add your first account",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                items(accounts) { account ->
                    AccountItem(
                        account = account,
                        onClick = {
                            accountToEdit = account
                            showDialog = true
                        }
                    )
                }
            }
        }
    }

    if (showDialog) {
        AccountDialog(
            initialContext = currentMode,
            existingAccount = accountToEdit,
            onDismiss = { showDialog = false },
            onConfirm = { name, type, balance, currency, context ->
                if (accountToEdit == null) {
                    viewModel.addAccount(name, type, balance, currency, context)
                } else {
                    viewModel.updateAccount(
                        accountToEdit!!.copy(
                            name = name,
                            type = type,
                            initialBalance = balance, // Update initial or current? Usually updating account updates details, but balance is tricky.
                            // For simplicity, let's say we update the initial balance property, but current balance logic might be complex if we track transactions.
                            // If we just want to update metadata (Context, Name, Type), we should preserve balance.
                            // But usually user wants to correct balance.
                            // Let's assume we update currentBalance too if it matches initial?
                            // Or just update metadata and currency.
                            // Let's update basic fields and Context. 
                            // WARNING: Changing currency might break things if transactions exist.
                            currency = currency,
                            context = context
                        )
                    )
                }
                showDialog = false
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountItem(account: Account, onClick: () -> Unit) {
    val accountColor = getAccountColor(account.name)
    val icon = when (account.type) {
        AccountType.BANK -> Icons.Outlined.AccountBalance
        AccountType.CASH -> Icons.Outlined.AccountBalanceWallet
        AccountType.CREDIT_CARD -> Icons.Outlined.CreditCard
        AccountType.WALLET -> Icons.Outlined.AccountBalanceWallet
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        onClick = onClick
    ) {
        Row(
            modifier = Modifier
                .padding(20.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(accountColor.copy(alpha = 0.12f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = accountColor,
                    modifier = Modifier.size(24.dp)
                )
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = account.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = account.type.name,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = formatCurrency(account.currentBalance, account.currency),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
        }
    }
}

private fun formatCurrency(amount: Double, symbol: String): String {
    return when {
        amount >= 10_000_000 -> "$symbol %.2fCr".format(amount / 10_000_000)
        amount >= 100_000 -> "$symbol %.2fL".format(amount / 100_000)
        amount >= 1_000 -> "$symbol %.2fK".format(amount / 1_000)
        else -> "$symbol %.2f".format(amount)
    }
}

private fun getAccountColor(accountName: String): Color {
    val colors = listOf(
        Color(0xFF3B82F6), // PrimaryBlue
        Color(0xFF14B8A6), // AccentTeal
        Color(0xFF8B5CF6), // AccentPurple
        Color(0xFFF59E0B), // AccentAmber
        Color(0xFFEC4899), // AccentRose
        Color(0xFF10B981)  // SuccessGreen
    )
    return colors[accountName.hashCode().mod(colors.size)]
}


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountDialog(
    initialContext: AppMode,
    existingAccount: Account? = null,
    onDismiss: () -> Unit,
    onConfirm: (String, AccountType, Double, String, AppMode) -> Unit
) {
    var name by remember { mutableStateOf(existingAccount?.name ?: "") }
    var balance by remember { mutableStateOf(existingAccount?.initialBalance?.toString() ?: "") }
    var selectedType by remember { mutableStateOf(existingAccount?.type ?: AccountType.BANK) }
    var selectedCurrency by remember { mutableStateOf(existingAccount?.currency ?: "₹") }
    var selectedContext by remember { mutableStateOf(existingAccount?.context ?: initialContext) }
    var expanded by remember { mutableStateOf(false) }
    var currencyExpanded by remember { mutableStateOf(false) }
    val currencies = listOf("₹", "$", "€", "£", "¥")

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (existingAccount == null) "Add Account" else "Edit Account") },
        text = {
            Column {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Account Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = balance,
                    onValueChange = { balance = it },
                    label = { Text("Initial Balance") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                
                // Context Switcher
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                   FilterChip(
                       selected = selectedContext == AppMode.PERSONAL,
                       onClick = { selectedContext = AppMode.PERSONAL },
                       label = { Text("Personal") },
                       leadingIcon = {
                           if (selectedContext == AppMode.PERSONAL) {
                               Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                           }
                       }
                   )
                   FilterChip(
                       selected = selectedContext == AppMode.BUSINESS,
                       onClick = { selectedContext = AppMode.BUSINESS },
                       label = { Text("Business") },
                       leadingIcon = {
                           if (selectedContext == AppMode.BUSINESS) {
                               Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                           }
                       }
                   )
                }
                
                Spacer(modifier = Modifier.height(8.dp))

                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded }
                ) {
                    OutlinedTextField(
                        value = selectedType.name,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Account Type") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        AccountType.values().forEach { type ->
                            DropdownMenuItem(
                                text = { Text(type.name) },
                                onClick = {
                                    selectedType = type
                                    expanded = false
                                }
                            )
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                Text("Currency", style = MaterialTheme.typography.labelMedium)
                Box {
                    OutlinedButton(
                        onClick = { currencyExpanded = true },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(selectedCurrency)
                    }
                    DropdownMenu(
                        expanded = currencyExpanded,
                        onDismissRequest = { currencyExpanded = false }
                    ) {
                        currencies.forEach { currency ->
                            DropdownMenuItem(
                                text = { Text(currency) },
                                onClick = {
                                    selectedCurrency = currency
                                    currencyExpanded = false
                                }
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val balanceValue = balance.toDoubleOrNull() ?: 0.0
                    if (name.isNotBlank()) {
                        onConfirm(name, selectedType, balanceValue, selectedCurrency, selectedContext)
                    }
                }
            ) {
                Text(if (existingAccount == null) "Add" else "Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

