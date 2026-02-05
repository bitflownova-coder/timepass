package com.bitflow.finance.ui.screens.investments

import com.bitflow.finance.ui.theme.AppColors
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.TrendingDown
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.AssetType
import com.bitflow.finance.data.local.entity.HoldingEntity


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InvestmentScreen(
    onBackClick: () -> Unit,
    viewModel: InvestmentViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Investment Portfolio") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = AppColors.Surface)
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.toggleAddDialog(true) },
                containerColor = AppColors.Primary,
                contentColor = Color.White
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Holding")
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
                    Text("Net Worth (Investments)", style = MaterialTheme.typography.labelMedium, color = AppColors.TextSecondary)
                    Text("₹${String.format("%,.0f", uiState.totalCurrentValue)}", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column {
                            Text("Invested", style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
                            Text("₹${String.format("%,.0f", uiState.totalInvested)}", style = MaterialTheme.typography.bodyLarge)
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("Returns", style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    if (uiState.totalProfitLoss >= 0) Icons.Default.TrendingUp else Icons.Default.TrendingDown,
                                    contentDescription = null,
                                    tint = if (uiState.totalProfitLoss >= 0) AppColors.Income else AppColors.Expense,
                                    modifier = Modifier.size(16.dp)
                                )
                                Text(
                                    "${if (uiState.totalProfitLoss >= 0) "+" else ""}₹${String.format("%,.0f", uiState.totalProfitLoss)} (${String.format("%.1f", uiState.returnsPercentage)}%)",
                                    style = MaterialTheme.typography.bodyLarge,
                                    color = if (uiState.totalProfitLoss >= 0) AppColors.Income else AppColors.Expense,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }
            }

            // Holdings List
            Text(
                "Holdings",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )

            LazyColumn(
                contentPadding = PaddingValues(bottom = 80.dp)
            ) {
                items(uiState.holdings) { holding ->
                    HoldingItem(holding, onDelete = { viewModel.deleteHolding(holding) })
                }
            }
        }
    }

    if (uiState.showAddDialog) {
        AddHoldingDialog(
            onDismiss = { viewModel.toggleAddDialog(false) },
            onConfirm = { name, type, qty, buy, market ->
                viewModel.addHolding(name, type, qty, buy, market)
                viewModel.toggleAddDialog(false)
            }
        )
    }
}

@Composable
fun HoldingItem(holding: HoldingEntity, onDelete: () -> Unit) {
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
                Text(holding.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Text(holding.type.name.replace("_", " "), style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
                Text("${holding.quantity} units @ ₹${holding.averageBuyPrice}", style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("₹${String.format("%,.0f", holding.currentValue)}", style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val pl = holding.profitLoss
                    Text(
                        "${if (pl >= 0) "+" else ""}₹${String.format("%,.0f", pl)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = if (pl >= 0) AppColors.Income else AppColors.Expense
                    )
                    IconButton(onClick = onDelete, modifier = Modifier.size(24.dp).padding(start = 4.dp)) {
                        Icon(Icons.Default.Delete, contentDescription = "Delete", tint = Color.Gray, modifier = Modifier.size(16.dp))
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddHoldingDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, AssetType, Double, Double, Double) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var type by remember { mutableStateOf(AssetType.STOCK) }
    var quantity by remember { mutableStateOf("") }
    var buyPrice by remember { mutableStateOf("") }
    var marketPrice by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Holding") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name (e.g. Reliance)") })
                
                Box {
                    OutlinedTextField(
                        value = type.name,
                        onValueChange = {},
                        label = { Text("Type") },
                        readOnly = true,
                        trailingIcon = { IconButton(onClick = { expanded = true }) { Icon(Icons.Default.ArrowBack, contentDescription = null) } }, // Placeholder icon
                        modifier = Modifier.clickable { expanded = true }
                    )
                    DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        AssetType.values().forEach { assetType ->
                            DropdownMenuItem(
                                text = { Text(assetType.name) },
                                onClick = {
                                    type = assetType
                                    expanded = false
                                }
                            )
                        }
                    }
                }
                
                OutlinedTextField(value = quantity, onValueChange = { quantity = it }, label = { Text("Quantity") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = buyPrice, onValueChange = { buyPrice = it }, label = { Text("Avg Buy Price") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = marketPrice, onValueChange = { marketPrice = it }, label = { Text("Current Market Price") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            }
        },
        confirmButton = {
            Button(onClick = {
                val q = quantity.toDoubleOrNull() ?: 0.0
                val b = buyPrice.toDoubleOrNull() ?: 0.0
                val m = marketPrice.toDoubleOrNull() ?: 0.0
                if (name.isNotEmpty() && q > 0) {
                    onConfirm(name, type, q, b, m)
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
