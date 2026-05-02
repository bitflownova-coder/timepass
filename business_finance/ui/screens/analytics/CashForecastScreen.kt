package com.bitflow.finance.ui.screens.analytics

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.usecase.DailyBalanceProjection
import com.bitflow.finance.domain.model.ActivityType
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CashForecastScreen(
    viewModel: CashForecastViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Cash Forecast", fontWeight = FontWeight.Bold)
                        Text("Next 30 Days", style = MaterialTheme.typography.bodySmall)
                    }
                },
                navigationIcon = {
                    // Add Back Icon call here if needed, or rely on caller
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { padding ->
        if (uiState.isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // 1. Summary Card
                item {
                    ForecastSummaryCard(uiState)
                }

                // 2. Chart
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth().height(300.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha=0.3f))
                    ) {
                        Column(Modifier.padding(16.dp)) {
                            Text("Balance Projection", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(16.dp))
                            ForecastLineChart(uiState.projections, uiState.minBalance, uiState.maxBalance)
                        }
                    }
                }

                // 3. Alerts
                uiState.lowBalanceDate?.let { date ->
                    item {
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFFEF2F2)), // Light Red
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                                Text("⚠️", style = MaterialTheme.typography.headlineMedium)
                                Spacer(Modifier.width(12.dp))
                                Column {
                                    Text("Low Balance Warning", fontWeight = FontWeight.Bold, color = Color(0xFFDC2626))
                                    Text(
                                        "Projected to drop below 5k on ${date.format(DateTimeFormatter.ofPattern("MMM dd"))}",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = Color(0xFFDC2626)
                                    )
                                }
                            }
                        }
                    }
                }
                
                // 4. Safe to Spend
                item {
                     Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFECFDF5)), // Light Green
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text("✅", style = MaterialTheme.typography.headlineMedium)
                            Spacer(Modifier.width(12.dp))
                            Column {
                                Text("Safe to Spend", fontWeight = FontWeight.Bold, color = Color(0xFF059669))
                                Text(
                                    "You can spend ₹${uiState.safeToSpendDaily.toInt()}/day comfortably.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = Color(0xFF059669)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ForecastSummaryCard(state: CashForecastUiState) {
    val endBalance = state.projections.lastOrNull()?.endingBalance ?: 0.0
    val startBalance = state.projections.firstOrNull()?.startingBalance ?: 0.0
    val diff = endBalance - startBalance
    val isPositive = diff >= 0

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Column(Modifier.padding(24.dp)) {
            Text("Expected Balance (30 Days)", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha=0.7f))
            Text(
                "₹${"%,.0f".format(endBalance)}",
                style = MaterialTheme.typography.displayMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if(isPositive) "▲ +₹${"%,.0f".format(diff)}" else "▼ -₹${"%,.0f".format(Math.abs(diff))}",
                    color = if(isPositive) Color(0xFF059669) else Color(0xFFDC2626),
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge
                )
                Text(
                    " vs Today",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha=0.7f)
                )
            }
        }
    }
}

@Composable
fun ForecastLineChart(data: List<DailyBalanceProjection>, min: Double, max: Double) {
    if (data.isEmpty()) return

    Canvas(modifier = Modifier.fillMaxWidth().height(200.dp)) {
        val width = size.width
        val height = size.height
        val padding = 20f

        val xStep = width / (data.size - 1).coerceAtLeast(1)
        // Normalize Y: Map [min, max] to [height, 0] (inverted Y)
        val range = (max - min).coerceAtLeast(1.0)
        
        fun y(valY: Double): Float {
            val normalized = (valY - min) / range
            return (height - padding) - (normalized * (height - 2 * padding)).toFloat() - padding
        }

        val path = Path()
        data.forEachIndexed { index, point ->
            val x = index * xStep
            val yPos = y(point.endingBalance)
            if (index == 0) path.moveTo(x, yPos) else path.lineTo(x, yPos)
        }
        
        // Draw Fill Gradient
        val fillPath = Path()
        fillPath.addPath(path)
        fillPath.lineTo(width, height)
        fillPath.lineTo(0f, height)
        fillPath.close()
        
        drawPath(
            path = fillPath,
            brush = Brush.verticalGradient(
                colors = listOf(
                    Color(0xFF3B82F6).copy(alpha = 0.3f),
                    Color(0xFF3B82F6).copy(alpha = 0.0f)
                )
            )
        )

        // Draw Line
        drawPath(
            path = path,
            color = Color(0xFF3B82F6),
            style = Stroke(width = 3.dp.toPx(), cap = StrokeCap.Round)
        )
        
        // Draw Threshold Line (5000)
        val thresholdY = y(5000.0)
        if (thresholdY in 0f..height) {
            drawLine(
                color = Color.Red.copy(alpha = 0.5f),
                start = Offset(0f, thresholdY),
                end = Offset(width, thresholdY),
                strokeWidth = 1.dp.toPx(),
                pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(10f, 10f))
            )
        }
    }
}
