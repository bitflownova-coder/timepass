package com.bitflow.finance.ui.screens.dev_tools

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.TimeEntryEntity
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TimeTrackerScreen(
    viewModel: DevToolsViewModel = hiltViewModel(),
    onBackClick: () -> Unit
) {
    val allEntries by viewModel.allTimeEntries.collectAsState()
    val activeTimer by viewModel.activeTimer.collectAsState()
    val todayEntries by viewModel.todayEntries.collectAsState()
    val weekEntries by viewModel.weekEntries.collectAsState()
    val monthEntries by viewModel.monthEntries.collectAsState()
    val projectNames by viewModel.projectNames.collectAsState()
    
    var selectedTab by remember { mutableStateOf(0) }
    var showStartDialog by remember { mutableStateOf(false) }
    var showManualEntryDialog by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Time Tracker", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { showManualEntryDialog = true }) {
                        Icon(Icons.Default.Add, "Add Manual Entry")
                    }
                }
            )
        },
        floatingActionButton = {
            if (activeTimer == null) {
                ExtendedFloatingActionButton(
                    onClick = { showStartDialog = true },
                    icon = { Icon(Icons.Default.PlayArrow, "Start") },
                    text = { Text("Start Timer") },
                    containerColor = Color(0xFF10B981),
                    contentColor = Color.White
                )
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Active Timer Card
            activeTimer?.let { timer ->
                ActiveTimerCard(
                    timer = timer,
                    onStop = { viewModel.stopTimer(timer) }
                )
            }
            
            // Stats Summary
            StatsSummaryRow(
                todayMinutes = todayEntries.filter { it.endTime != null }.sumOf { it.durationMinutes },
                weekMinutes = weekEntries.filter { it.endTime != null }.sumOf { it.durationMinutes },
                monthMinutes = monthEntries.filter { it.endTime != null }.sumOf { it.durationMinutes }
            )
            
            // Tabs
            TabRow(selectedTabIndex = selectedTab) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("Today") }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("This Week") }
                )
                Tab(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    text = { Text("All") }
                )
            }
            
            // Entry List
            val displayEntries = when (selectedTab) {
                0 -> todayEntries
                1 -> weekEntries
                else -> allEntries
            }
            
            if (displayEntries.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            Icons.Default.Timer,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.outline
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            "No time entries yet",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.outline
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "Start tracking your time!",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(displayEntries.filter { it.endTime != null }) { entry ->
                        TimeEntryCard(
                            entry = entry,
                            onDelete = { viewModel.deleteTimeEntry(entry) }
                        )
                    }
                }
            }
        }
    }
    
    // Start Timer Dialog
    if (showStartDialog) {
        StartTimerDialog(
            projectNames = projectNames,
            onDismiss = { showStartDialog = false },
            onStart = { project, task, rate, tags ->
                viewModel.startTimer(project, task, rate, tags = tags)
                showStartDialog = false
            }
        )
    }
    
    // Manual Entry Dialog
    if (showManualEntryDialog) {
        ManualEntryDialog(
            projectNames = projectNames,
            onDismiss = { showManualEntryDialog = false },
            onSave = { project, task, start, end, rate, tags, notes ->
                viewModel.addManualEntry(project, task, start, end, rate, tags = tags, notes = notes)
                showManualEntryDialog = false
            }
        )
    }
}

@Composable
private fun ActiveTimerCard(
    timer: TimeEntryEntity,
    onStop: () -> Unit
) {
    var elapsedSeconds by remember { mutableStateOf(0L) }
    
    LaunchedEffect(timer.startTime) {
        while (true) {
            elapsedSeconds = (System.currentTimeMillis() - timer.startTime) / 1000
            delay(1000)
        }
    }
    
    val hours = elapsedSeconds / 3600
    val minutes = (elapsedSeconds % 3600) / 60
    val seconds = elapsedSeconds % 60
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF10B981).copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = timer.projectName,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF10B981)
                )
                if (timer.taskDescription.isNotEmpty()) {
                    Text(
                        text = timer.taskDescription,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = String.format("%02d:%02d:%02d", hours, minutes, seconds),
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF10B981)
                )
            }
            
            IconButton(
                onClick = onStop,
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(Color(0xFFEF4444))
            ) {
                Icon(
                    Icons.Default.Stop,
                    contentDescription = "Stop",
                    tint = Color.White,
                    modifier = Modifier.size(32.dp)
                )
            }
        }
    }
}

