package com.bitflow.finance.ui.screens.home

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.ui.screens.bitflow.BitflowViewModel
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.ui.components.ModeToggle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BusinessDashboardScreen(
    viewModel: BitflowViewModel = hiltViewModel(),
    onGenerateInvoice: () -> Unit,
    onAddExpense: () -> Unit,
    onViewInvoices: () -> Unit,
    currentMode: AppMode,
    onModeChange: (AppMode) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        containerColor = Color(0xFF121212), // Dark theme for Business
        floatingActionButton = {
            FloatingActionButton(
                onClick = onAddExpense,
                containerColor = Color(0xFFBB86FC) // Business Purple
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Expense")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
             // Mode Toggle
            item {
                ModeToggle(
                    currentMode = currentMode,
                    onModeChange = onModeChange,
                    modifier = Modifier.fillMaxWidth().wrapContentWidth(Alignment.CenterHorizontally)
                )
            }
            
            // Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Business Mode",
                            style = MaterialTheme.typography.labelMedium,
                            color = Color.Gray
                        )
                        Text(
                            text = "Dashboard",
                            style = MaterialTheme.typography.headlineMedium,
                            color = Color.White,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    IconButton(onClick = onGenerateInvoice) {
                        Icon(
                            Icons.Default.PostAdd, 
                            contentDescription = "New Invoice",
                            tint = Color(0xFFBB86FC)
                        )
                    }
                }
            }

            // P&L Card
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E)),
                    shape = RoundedCornerShape(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            "Net Profit",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.Gray
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "₹${String.format("%,.0f", uiState.netProfit)}",
                            style = MaterialTheme.typography.displaySmall,
                            fontWeight = FontWeight.Bold,
                            color = if (uiState.netProfit >= 0) Color(0xFF03DAC6) else Color(0xFFCF6679)
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Column {
                                Text("Revenue", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text(
                                    "₹${String.format("%,.0f", uiState.totalRevenue)}",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = Color(0xFF03DAC6)
                                )
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text("Expenses", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text(
                                    "₹${String.format("%,.0f", uiState.totalExpenses)}",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = Color(0xFFCF6679)
                                )
                            }
                        }
                    }
                }
            }

            // Invoice Summary
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E)),
                    shape = RoundedCornerShape(16.dp),
                    modifier = Modifier.fillMaxWidth(),
                    onClick = onViewInvoices
                ) {
                    Row(
                        modifier = Modifier
                            .padding(16.dp)
                            .fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .background(Color(0xFFBB86FC).copy(alpha=0.1f), RoundedCornerShape(8.dp)),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(Icons.Default.Description, null, tint = Color(0xFFBB86FC))
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text("Unpaid Invoices", color = Color.White, fontWeight = FontWeight.Bold)
                                Text("${uiState.unpaidInvoicesCount} Pending", color = Color.Gray, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                        Text(
                            "₹${String.format("%,.0f", uiState.unpaidAmount)}",
                            color = Color(0xFFCF6679),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
            
             // Recent Invoices (Simplified list)
             item {
                 Text("Recent Performance", color = Color.White, style = MaterialTheme.typography.titleMedium)
             }
             
             // Placeholder for chart or list
             item {
                 Box(
                     modifier = Modifier
                        .fillMaxWidth()
                        .height(100.dp)
                        .background(Color(0xFF1E1E1E), RoundedCornerShape(16.dp)),
                     contentAlignment = Alignment.Center
                 ) {
                     Text("Revenue Chart Coming Soon", color = Color.Gray)
                 }
             }
        }
    }
}
