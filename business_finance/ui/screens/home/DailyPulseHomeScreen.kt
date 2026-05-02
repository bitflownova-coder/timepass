package com.bitflow.finance.ui.screens.home

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.RecurringPattern
import com.bitflow.finance.ui.components.FilterChipsRow
import com.bitflow.finance.ui.components.TimeFilter
import com.bitflow.finance.ui.components.getDateRangeForFilter
import com.bitflow.finance.domain.model.AppMode
import com.bitflow.finance.ui.components.ModeToggle
import java.time.format.DateTimeFormatter

/**
 * Phase 3: Daily Pulse Home Screen
 * "Don't Make Me Think" - Show peace of mind, not data overload
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DailyPulseHomeScreen(
    viewModel: DailyPulseViewModel = hiltViewModel(),
    onAddActivityClick: () -> Unit,
    onActivityClick: (Long) -> Unit,
    onImportClick: () -> Unit,
    onAnalyticsClick: () -> Unit,
    onToolsClick: () -> Unit,
    currentMode: AppMode,
    onModeChange: (AppMode) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val streak by viewModel.streak.collectAsState()
    var selectedFilter by remember { mutableStateOf(TimeFilter.THIS_MONTH) }
    
    // Apply filter to activities and ensure proper sorting
    val filteredActivities = remember(uiState.recentActivities, selectedFilter) {
        val activities = uiState.recentActivities
        
        val filtered = if (selectedFilter == TimeFilter.ALL) {
            activities
        } else {
            val dateRange = getDateRangeForFilter(selectedFilter)
            activities.filter { activity ->
                activity.activityDate >= dateRange.first && activity.activityDate <= dateRange.second
            }
        }
        
        // Sort by date descending (newest first), then by ID for consistent ordering
        val sorted = filtered.sortedWith(
            compareByDescending<Activity> { it.activityDate }
                .thenByDescending { it.id }
        )
        
        // Apply LAST_10 limit after sorting
        if (selectedFilter == TimeFilter.LAST_10) {
            sorted.take(10)
        } else {
            sorted
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = getGreeting(),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = if (uiState.userName.isNotBlank()) uiState.userName else "Your Money",
                                style = MaterialTheme.typography.titleMedium
                            )
                        }
                        
                        // Streak Badge
                        if (streak > 0) {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = Color(0xFFFF5722).copy(alpha = 0.1f),
                                modifier = Modifier.padding(end = 8.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "\uD83D\uDD25", // Fire emoji
                                        fontSize = 14.sp
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(
                                        text = "$streak",
                                        style = MaterialTheme.typography.labelLarge,
                                        color = Color(0xFFFF5722),
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    }
                },
                actions = {
                    IconButton(onClick = onToolsClick) {
                        Icon(
                            imageVector = Icons.Default.Build,
                            contentDescription = "Tools"
                        )
                    }
                    IconButton(onClick = onImportClick) {
                        Icon(
                            imageVector = Icons.Default.Upload,
                            contentDescription = "Import Statement"
                        )
                    }
                    IconButton(onClick = { viewModel.togglePrivacyMode() }) {
                        Icon(
                            imageVector = if (uiState.isPrivacyMode) 
                                Icons.Default.VisibilityOff 
                            else 
                                Icons.Default.Visibility,
                            contentDescription = "Toggle Privacy"
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
        BoxWithConstraints {
            val screenWidth = maxWidth
            val horizontalPadding = when {
                screenWidth < 360.dp -> 12.dp
                screenWidth < 600.dp -> 16.dp
                else -> 24.dp
            }
            
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentPadding = PaddingValues(horizontal = horizontalPadding, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Mode Toggle
                item {
                    ModeToggle(
                        currentMode = currentMode,
                        onModeChange = onModeChange,
                        modifier = Modifier.fillMaxWidth().wrapContentWidth(Alignment.CenterHorizontally)
                    )
                }

                // Phase 3.1: Daily Pulse Card (Top Priority)
                item {
                    DailyPulseCard(
                        currentBalance = uiState.currentBalance,
                        monthIncome = uiState.monthIncome,
                        monthExpenses = uiState.monthExpenses,
                        spentToday = uiState.todayExpenses,
                        isPrivacyMode = uiState.isPrivacyMode,
                        pulseStatus = uiState.pulseStatus
                    )
                }
            
            // Smart Nudge
            if (uiState.smartNudge != null) {
                item {
                    SmartNudgeCard(nudge = uiState.smartNudge!!)
                }
            }

            // Phase 3.2: Subscription Alerts
            if (uiState.potentialSubscriptions.isNotEmpty()) {
                item {
                    Text(
                        "Detected Patterns",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                
                items(uiState.potentialSubscriptions) { subscription ->
                    SubscriptionAlertCard(
                        pattern = subscription,
                        onConfirm = { viewModel.confirmSubscription(subscription) },
                        onDismiss = { viewModel.dismissSubscription(subscription) }
                    )
                }
            }

            // Phase 3.3: Recent Transactions with Filters
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
                    Text(
                        "${filteredActivities.size} transactions",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Filter Chips
            item {
                FilterChipsRow(
                    selectedFilter = selectedFilter,
                    onFilterSelected = { selectedFilter = it }
                )
            }

            if (filteredActivities.isEmpty()) {
                item {
                    EmptyStateMessage(
                        message = if (uiState.recentActivities.isEmpty()) 
                            "No activities yet" 
                        else 
                            "No activities in this period"
                    )
                }
            } else {
                items(filteredActivities) { activity ->
                    SwipeableActivityItem(
                        activity = activity,
                        isPrivacyMode = uiState.isPrivacyMode,
                        onClick = { onActivityClick(activity.id) },
                        onDelete = { viewModel.deleteActivity(activity.id) },
                        onEdit = { /* Navigate to edit */ }
                    )
                }
            }
            }
        }
    }
}

