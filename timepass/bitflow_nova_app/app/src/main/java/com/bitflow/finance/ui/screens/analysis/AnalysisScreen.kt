package com.bitflow.finance.ui.screens.analysis

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.ui.components.FilterChipsRow
import com.bitflow.finance.ui.components.TimeFilter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalysisScreen(
    viewModel: AnalysisViewModel = hiltViewModel(),
    onCashForecastClick: () -> Unit = {}
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedFilter by remember { mutableStateOf(TimeFilter.THIS_MONTH) }

    // Assign colors to breakdown items
    val chartColors = listOf(
        Color(0xFF3B82F6), // PrimaryBlue
        Color(0xFF14B8A6), // AccentTeal
        Color(0xFF8B5CF6), // AccentPurple
        Color(0xFFF59E0B), // AccentAmber
        Color(0xFFEC4899), // AccentRose
        Color(0xFF10B981), // SuccessGreen
        Color(0xFF6366F1)  // Additional Indigo
    )
    val coloredBreakdown = remember(uiState.categoryBreakdown) {
        uiState.categoryBreakdown.mapIndexed { index, item ->
            item.copy(color = chartColors[index % chartColors.size])
        }
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        "Analysis",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold
                    ) 
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
        ) {
            // 1. Time Filter Chips
            FilterChipsRow(
                selectedFilter = selectedFilter,
                onFilterSelected = { 
                    selectedFilter = it
                    viewModel.loadAnalysis(it)
                }
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Forecast Button
            Button(
                onClick = onCashForecastClick,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer, contentColor = MaterialTheme.colorScheme.onTertiaryContainer)
            ) {
                Text("🔮 View Cash Forecast (30 Days)")
            }
            
            Spacer(modifier = Modifier.height(24.dp))

            // 2. Donut Chart
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(300.dp),
                contentAlignment = Alignment.Center
            ) {
                if (coloredBreakdown.isNotEmpty()) {
                    DonutChart(
                        data = coloredBreakdown,
                        totalAmount = uiState.totalExpense,
                        modifier = Modifier.size(260.dp)
                    )
                    
                    // Center Text
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "Total Expense",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = "${uiState.currencySymbol}${uiState.totalExpense.toInt()}",
                            style = MaterialTheme.typography.headlineLarge,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onBackground
                        )
                    }
                } else {
                    Text(
                        "No data for this period",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // 3. Category Breakdown List
            Text(
                text = "Breakdown",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 24.dp)
            ) {
                items(coloredBreakdown) { item ->
                    CategoryBreakdownItem(
                        item = item,
                        currencySymbol = uiState.currencySymbol
                    )
                }
            }
        }
    }
}

@Composable
fun DonutChart(
    data: List<CategoryBreakdown>,
    totalAmount: Double,
    modifier: Modifier = Modifier,
    strokeWidth: Dp = 30.dp
) {
    val animatedProgress = remember { androidx.compose.animation.core.Animatable(0f) }
    
    LaunchedEffect(data) {
        animatedProgress.animateTo(1f, animationSpec = tween(durationMillis = 1000))
    }

    Canvas(modifier = modifier) {
        val center = Offset(size.width / 2, size.height / 2)
        val radius = (size.minDimension - strokeWidth.toPx()) / 2
        
        var startAngle = -90f
        
        data.forEach { item ->
            val sweepAngle = (item.percentage * 360f) * animatedProgress.value
            
            drawArc(
                color = item.color,
                startAngle = startAngle,
                sweepAngle = sweepAngle,
                useCenter = false,
                topLeft = Offset(center.x - radius, center.y - radius),
                size = Size(radius * 2, radius * 2),
                style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round)
            )
            
            startAngle += sweepAngle
        }
    }
}

@Composable
fun CategoryBreakdownItem(
    item: CategoryBreakdown,
    currencySymbol: String
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Icon
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.surfaceVariant),
            contentAlignment = Alignment.Center
        ) {
            Text(text = item.icon, fontSize = 20.sp)
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        // Name & Bar
        Column(modifier = Modifier.weight(1f)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = item.categoryName,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Text(
                    text = "$currencySymbol${item.amount.toInt()}",
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground
                )
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Progress Bar
            LinearProgressIndicator(
                progress = item.percentage,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp)),
                color = item.color,
                trackColor = MaterialTheme.colorScheme.surfaceVariant,
            )
        }
        
        Spacer(modifier = Modifier.width(12.dp))
        
        // Percentage
        Text(
            text = "${(item.percentage * 100).toInt()}%",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(40.dp)
        )
    }
}
