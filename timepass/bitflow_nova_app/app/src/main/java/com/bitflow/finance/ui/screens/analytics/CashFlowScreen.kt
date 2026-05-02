package com.bitflow.finance.ui.screens.analytics

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.TrendingDown
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CashFlowScreen(
    viewModel: CashFlowViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val forecast by viewModel.forecast.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val forecastDays by viewModel.forecastDays.collectAsState()
    val dayOptions = listOf(7, 14, 30, 60, 90)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Cash Flow Forecast", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Period Selector
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                dayOptions.forEach { days ->
                    FilterChip(
                        selected = forecastDays == days,
                        onClick = { viewModel.setForecastDays(days) },
                        label = { Text("${days}d") },
                        leadingIcon = if (forecastDays == days) {
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
                forecast?.let { f ->
                    // Current & Projected Balance Card
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (f.netDailyFlow >= 0) 
                                Color(0xFF10B981).copy(alpha = 0.15f) 
                            else 
                                Color(0xFFEF4444).copy(alpha = 0.15f)
                        )
                    ) {
                        Column(modifier = Modifier.padding(20.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Text("Current Balance", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                    Text(
                                        "₹${"%,.0f".format(f.currentBalance)}",
                                        style = MaterialTheme.typography.headlineSmall,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                                Column(horizontalAlignment = Alignment.End) {
                                    Text("In ${f.forecastDays} Days", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                    Text(
                                        "₹${"%,.0f".format(f.projectedBalance)}",
                                        style = MaterialTheme.typography.headlineSmall,
                                        fontWeight = FontWeight.Bold,
                                        color = if (f.projectedBalance >= f.currentBalance) Color(0xFF10B981) else Color(0xFFEF4444)
                                    )
                                }
                            }
                            
                            Spacer(modifier = Modifier.height(16.dp))
                            
                            // Change indicator
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.Center,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    if (f.netDailyFlow >= 0) Icons.Default.TrendingUp else Icons.Default.TrendingDown,
                                    contentDescription = null,
                                    tint = if (f.netDailyFlow >= 0) Color(0xFF10B981) else Color(0xFFEF4444)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    "${if (f.netDailyFlow >= 0) "+" else ""}₹${"%,.0f".format(f.netDailyFlow * f.forecastDays)}",
                                    fontWeight = FontWeight.Bold,
                                    color = if (f.netDailyFlow >= 0) Color(0xFF10B981) else Color(0xFFEF4444)
                                )
                            }
                        }
                    }

                    // Daily Averages
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // Daily Income
                        Card(
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Daily Income", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text(
                                    "₹${"%,.0f".format(f.dailyIncome)}",
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF10B981)
                                )
                            }
                        }
                        
                        // Daily Expense
                        Card(
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Daily Expense", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text(
                                    "₹${"%,.0f".format(f.dailyExpense)}",
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFFEF4444)
                                )
                            }
                        }
                    }

                    // Net Daily Flow
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp).fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("Net Daily Flow", fontWeight = FontWeight.Medium)
                            Text(
                                "${if (f.netDailyFlow >= 0) "+" else ""}₹${"%,.0f".format(f.netDailyFlow)}/day",
                                fontWeight = FontWeight.Bold,
                                color = if (f.netDailyFlow >= 0) Color(0xFF10B981) else Color(0xFFEF4444)
                            )
                        }
                    }

                    // Insight Card
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = Color(0xFF3B82F6).copy(alpha = 0.15f)
                        )
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("💡 Insight", fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                when {
                                    f.netDailyFlow > 100 -> "Great! You're saving ₹${"%,.0f".format(f.netDailyFlow * 30)} per month at this rate."
                                    f.netDailyFlow > 0 -> "You're on track with a positive cash flow. Keep it up!"
                                    f.netDailyFlow > -50 -> "Your spending is close to your income. Consider reviewing expenses."
                                    else -> "⚠️ Warning: You're spending more than you earn. Review your budget!"
                                },
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}