/**
 * Daily Pulse Card: Shows current balance and monthly summary
 */
@Composable
fun DailyPulseCard(
    currentBalance: Double,
    monthIncome: Double,
    monthExpenses: Double,
    spentToday: Double,
    isPrivacyMode: Boolean,
    pulseStatus: PulseStatus
) {
    val monthlySavings = monthIncome - monthExpenses
    val animatedProgress by animateFloatAsState(
        targetValue = if (monthIncome > 0) (monthExpenses / monthIncome).toFloat().coerceIn(0f, 1f) else 0f,
        animationSpec = tween(1000),
        label = "pulse_progress"
    )

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = when (pulseStatus) {
                PulseStatus.GOOD -> Color(0xFF4CAF50).copy(alpha = 0.1f)
                PulseStatus.CAUTION -> Color(0xFFFFC107).copy(alpha = 0.1f)
                PulseStatus.SLOW_DOWN -> Color(0xFFF44336).copy(alpha = 0.1f)
            }
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Status Icon
            Icon(
                imageVector = when (pulseStatus) {
                    PulseStatus.GOOD -> Icons.Default.CheckCircle
                    PulseStatus.CAUTION -> Icons.Default.Warning
                    PulseStatus.SLOW_DOWN -> Icons.Default.Error
                },
                contentDescription = null,
                tint = when (pulseStatus) {
                    PulseStatus.GOOD -> Color(0xFF4CAF50)
                    PulseStatus.CAUTION -> Color(0xFFFFC107)
                    PulseStatus.SLOW_DOWN -> Color(0xFFF44336)
                },
                modifier = Modifier.size(48.dp)
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Main Message
            Text(
                text = if (isPrivacyMode) "•••" else "Current Balance",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Balance Amount
            Text(
                text = if (isPrivacyMode) "₹ •••" else "₹${String.format("%,.0f", currentBalance)}",
                style = MaterialTheme.typography.displayMedium,
                fontWeight = FontWeight.Bold,
                color = when {
                    currentBalance > 0 -> Color(0xFF4CAF50)
                    currentBalance < 0 -> Color(0xFFF44336)
                    else -> MaterialTheme.colorScheme.onSurface
                }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Monthly Progress
            if (monthIncome > 0) {
                LinearProgressIndicator(
                    progress = animatedProgress,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                    color = when (pulseStatus) {
                        PulseStatus.GOOD -> Color(0xFF4CAF50)
                        PulseStatus.CAUTION -> Color(0xFFFFC107)
                        PulseStatus.SLOW_DOWN -> Color(0xFFF44336)
                    },
                    trackColor = MaterialTheme.colorScheme.surfaceVariant
                )

                Spacer(modifier = Modifier.height(12.dp))
            }

            // Monthly Summary
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "This Month",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = if (isPrivacyMode) "•••" else when {
                            monthlySavings > 0 -> "+₹${String.format("%,.0f", monthlySavings)}"
                            monthlySavings < 0 -> "-₹${String.format("%,.0f", -monthlySavings)}"
                            else -> "₹0"
                        },
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = when {
                            monthlySavings > 0 -> Color(0xFF4CAF50)
                            monthlySavings < 0 -> Color(0xFFF44336)
                            else -> MaterialTheme.colorScheme.onSurface
                        }
                    )
                }
                
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "Today",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = if (isPrivacyMode) "•••" else "₹${String.format("%,.0f", spentToday)}",
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = if (spentToday > 0) Color(0xFFF44336) else MaterialTheme.colorScheme.onSurface
                    )
                }
            }
        }
    }
}

