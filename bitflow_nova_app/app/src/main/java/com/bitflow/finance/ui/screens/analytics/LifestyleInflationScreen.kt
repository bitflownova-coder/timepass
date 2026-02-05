package com.bitflow.finance.ui.screens.analytics

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material.icons.filled.Warning
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
fun LifestyleInflationScreen(
    viewModel: LifestyleInflationViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val analysis by viewModel.analysis.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Lifestyle Inflation", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            if (isLoading) {
                Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                analysis?.let { a ->
                    // Alert Card
                    val (bgColor, icon, title, subtitle) = when (a.alertLevel) {
                        AlertLevel.SAFE -> Quadruple(
                            Color(0xFF10B981).copy(alpha = 0.15f),
                            "✅",
                            "Spending Under Control",
                            "Your spending has remained stable. Great job!"
                        )
                        AlertLevel.WARNING -> Quadruple(
                            Color(0xFFF59E0B).copy(alpha = 0.15f),
                            "⚠️",
                            "Moderate Increase Detected",
                            "Your spending has increased by ${"%,.1f".format(a.percentageChange)}% compared to the previous 6 months."
                        )
                        AlertLevel.DANGER -> Quadruple(
                            Color(0xFFEF4444).copy(alpha = 0.15f),
                            "🚨",
                            "Lifestyle Inflation Alert!",
                            "Warning: Your spending has increased significantly by ${"%,.1f".format(a.percentageChange)}%!"
                        )
                    }
                    
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = bgColor)
                    ) {
                        Row(
                            modifier = Modifier.padding(20.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(icon, style = MaterialTheme.typography.headlineLarge)
                            Spacer(modifier = Modifier.width(16.dp))
                            Column {
                                Text(title, fontWeight = FontWeight.Bold)
                                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                            }
                        }
                    }

                    // Comparison Card
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Card(
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Previous 6 Months", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text("Avg/Month", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    "₹${"%,.0f".format(a.previousAverage)}",
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                        
                        Card(
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("Last 6 Months", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Text("Avg/Month", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    "₹${"%,.0f".format(a.recentAverage)}",
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = when (a.alertLevel) {
                                        AlertLevel.SAFE -> Color(0xFF10B981)
                                        AlertLevel.WARNING -> Color(0xFFF59E0B)
                                        AlertLevel.DANGER -> Color(0xFFEF4444)
                                    }
                                )
                            }
                        }
                    }

                    // Monthly Breakdown
                    Text("Monthly Spending Trend", fontWeight = FontWeight.Bold)
                    
                    // Simple bar chart
                    val maxAmount = a.monthlyData.maxOfOrNull { it.amount } ?: 1.0
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        a.monthlyData.forEach { month ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    month.month,
                                    modifier = Modifier.width(40.dp),
                                    style = MaterialTheme.typography.labelSmall
                                )
                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .height(24.dp)
                                        .background(
                                            color = MaterialTheme.colorScheme.surfaceVariant,
                                            shape = RoundedCornerShape(4.dp)
                                        )
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .fillMaxHeight()
                                            .fillMaxWidth(fraction = (month.amount / maxAmount).toFloat().coerceIn(0f, 1f))
                                            .background(
                                                color = if (month.isRecent) Color(0xFF3B82F6) else Color(0xFF94A3B8),
                                                shape = RoundedCornerShape(4.dp)
                                            )
                                    )
                                }
                                Text(
                                    "₹${"%,.0f".format(month.amount)}",
                                    modifier = Modifier.width(80.dp).padding(start = 8.dp),
                                    style = MaterialTheme.typography.labelSmall
                                )
                            }
                        }
                    }

                    // Legend
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(modifier = Modifier.size(12.dp).background(Color(0xFF94A3B8), RoundedCornerShape(2.dp)))
                            Text(" Previous 6mo", style = MaterialTheme.typography.labelSmall)
                        }
                        Spacer(modifier = Modifier.width(16.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(modifier = Modifier.size(12.dp).background(Color(0xFF3B82F6), RoundedCornerShape(2.dp)))
                            Text(" Recent 6mo", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
        }
    }
}

private data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)
