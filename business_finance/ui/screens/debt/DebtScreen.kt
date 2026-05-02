package com.bitflow.finance.ui.screens.debt

import com.bitflow.finance.ui.theme.AppColors
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.DebtEntity


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DebtScreen(
    onBackClick: () -> Unit,
    viewModel: DebtViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Debt Snowball Tracker") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = AppColors.Surface,
                    titleContentColor = AppColors.TextPrimary
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.toggleAddDialog(true) },
                containerColor = AppColors.Primary,
                contentColor = Color.White
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Debt")
            }
        },
        containerColor = AppColors.Background
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            // Summary Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = AppColors.Surface),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Total Debt", style = MaterialTheme.typography.labelMedium, color = AppColors.TextSecondary)
                    Text("₹${uiState.totalDebt}", style = MaterialTheme.typography.headlineMedium, color = AppColors.Expense)
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("Min Payment", style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
                            Text("₹${uiState.totalMinimumMonthlyPayment}", style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            // Debt List
            Text(
                "Your Debts",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                color = AppColors.TextPrimary
            )
            
            LazyColumn(
                contentPadding = PaddingValues(bottom = 80.dp)
            ) {
                items(uiState.debts) { debt ->
                    DebtItem(debt = debt, onDelete = { viewModel.deleteDebt(debt) })
                }
            }
        }
    }
    
    if (uiState.showAddDialog) {
        AddDebtDialog(
            onDismiss = { viewModel.toggleAddDialog(false) },
            onConfirm = { name, amount, rate, minPay, due ->
                viewModel.addDebt(name, amount, rate, minPay, due)
                viewModel.toggleAddDialog(false)
            }
        )
    }
}

@Composable
fun DebtItem(debt: DebtEntity, onDelete: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        colors = CardDefaults.cardColors(containerColor = AppColors.Surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(debt.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                Text("${debt.interestRate}% Interest • Min ₹${debt.minimumPayment}", style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("₹${debt.currentBalance}", style = MaterialTheme.typography.bodyLarge, color = AppColors.Expense, fontWeight = FontWeight.Bold)
                IconButton(onClick = onDelete) {
                    Icon(Icons.Default.Delete, contentDescription = "Delete", tint = Color.Gray, modifier = Modifier.size(20.dp))
                }
            }
        }
    }
}

@Composable
fun AddDebtDialog(onDismiss: () -> Unit, onConfirm: (String, Double, Double, Double, Int) -> Unit) {
    var name by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var rate by remember { mutableStateOf("") }
    var minPay by remember { mutableStateOf("") }
    var dueDay by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Debt") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name (e.g. Credit Card)") })
                OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Current Balance") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = rate, onValueChange = { rate = it }, label = { Text("Interest Rate (%)") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = minPay, onValueChange = { minPay = it }, label = { Text("Minimum Payment") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = dueDay, onValueChange = { dueDay = it }, label = { Text("Due Day (1-31)") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            }
        },
        confirmButton = {
            Button(onClick = {
                val a = amount.toDoubleOrNull() ?: 0.0
                val r = rate.toDoubleOrNull() ?: 0.0
                val m = minPay.toDoubleOrNull() ?: 0.0
                val d = dueDay.toIntOrNull() ?: 1
                if (name.isNotEmpty() && a > 0) {
                    onConfirm(name, a, r, m, d)
                }
            }) {
                Text("Add")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
