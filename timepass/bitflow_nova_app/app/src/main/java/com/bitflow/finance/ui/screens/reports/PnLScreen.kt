package com.bitflow.finance.ui.screens.reports

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PnLScreen(
    viewModel: PnLViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val statement by viewModel.statement.collectAsState()
    val selectedPeriod by viewModel.selectedPeriod.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val periods = viewModel.getAvailablePeriods()
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Profit & Loss", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface),
                actions = {
                    IconButton(
                        onClick = {
                            val intent = viewModel.exportToPdf()
                            if (intent != null) {
                                context.startActivity(intent)
                            } else {
                                Toast.makeText(context, "No data to export", Toast.LENGTH_SHORT).show()
                            }
                        }
                    ) {
                        Icon(Icons.Default.Share, contentDescription = "Export PDF")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
        ) {
            // Period Selector
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                periods.forEach { period ->
                    FilterChip(
                        selected = selectedPeriod == period,
                        onClick = { viewModel.selectPeriod(period) },
                        label = { Text(period, style = MaterialTheme.typography.labelSmall) },
                        leadingIcon = if (selectedPeriod == period) {
                            { Icon(Icons.Default.Check, contentDescription = null, Modifier.size(14.dp)) }
                        } else null
                    )
                }
            }

            if (isLoading) {
                Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                statement?.let { stmt ->
                    // Revenue Card
                    PnLCard(
                        title = "Revenue",
                        items = listOf(
                            "Invoice Revenue" to stmt.revenue
                        ),
                        total = Pair("Gross Profit", stmt.grossProfit),
                        totalColor = Color(0xFF10B981)
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // Expenses Card
                    PnLCard(
                        title = "Expenses",
                        items = listOf(
                            "Operating Expenses" to stmt.operatingExpenses
                        ),
                        total = Pair("Total Expenses", stmt.operatingExpenses),
                        totalColor = Color(0xFFEF4444)
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // Net Profit Card
                    Card(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (stmt.netProfit >= 0) 
                                Color(0xFF10B981).copy(alpha = 0.15f) 
                            else 
                                Color(0xFFEF4444).copy(alpha = 0.15f)
                        )
                    ) {
                        Row(
                            modifier = Modifier.padding(20.dp).fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Net Profit", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                            Text(
                                "₹${"%,.2f".format(stmt.netProfit)}",
                                style = MaterialTheme.typography.headlineSmall,
                                fontWeight = FontWeight.Bold,
                                color = if (stmt.netProfit >= 0) Color(0xFF10B981) else Color(0xFFEF4444)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Stats
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        StatChip("${stmt.invoiceCount} Invoices", Color(0xFF3B82F6))
                        StatChip("${stmt.expenseCount} Expenses", Color(0xFFF59E0B))
                    }
                }
            }
        }
    }
}

@Composable
fun PnLCard(
    title: String,
    items: List<Pair<String, Double>>,
    total: Pair<String, Double>,
    totalColor: Color
) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            items.forEach { (label, value) ->
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(label, style = MaterialTheme.typography.bodyMedium)
                    Text("₹${"%,.2f".format(value)}", style = MaterialTheme.typography.bodyMedium)
                }
                Spacer(modifier = Modifier.height(4.dp))
            }
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(total.first, fontWeight = FontWeight.Bold, color = totalColor)
                Text("₹${"%,.2f".format(total.second)}", fontWeight = FontWeight.Bold, color = totalColor)
            }
        }
    }
}

@Composable
fun StatChip(text: String, color: Color) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = color.copy(alpha = 0.15f)
    ) {
        Text(
            text,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelMedium,
            color = color
        )
    }
}
