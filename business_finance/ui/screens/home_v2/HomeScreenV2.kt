package com.bitflow.finance.ui.screens.home_v2

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.DailyPulse
import com.bitflow.finance.domain.model.PulseStatus
import com.bitflow.finance.domain.model.SubscriptionDetectionCard

/**
 * Redesigned Home Screen - "Peace of Mind" Dashboard
 * 
 * Key Changes:
 * - Daily Pulse replaces Net Worth
 * - Safe-to-Spend metric (not complex budgets)
 * - Subscription Detective cards
 * - Simplified activity list
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreenV2(
    viewModel: HomeViewModelV2 = hiltViewModel(),
    onAddActivityClick: () -> Unit,
    onActivityClick: (Long) -> Unit,
    onInsightsClick: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = uiState.greeting,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = uiState.userName,
                            style = MaterialTheme.typography.titleMedium
                        )
                    }
                },
                actions = {
                    // Simple Privacy Toggle (no shake needed)
                    IconButton(onClick = { viewModel.togglePrivacyMode() }) {
                        Icon(
                            imageVector = if (uiState.isPrivacyMode) 
                                Icons.Default.VisibilityOff 
                            else 
                                Icons.Default.Visibility,
                            contentDescription = "Privacy"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onAddActivityClick,
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Activity")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Daily Pulse - The "Peace of Mind" Metric
            item {
                DailyPulseCard(
                    dailyPulse = uiState.dailyPulse,
                    currencySymbol = uiState.currencySymbol,
                    isPrivacyMode = uiState.isPrivacyMode
                )
            }

            // Subscription Detective Cards
            if (uiState.detectedSubscriptions.isNotEmpty()) {
                item {
                    Text(
                        "We noticed these recurring payments",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }

                items(uiState.detectedSubscriptions) { subscription ->
                    SubscriptionDetectionCardItem(
                        subscription = subscription,
                        currencySymbol = uiState.currencySymbol,
                        onYesClick = { viewModel.confirmSubscription(subscription.id) },
                        onNoClick = { viewModel.dismissSubscription(subscription.id) }
                    )
                }
            }

            // Recent Activities (simplified)
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "Recent Activity",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    TextButton(onClick = onInsightsClick) {
                        Text("View Insights")
                    }
                }
            }

            items(uiState.recentActivities) { activity ->
                ActivityListItem(
                    activity = activity,
                    currencySymbol = uiState.currencySymbol,
                    isPrivacyMode = uiState.isPrivacyMode,
                    onClick = { onActivityClick(activity.id) }
                )
            }
        }
    }
}

/**
 * Daily Pulse Card - Shows "Safe to Spend" amount with a visual gauge
 */
@Composable
fun DailyPulseCard(
    dailyPulse: DailyPulse,
    currencySymbol: String,
    isPrivacyMode: Boolean
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(240.dp),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(
            containerColor = when (dailyPulse.pulseStatus) {
                PulseStatus.GREAT, PulseStatus.GOOD -> Color(0xFF66BB6A)
                PulseStatus.CAUTION -> Color(0xFFFFA726)
                PulseStatus.SLOW_DOWN -> Color(0xFFEF5350)
            }
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            Column(
                modifier = Modifier.align(Alignment.TopStart)
            ) {
                Text(
                    text = "Today's Pulse",
                    color = Color.White.copy(alpha = 0.9f),
                    style = MaterialTheme.typography.labelLarge
                )
                Spacer(modifier = Modifier.height(8.dp))
                
                if (!isPrivacyMode) {
                    Text(
                        text = "$currencySymbol ${String.format("%.0f", dailyPulse.safeToSpendToday)}",
                        color = Color.White,
                        style = MaterialTheme.typography.displayMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = dailyPulse.message,
                        color = Color.White.copy(alpha = 0.9f),
                        style = MaterialTheme.typography.bodyMedium
                    )
                } else {
                    Text(
                        text = "$currencySymbol ****",
                        color = Color.White,
                        style = MaterialTheme.typography.displayMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // Visual Gauge
            if (!isPrivacyMode) {
                PulseGauge(
                    progress = dailyPulse.progressPercentage,
                    status = dailyPulse.pulseStatus,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .size(100.dp)
                )
            }
        }
    }
}

@Composable
fun PulseGauge(
    progress: Float,
    status: PulseStatus,
    modifier: Modifier = Modifier
) {
    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        label = "pulse_gauge"
    )

    Canvas(modifier = modifier) {
        val strokeWidth = 12.dp.toPx()
        val diameter = size.minDimension
        val radius = (diameter - strokeWidth) / 2

        // Background arc
        drawArc(
            color = Color.White.copy(alpha = 0.3f),
            startAngle = 135f,
            sweepAngle = 270f,
            useCenter = false,
            topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
            size = Size(diameter - strokeWidth, diameter - strokeWidth),
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )

        // Progress arc
        drawArc(
            color = Color.White,
            startAngle = 135f,
            sweepAngle = 270f * animatedProgress,
            useCenter = false,
            topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
            size = Size(diameter - strokeWidth, diameter - strokeWidth),
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )
    }
}

/**
 * Subscription Detective Card - "We noticed..."
 */
@Composable
fun SubscriptionDetectionCardItem(
    subscription: SubscriptionDetectionCard,
    currencySymbol: String,
    onYesClick: () -> Unit,
    onNoClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Info,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    "We noticed a recurring payment",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "${subscription.frequency.lowercase().capitalize()} payment of $currencySymbol${subscription.averageAmount} to ${subscription.merchantName}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Next expected: ${subscription.nextExpectedDate}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onNoClick,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                ) {
                    Text("No, Ignore")
                }
                Button(
                    onClick = onYesClick,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Yes, Track it")
                }
            }
        }
    }
}

/**
 * Simplified Activity List Item
 */
@Composable
fun ActivityListItem(
    activity: Activity,
    currencySymbol: String,
    isPrivacyMode: Boolean,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Category Icon/Emoji
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(
                    when (activity.type) {
                        ActivityType.EXPENSE -> Color(0xFFFFEBEE)
                        ActivityType.INCOME -> Color(0xFFE8F5E9)
                        ActivityType.TRANSFER -> Color(0xFFE3F2FD)
                    }
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = activity.description.take(1).uppercase(),
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = activity.description,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                maxLines = 1
            )
            Text(
                text = activity.activityDate.toString(),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Text(
            text = if (isPrivacyMode) {
                "$currencySymbol ****"
            } else {
                "${if (activity.type == ActivityType.EXPENSE) "-" else "+"}$currencySymbol${activity.amount}"
            },
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = when (activity.type) {
                ActivityType.EXPENSE -> Color(0xFFEF5350)
                ActivityType.INCOME -> Color(0xFF66BB6A)
                ActivityType.TRANSFER -> MaterialTheme.colorScheme.primary
            }
        )
    }
}