/**
 * Subscription Alert Card: "Is this a subscription?"
 */
@Composable
fun SubscriptionAlertCard(
    pattern: RecurringPattern,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF2196F3).copy(alpha = 0.1f)
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
                    imageVector = Icons.Default.Refresh,
                    contentDescription = null,
                    tint = Color(0xFF2196F3),
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Subscription Detected",
                    style = MaterialTheme.typography.labelMedium,
                    color = Color(0xFF2196F3),
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "We noticed a ${pattern.frequency} payment of ₹${String.format("%.0f", pattern.averageAmount)} to ${pattern.merchantName}",
                style = MaterialTheme.typography.bodyMedium
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onDismiss,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Not a subscription")
                }
                Button(
                    onClick = onConfirm,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Track it")
                }
            }
        }
    }
}

/**
 * Swipeable Activity Item
 * Left swipe: Delete, Right swipe: Edit
 */
@Composable
fun SwipeableActivityItem(
    activity: Activity,
    isPrivacyMode: Boolean,
    onClick: () -> Unit,
    onDelete: () -> Unit,
    onEdit: () -> Unit
) {
    var offsetX by remember { mutableStateOf(0f) }
    val maxSwipe = 200f

    Box(
        modifier = Modifier.fillMaxWidth()
    ) {
        // Background actions (visible when swiping)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(72.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // Left: Delete
            if (offsetX > 50f) {
                Box(
                    modifier = Modifier
                        .width(offsetX.dp)
                        .fillMaxHeight()
                        .background(Color(0xFFF44336)),
                    contentAlignment = Alignment.CenterStart
                ) {
                    Icon(
                        Icons.Default.Delete,
                        contentDescription = "Delete",
                        tint = Color.White,
                        modifier = Modifier.padding(start = 16.dp)
                    )
                }
            }
        }

        // Foreground: Activity Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .offset(x = offsetX.dp)
                .draggable(
                    orientation = Orientation.Horizontal,
                    state = rememberDraggableState { delta ->
                        offsetX = (offsetX + delta).coerceIn(-maxSwipe, maxSwipe)
                    },
                    onDragStopped = {
                        if (offsetX > 100f) {
                            onDelete()
                        }
                        offsetX = 0f
                    }
                )
                .clickable(onClick = onClick),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Left: Category Icon + Details
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                            .background(
                                when (activity.type) {
                                    ActivityType.EXPENSE -> Color(0xFFF44336).copy(alpha = 0.1f)
                                    ActivityType.INCOME -> Color(0xFF4CAF50).copy(alpha = 0.1f)
                                    ActivityType.TRANSFER -> Color(0xFF2196F3).copy(alpha = 0.1f)
                                }
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = when (activity.type) {
                                ActivityType.EXPENSE -> Icons.Default.ArrowDownward
                                ActivityType.INCOME -> Icons.Default.ArrowUpward
                                ActivityType.TRANSFER -> Icons.Default.SwapHoriz
                            },
                            contentDescription = null,
                            tint = when (activity.type) {
                                ActivityType.EXPENSE -> Color(0xFFF44336)
                                ActivityType.INCOME -> Color(0xFF4CAF50)
                                ActivityType.TRANSFER -> Color(0xFF2196F3)
                            },
                            modifier = Modifier.size(20.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(12.dp))

                    Column {
                        Text(
                            text = activity.description.take(30),
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = FontWeight.Medium
                        )
                        Text(
                            text = activity.activityDate.format(DateTimeFormatter.ofPattern("MMM dd, yyyy")),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                // Right: Amount
                Text(
                    text = if (isPrivacyMode) "•••" else "${if (activity.type == ActivityType.EXPENSE) "-" else "+"}₹${String.format("%.0f", activity.amount)}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = when (activity.type) {
                        ActivityType.EXPENSE -> Color(0xFFF44336)
                        ActivityType.INCOME -> Color(0xFF4CAF50)
                        ActivityType.TRANSFER -> MaterialTheme.colorScheme.primary
                    }
                )
            }
        }
    }
}

