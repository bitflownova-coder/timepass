package com.bitflow.finance.ui.screens.tds

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TdsTrackerScreen(
    viewModel: TdsTrackerViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val currentQuarter by viewModel.currentQuarter.collectAsState()
    val summary by viewModel.summary.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val quarters = viewModel.getAvailableQuarters()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("TDS Tracker", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                // Quarter Selector
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(quarters.take(8)) { quarter ->
                        FilterChip(
                            selected = currentQuarter == quarter,
                            onClick = { viewModel.selectQuarter(quarter) },
                            label = { Text(quarter) },
                            leadingIcon = if (currentQuarter == quarter) {
                                { Icon(Icons.Default.Check, contentDescription = null, Modifier.size(16.dp)) }
                            } else null
                        )
                    }
                }
            }

            if (isLoading) {
                item {
                    Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
            } else {
                summary?.let { s ->
                    item {
                        // Summary Card
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f))
                        ) {
                            Column(modifier = Modifier.padding(20.dp)) {
                                Text("TDS Summary - $currentQuarter", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                                Spacer(modifier = Modifier.height(16.dp))
                                Row(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text("Total Revenue", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                        Text("₹${"%,.0f".format(s.totalRevenue)}", fontWeight = FontWeight.Bold)
                                    }
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text("TDS Deducted", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                        Text("₹${"%,.0f".format(s.totalTds)}", fontWeight = FontWeight.Bold, color = Color(0xFFEF4444))
                                    }
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text("Net Received", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                        Text("₹${"%,.0f".format(s.totalRevenue - s.totalTds)}", fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                                    }
                                }
                            }
                        }
                    }

                    item {
                        Text("Invoices with TDS", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
                    }

                    if (s.invoicesWithTds.isEmpty()) {
                        item {
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                            ) {
                                Box(modifier = Modifier.padding(32.dp).fillMaxWidth(), contentAlignment = Alignment.Center) {
                                    Text("No invoices with TDS in this quarter", color = Color.Gray)
                                }
                            }
                        }
                    } else {
                        items(s.invoicesWithTds) { invoice ->
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                            ) {
                                Row(
                                    modifier = Modifier.padding(16.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(invoice.clientName, fontWeight = FontWeight.Bold)
                                        Text(
                                            SimpleDateFormat("dd MMM yyyy", Locale.getDefault()).format(Date(invoice.date)),
                                            style = MaterialTheme.typography.bodySmall,
                                            color = Color.Gray
                                        )
                                    }
                                    Column(horizontalAlignment = Alignment.End) {
                                        Text("₹${"%,.0f".format(invoice.amount)}", fontWeight = FontWeight.Bold)
                                        Text(
                                            "TDS: ₹${"%,.0f".format(invoice.tdsAmount)} (${invoice.tdsRate}%)",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = Color(0xFFEF4444)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