@Composable
private fun StatsSummaryRow(
    todayMinutes: Int,
    weekMinutes: Int,
    monthMinutes: Int
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        StatCard(
            modifier = Modifier.weight(1f),
            label = "Today",
            minutes = todayMinutes,
            color = Color(0xFF3B82F6)
        )
        StatCard(
            modifier = Modifier.weight(1f),
            label = "Week",
            minutes = weekMinutes,
            color = Color(0xFF8B5CF6)
        )
        StatCard(
            modifier = Modifier.weight(1f),
            label = "Month",
            minutes = monthMinutes,
            color = Color(0xFFF59E0B)
        )
    }
}

@Composable
private fun StatCard(
    modifier: Modifier = Modifier,
    label: String,
    minutes: Int,
    color: Color
) {
    val hours = minutes / 60
    val mins = minutes % 60
    
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = color
            )
            Text(
                text = "${hours}h ${mins}m",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = color
            )
        }
    }
}

@Composable
private fun TimeEntryCard(
    entry: TimeEntryEntity,
    onDelete: () -> Unit
) {
    val dateFormat = remember { SimpleDateFormat("MMM dd, hh:mm a", Locale.getDefault()) }
    val hours = entry.durationMinutes / 60
    val minutes = entry.durationMinutes % 60
    
    var showDeleteConfirm by remember { mutableStateOf(false) }
    
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = entry.projectName,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    if (entry.isManualEntry) {
                        Surface(
                            color = MaterialTheme.colorScheme.tertiaryContainer,
                            shape = RoundedCornerShape(4.dp)
                        ) {
                            Text(
                                text = "Manual",
                                style = MaterialTheme.typography.labelSmall,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }
                }
                if (entry.taskDescription.isNotEmpty()) {
                    Text(
                        text = entry.taskDescription,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = dateFormat.format(Date(entry.startTime)),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline
                )
                if (entry.tags.isNotEmpty()) {
                    Row(
                        modifier = Modifier.padding(top = 4.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        entry.tags.split(",").take(3).forEach { tag ->
                            Surface(
                                color = MaterialTheme.colorScheme.secondaryContainer,
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    text = tag.trim(),
                                    style = MaterialTheme.typography.labelSmall,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
                }
            }
            
            Column(
                horizontalAlignment = Alignment.End
            ) {
                Text(
                    text = "${hours}h ${minutes}m",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF10B981)
                )
                if (entry.hourlyRate > 0) {
                    val earnings = entry.durationMinutes * entry.hourlyRate / 60
                    Text(
                        text = "₹${String.format("%.0f", earnings)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.outline
                    )
                }
                IconButton(onClick = { showDeleteConfirm = true }) {
                    Icon(
                        Icons.Default.Delete,
                        contentDescription = "Delete",
                        tint = MaterialTheme.colorScheme.error,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
    
    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("Delete Entry?") },
            text = { Text("This action cannot be undone.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        onDelete()
                        showDeleteConfirm = false
                    }
                ) {
                    Text("Delete", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun StartTimerDialog(
    projectNames: List<String>,
    onDismiss: () -> Unit,
    onStart: (project: String, task: String, rate: Double, tags: String) -> Unit
) {
    var projectName by remember { mutableStateOf("") }
    var taskDescription by remember { mutableStateOf("") }
    var hourlyRate by remember { mutableStateOf("") }
    var tags by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Start Timer", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    OutlinedTextField(
                        value = projectName,
                        onValueChange = { projectName = it },
                        label = { Text("Project Name *") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor(),
                        trailingIcon = {
                            ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                        },
                        singleLine = true
                    )
                    if (projectNames.isNotEmpty()) {
                        ExposedDropdownMenu(
                            expanded = expanded,
                            onDismissRequest = { expanded = false }
                        ) {
                            projectNames.forEach { name ->
                                DropdownMenuItem(
                                    text = { Text(name) },
                                    onClick = {
                                        projectName = name
                                        expanded = false
                                    }
                                )
                            }
                        }
                    }
                }
                
                OutlinedTextField(
                    value = taskDescription,
                    onValueChange = { taskDescription = it },
                    label = { Text("Task Description") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                OutlinedTextField(
                    value = hourlyRate,
                    onValueChange = { hourlyRate = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("Hourly Rate (₹)") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true
                )
                
                OutlinedTextField(
                    value = tags,
                    onValueChange = { tags = it },
                    label = { Text("Tags (comma separated)") },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("coding, meeting, research") },
                    singleLine = true
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (projectName.isNotBlank()) {
                        onStart(
                            projectName.trim(),
                            taskDescription.trim(),
                            hourlyRate.toDoubleOrNull() ?: 0.0,
                            tags.trim()
                        )
                    }
                },
                enabled = projectName.isNotBlank()
            ) {
                Icon(Icons.Default.PlayArrow, null, modifier = Modifier.size(20.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Start")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ManualEntryDialog(
    projectNames: List<String>,
    onDismiss: () -> Unit,
    onSave: (project: String, task: String, start: Long, end: Long, rate: Double, tags: String, notes: String) -> Unit
) {
    var projectName by remember { mutableStateOf("") }
    var taskDescription by remember { mutableStateOf("") }
    var hourlyRate by remember { mutableStateOf("") }
    var tags by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }
    var durationHours by remember { mutableStateOf("") }
    var durationMinutes by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }
    
    val now = System.currentTimeMillis()
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Manual Entry", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    OutlinedTextField(
                        value = projectName,
                        onValueChange = { projectName = it },
                        label = { Text("Project Name *") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor(),
                        trailingIcon = {
                            if (projectNames.isNotEmpty()) {
                                ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                            }
                        },
                        singleLine = true
                    )
                    if (projectNames.isNotEmpty()) {
                        ExposedDropdownMenu(
                            expanded = expanded,
                            onDismissRequest = { expanded = false }
                        ) {
                            projectNames.forEach { name ->
                                DropdownMenuItem(
                                    text = { Text(name) },
                                    onClick = {
                                        projectName = name
                                        expanded = false
                                    }
                                )
                            }
                        }
                    }
                }
                
                OutlinedTextField(
                    value = taskDescription,
                    onValueChange = { taskDescription = it },
                    label = { Text("Task Description") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                Text("Duration *", style = MaterialTheme.typography.labelMedium)
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedTextField(
                        value = durationHours,
                        onValueChange = { durationHours = it.filter { c -> c.isDigit() } },
                        label = { Text("Hours") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = durationMinutes,
                        onValueChange = { 
                            val filtered = it.filter { c -> c.isDigit() }
                            if (filtered.isEmpty() || filtered.toInt() < 60) {
                                durationMinutes = filtered
                            }
                        },
                        label = { Text("Minutes") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                }
                
                OutlinedTextField(
                    value = hourlyRate,
                    onValueChange = { hourlyRate = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("Hourly Rate (₹)") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true
                )
                
                OutlinedTextField(
                    value = tags,
                    onValueChange = { tags = it },
                    label = { Text("Tags") },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("coding, meeting") },
                    singleLine = true
                )
                
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Notes") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val hours = durationHours.toIntOrNull() ?: 0
                    val mins = durationMinutes.toIntOrNull() ?: 0
                    val totalMins = hours * 60 + mins
                    if (projectName.isNotBlank() && totalMins > 0) {
                        val endTime = now
                        val startTime = endTime - (totalMins * 60 * 1000L)
                        onSave(
                            projectName.trim(),
                            taskDescription.trim(),
                            startTime,
                            endTime,
                            hourlyRate.toDoubleOrNull() ?: 0.0,
                            tags.trim(),
                            notes.trim()
                        )
                    }
                },
                enabled = projectName.isNotBlank() && 
                    ((durationHours.toIntOrNull() ?: 0) > 0 || (durationMinutes.toIntOrNull() ?: 0) > 0)
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