@Composable
fun EmptyStateMessage(message: String = "No activities yet") {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = Icons.Default.Receipt,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = message,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = if (message == "No activities yet") 
                "Tap + to add your first expense or income" 
            else 
                "Try selecting a different time period",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}

private fun getGreeting(): String {
    val hour = java.time.LocalTime.now().hour
    return when {
        hour < 12 -> "Good Morning"
        hour < 17 -> "Good Afternoon"
        else -> "Good Evening"
    }
}

enum class PulseStatus {
    GOOD,
    CAUTION,
    SLOW_DOWN
}

@Composable
fun SmartNudgeCard(nudge: com.bitflow.finance.domain.usecase.SmartNudge) {
    val (bgColor, textColor) = when (nudge.type) {
        com.bitflow.finance.domain.usecase.NudgeType.WARNING -> MaterialTheme.colorScheme.errorContainer to MaterialTheme.colorScheme.onErrorContainer
        com.bitflow.finance.domain.usecase.NudgeType.CELEBRATION -> Color(0xFFECFDF5) to Color(0xFF047857)
        com.bitflow.finance.domain.usecase.NudgeType.TIP -> MaterialTheme.colorScheme.tertiaryContainer to MaterialTheme.colorScheme.onTertiaryContainer
        else -> MaterialTheme.colorScheme.surfaceVariant to MaterialTheme.colorScheme.onSurfaceVariant
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = bgColor)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Text(
                text = when(nudge.type) {
                    com.bitflow.finance.domain.usecase.NudgeType.WARNING -> "⚠️"
                    com.bitflow.finance.domain.usecase.NudgeType.CELEBRATION -> "🎉"
                    com.bitflow.finance.domain.usecase.NudgeType.TIP -> "💡"
                    else -> "ℹ️"
                },
                style = MaterialTheme.typography.titleLarge
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = nudge.message,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = textColor
                )
                if (nudge.actionLabel != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = nudge.actionLabel,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = textColor,
                        modifier = Modifier.clickable { /* Handle action */ }
                    )
                }
            }
        }
    }
}
