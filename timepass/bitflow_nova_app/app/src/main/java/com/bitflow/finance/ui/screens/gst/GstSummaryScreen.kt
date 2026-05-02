package com.bitflow.finance.ui.screens.gst

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GstSummaryScreen(
    viewModel: GstSummaryViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val currentQuarter by viewModel.currentQuarter.collectAsState()
    val summary by viewModel.summary.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val quarters = viewModel.getAvailableQuarters()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("GST Summary", fontWeight = FontWeight.Bold) },
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
        ) {
            // Quarter Selector
            LazyRow(
                modifier = Modifier.padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
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

            if (isLoading) {
                Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                // Summary Cards
                GstSummaryCard(summary)
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // TDS Card
                TdsSummaryCard(summary.tdsCollected)
            }
        }
    }
}

@Composable
fun GstSummaryCard(summary: GstSummary) {
    val primaryColor = Color(0xFF10B981)
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                "GST Collected",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(16.dp))
            
            // Tax Breakdown
            GstRow("Taxable Amount (Subtotal)", summary.subtotal, Color.Gray)
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            GstRow("CGST", summary.cgst, Color(0xFF3B82F6))
            GstRow("SGST", summary.sgst, Color(0xFF8B5CF6))
            GstRow("IGST", summary.igst, Color(0xFFF59E0B))
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            GstRow("Total GST", summary.totalGst, primaryColor, isBold = true)
            Spacer(modifier = Modifier.height(8.dp))
            GstRow("Total Invoice Amount", summary.totalAmount, Color.White, isBold = true)
        }
    }
}

@Composable
fun GstRow(label: String, amount: Double, color: Color, isBold: Boolean = false) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (isBold) FontWeight.Bold else FontWeight.Normal,
            color = color
        )
        Text(
            "₹${"%,.2f".format(amount)}",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (isBold) FontWeight.Bold else FontWeight.Normal,
            color = color
        )
    }
}

@Composable
fun TdsSummaryCard(tds: Double) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f))
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "TDS Deducted",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "Tax Deducted at Source by clients",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.Gray
                )
            }
            Text(
                "₹${"%,.2f".format(tds)}",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFEF4444)
            )
        }
    }
}
