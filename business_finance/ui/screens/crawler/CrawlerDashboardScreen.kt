package com.bitflow.finance.ui.screens.crawler

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Language
import androidx.compose.foundation.BorderStroke
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import java.text.SimpleDateFormat
import java.util.*

// Filter options
enum class CrawlFilter(val label: String) {
    ALL("All"),
    RUNNING("Running"),
    COMPLETED("Completed"),
    FAILED("Failed")
}

// Sort options
enum class CrawlSort(val label: String) {
    RECENT("Recent First"),
    OLDEST("Oldest First"),
    MOST_PAGES("Most Pages")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CrawlerDashboardScreen(
    viewModel: CrawlerViewModel,
    navController: NavController
) {
    val sessions by viewModel.allSessions.collectAsState()
    var showNewCrawlDialog by remember { mutableStateOf(false) }
    
    // Search and filter state
    var searchQuery by remember { mutableStateOf("") }
    var selectedFilter by remember { mutableStateOf(CrawlFilter.ALL) }
    var selectedSort by remember { mutableStateOf(CrawlSort.RECENT) }
    var showSortMenu by remember { mutableStateOf(false) }
    var visibleCount by remember { mutableIntStateOf(10) }
    
    // Calculate stats
    val runningCount = sessions.count { it.status == "RUNNING" }
    val completedCount = sessions.count { it.status == "COMPLETED" }
    val failedCount = sessions.count { it.status == "FAILED" }
    
    // Filter and sort sessions
    val filteredSessions = remember(sessions, searchQuery, selectedFilter, selectedSort, visibleCount) {
        sessions
            .filter { session ->
                // Apply search filter
                val matchesSearch = searchQuery.isBlank() || 
                    session.startUrl.contains(searchQuery, ignoreCase = true)
                
                // Apply status filter
                val matchesFilter = when (selectedFilter) {
                    CrawlFilter.ALL -> true
                    CrawlFilter.RUNNING -> session.status == "RUNNING"
                    CrawlFilter.COMPLETED -> session.status == "COMPLETED"
                    CrawlFilter.FAILED -> session.status == "FAILED"
                }
                
                matchesSearch && matchesFilter
            }
            .sortedWith(
                when (selectedSort) {
                    CrawlSort.RECENT -> compareByDescending { it.startTime }
                    CrawlSort.OLDEST -> compareBy { it.startTime }
                    CrawlSort.MOST_PAGES -> compareByDescending { it.pagesCrawled }
                }
            )
    }
    
    val displayedSessions = filteredSessions.take(visibleCount)
    val hasMore = filteredSessions.size > visibleCount

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header with title and new crawl button
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            "Website Crawler",
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Black,
                            color = MaterialTheme.colorScheme.onBackground
                        )
                        Text(
                            "Analyze & scan websites",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    FilledTonalButton(
                        onClick = { showNewCrawlDialog = true },
                        colors = ButtonDefaults.filledTonalButtonColors(
                            containerColor = Color(0xFF6366F1),
                            contentColor = Color.White
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Rounded.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("New Crawl", fontWeight = FontWeight.Bold)
                    }
                }
            }
            
            // Stats Cards Row
            if (sessions.isNotEmpty()) {
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        StatCard(
                            count = sessions.size,
                            label = "Total",
                            color = Color(0xFF6366F1),
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            count = runningCount,
                            label = "Running",
                            color = Color(0xFF10B981),
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            count = completedCount,
                            label = "Done",
                            color = Color(0xFF3B82F6),
                            modifier = Modifier.weight(1f)
                        )
                        if (failedCount > 0) {
                            StatCard(
                                count = failedCount,
                                label = "Failed",
                                color = Color(0xFFEF4444),
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
            
            // Search Bar
            item {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { 
                        searchQuery = it
                        visibleCount = 10 // Reset pagination on search
                    },
                    placeholder = { Text("Search by URL...") },
                    leadingIcon = { 
                        Icon(
                            Icons.Default.Search, 
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        ) 
                    },
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(Icons.Default.Close, contentDescription = "Clear")
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f)
                    )
                )
            }
            
            // Filter Chips and Sort
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.weight(1f)
                    ) {
                        items(CrawlFilter.entries) { filter ->
                            FilterChip(
                                selected = selectedFilter == filter,
                                onClick = { 
                                    selectedFilter = filter
                                    visibleCount = 10
                                },
                                label = { 
                                    Text(
                                        filter.label,
                                        fontWeight = if (selectedFilter == filter) FontWeight.Bold else FontWeight.Normal
                                    )
                                },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = Color(0xFF6366F1).copy(alpha = 0.15f),
                                    selectedLabelColor = Color(0xFF6366F1)
                                )
                            )
                        }
                    }
                    
                    // Sort Button
                    Box {
                        IconButton(onClick = { showSortMenu = true }) {
                            Icon(
                                Icons.Default.Sort,
                                contentDescription = "Sort",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        DropdownMenu(
                            expanded = showSortMenu,
                            onDismissRequest = { showSortMenu = false }
                        ) {
                            CrawlSort.entries.forEach { sort ->
                                DropdownMenuItem(
                                    text = { 
                                        Text(
                                            sort.label,
                                            fontWeight = if (selectedSort == sort) FontWeight.Bold else FontWeight.Normal
                                        )
                                    },
                                    onClick = {
                                        selectedSort = sort
                                        showSortMenu = false
                                    },
                                    leadingIcon = {
                                        if (selectedSort == sort) {
                                            Icon(
                                                Icons.Default.Check,
                                                contentDescription = null,
                                                tint = Color(0xFF6366F1)
                                            )
                                        }
                                    }
                                )
                            }
                        }
                    }
                }
            }
            
            // Results count
            if (filteredSessions.isNotEmpty()) {
                item {
                    Text(
                        "${filteredSessions.size} result${if (filteredSessions.size != 1) "s" else ""}" +
                            if (hasMore) " (showing ${displayedSessions.size})" else "",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            if (sessions.isEmpty()) {
                item {
                    EmptyDashboardContent(onNewCrawl = { showNewCrawlDialog = true })
                }
            } else if (filteredSessions.isEmpty()) {
                item {
                    NoResultsContent(searchQuery, selectedFilter)
                }
            } else {
                // Session Cards
                items(
                    items = displayedSessions,
                    key = { it.id }
                ) { session ->
                    CrawlSessionCard(session) {
                        navController.navigate("helper_crawl_detail/${session.id}")
                    }
                }
                
                // Load More button
                if (hasMore) {
                    item {
                        OutlinedButton(
                            onClick = { visibleCount += 10 },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text("Load More (${filteredSessions.size - visibleCount} remaining)")
                        }
                    }
                }
                
                item {
                    Spacer(Modifier.height(16.dp))
                }
            }
        }
        
        if (showNewCrawlDialog) {
            NewCrawlDialog(
                onDismiss = { showNewCrawlDialog = false },
                onStart = { url, depth, isMobile, categories ->
                    viewModel.startCrawl(url, depth, isMobile, categories)
                    showNewCrawlDialog = false
                }
            )
        }
    }
}

@Composable
fun StatCard(count: Int, label: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                "$count",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Black,
                color = color
            )
            Text(
                label,
                style = MaterialTheme.typography.labelSmall,
                color = color.copy(alpha = 0.8f)
            )
        }
    }
}

@Composable
fun NoResultsContent(searchQuery: String, filter: CrawlFilter) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                Icons.Outlined.SearchOff,
                contentDescription = null,
                modifier = Modifier.size(48.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            Text(
                "No results found",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Text(
                if (searchQuery.isNotEmpty()) "Try a different search term"
                else "No ${filter.label.lowercase()} crawls available",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun EmptyDashboardContent(onNewCrawl: () -> Unit = {}) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        ),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .background(
                        Color(0xFF6366F1).copy(alpha = 0.1f),
                        CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Rounded.Language, 
                    contentDescription = null, 
                    modifier = Modifier.size(40.dp),
                    tint = Color(0xFF6366F1)
                )
            }
            Spacer(Modifier.height(16.dp))
            Text(
                "No Crawls Yet",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Start by crawling your first website",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(Modifier.height(20.dp))
            Button(
                onClick = onNewCrawl,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF6366F1)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Rounded.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Start First Crawl", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewCrawlDialog(onDismiss: () -> Unit, onStart: (String, Int, Boolean, Set<String>) -> Unit) {
    var url by remember { mutableStateOf("https://") }
    var depth by remember { mutableFloatStateOf(1f) }
    var isMobile by remember { mutableStateOf(false) }
    var isProcessing by remember { mutableStateOf(false) }
    
    // Scan mode: 0 = Quick, 1 = Full, 2 = Custom
    var scanMode by remember { mutableIntStateOf(1) } // Default to Full
    var showCustomOptions by remember { mutableStateOf(false) }
    
    // Scan categories state
    val categories = remember { mutableStateMapOf(
        "dns_recon" to true,
        "ssl_analysis" to true,
        "subdomain_enum" to true,
        "api_discovery" to true,
        "param_fuzzing" to true,
        "auth_testing" to true,
        "cloud_scanner" to true,
        "security_headers" to true
    ) }
    
    // Quick scan only runs essential scans
    val quickScanCategories = setOf("ssl_analysis", "security_headers")
    
    // Category display info with icons
    val categoryInfo = listOf(
        Triple("security_headers", "🛡️ Headers", "CSP, HSTS, X-Frame"),
        Triple("ssl_analysis", "🔒 SSL/TLS", "Certificates, protocols"),
        Triple("dns_recon", "🌐 DNS", "Records, WHOIS, email"),
        Triple("subdomain_enum", "🔍 Subdomains", "Enumerate subdomains"),
        Triple("api_discovery", "📡 APIs", "Swagger, GraphQL"),
        Triple("param_fuzzing", "⚡ Parameters", "Hidden params, XSS"),
        Triple("auth_testing", "🔑 Auth", "Login, rate limits"),
        Triple("cloud_scanner", "☁️ Cloud", "S3, Azure, GCP")
    )

    AlertDialog(
        onDismissRequest = { if (!isProcessing) onDismiss() },
        title = { 
            Column {
                Text("New Website Crawl", fontWeight = FontWeight.Bold)
                Text(
                    "Scan & analyze website",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        },
        text = {
            LazyColumn(
                modifier = Modifier.heightIn(max = 450.dp)
            ) {
                item {
                    OutlinedTextField(
                        value = url,
                        onValueChange = { url = it },
                        label = { Text("Target URL") },
                        placeholder = { Text("https://example.com") },
                        leadingIcon = { Icon(Icons.Default.Language, contentDescription = null) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 16.dp),
                        shape = RoundedCornerShape(12.dp),
                        singleLine = true,
                    )
                }
                
                // Scan Mode Selection - VISIBLE BY DEFAULT
                item {
                    Text(
                        "Scan Mode",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                }
                
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Quick Scan
                        ScanModeCard(
                            selected = scanMode == 0,
                            title = "Quick",
                            subtitle = "2 scans",
                            icon = "⚡",
                            color = Color(0xFF10B981),
                            modifier = Modifier.weight(1f),
                            onClick = { 
                                scanMode = 0
                                showCustomOptions = false
                                // Set only quick categories
                                categories.keys.forEach { 
                                    categories[it] = quickScanCategories.contains(it)
                                }
                            }
                        )
                        
                        // Full Scan
                        ScanModeCard(
                            selected = scanMode == 1,
                            title = "Full",
                            subtitle = "8 scans",
                            icon = "🔒",
                            color = Color(0xFF3B82F6),
                            modifier = Modifier.weight(1f),
                            onClick = { 
                                scanMode = 1
                                showCustomOptions = false
                                // Enable all
                                categories.keys.forEach { categories[it] = true }
                            }
                        )
                        
                        // Custom
                        ScanModeCard(
                            selected = scanMode == 2,
                            title = "Custom",
                            subtitle = "${categories.values.count { it }}",
                            icon = "⚙️",
                            color = Color(0xFF8B5CF6),
                            modifier = Modifier.weight(1f),
                            onClick = { 
                                scanMode = 2
                                showCustomOptions = true
                            }
                        )
                    }
                }
                
                // Custom options (shown when Custom mode selected)
                if (showCustomOptions || scanMode == 2) {
                    item {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            "Select Scans",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(Modifier.height(8.dp))
                    }
                    
                    // Grid of scan options
                    item {
                        Column(
                            verticalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            categoryInfo.chunked(2).forEach { row ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    row.forEach { (key, name, desc) ->
                                        ScanOptionChip(
                                            icon = name.split(" ")[0],
                                            name = name.split(" ").drop(1).joinToString(" "),
                                            selected = categories[key] ?: false,
                                            modifier = Modifier.weight(1f),
                                            onClick = { 
                                                categories[key] = !(categories[key] ?: false)
                                            }
                                        )
                                    }
                                    // Fill remaining space if odd number
                                    if (row.size == 1) {
                                        Spacer(Modifier.weight(1f))
                                    }
                                }
                            }
                        }
                    }
                }
                
                item {
                    Spacer(Modifier.height(16.dp))
                    Divider()
                    Spacer(Modifier.height(12.dp))
                }
                
                // Crawl depth
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Crawl Depth", style = MaterialTheme.typography.labelLarge)
                        Text(
                            "${depth.toInt()} pages deep",
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Slider(
                        value = depth,
                        onValueChange = { depth = it },
                        valueRange = 1f..5f,
                        steps = 3
                    )
                }

                // Mobile toggle
                item {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .clickable { isMobile = !isMobile }
                            .padding(vertical = 4.dp)
                    ) {
                        Checkbox(
                            checked = isMobile,
                            onCheckedChange = { isMobile = it }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Mobile User-Agent", style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = { 
                    isProcessing = true
                    val enabledCategories = categories.filter { it.value }.keys
                    onStart(url, depth.toInt(), isMobile, enabledCategories) 
                },
                shape = RoundedCornerShape(8.dp),
                enabled = !isProcessing && url.length > 8 && categories.values.any { it }
            ) {
                if (isProcessing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(Modifier.width(8.dp))
                }
                Text(if(isProcessing) "Starting..." else "Start Crawl")
            }
        },
        dismissButton = {
            TextButton(
                onClick = { onDismiss() },
                enabled = !isProcessing
            ) {
                Text("Cancel")
            }
        }
    )
}

@Composable
fun ScanModeCard(
    selected: Boolean,
    title: String,
    subtitle: String,
    icon: String,
    color: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) color.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        ),
        border = if (selected) androidx.compose.foundation.BorderStroke(2.dp, color) else null,
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(icon, fontSize = 24.sp)
            Spacer(Modifier.height(4.dp))
            Text(
                title,
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp,
                color = if (selected) color else MaterialTheme.colorScheme.onSurface
            )
            Text(
                subtitle,
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun ScanOptionChip(
    icon: String,
    name: String,
    selected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        modifier = modifier.clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) 
                MaterialTheme.colorScheme.primary.copy(alpha = 0.1f) 
            else 
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
        ),
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(icon, fontSize = 16.sp)
            Spacer(Modifier.width(6.dp))
            Text(
                name,
                fontSize = 12.sp,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Spacer(Modifier.weight(1f))
            if (selected) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    modifier = Modifier.size(14.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
fun CrawlSessionCard(session: CrawlSessionEntity, onClick: () -> Unit) {
    val statusColor = getStatusColor(session.status)
    val isRunning = session.status == "RUNNING"
    val isCompleted = session.status == "COMPLETED"
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (isRunning) 6.dp else 2.dp
        ),
        shape = RoundedCornerShape(16.dp),
        border = if (isRunning) androidx.compose.foundation.BorderStroke(
            2.dp, 
            Brush.horizontalGradient(listOf(statusColor, statusColor.copy(alpha = 0.5f)))
        ) else null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Status Indicator Circle
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(statusColor.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                if (isRunning) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        strokeWidth = 2.dp,
                        color = statusColor
                    )
                } else {
                    Icon(
                        if (isCompleted) Icons.Default.CheckCircle else Icons.Default.Warning,
                        contentDescription = null,
                        tint = statusColor,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }
            
            Spacer(Modifier.width(14.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = session.startUrl
                        .removePrefix("https://www.")
                        .removePrefix("http://www.")
                        .removePrefix("https://")
                        .removePrefix("http://")
                        .trimEnd('/')
                        .take(30) + if (session.startUrl.length > 38) "..." else "",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                
                Spacer(Modifier.height(4.dp))
                
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = formatDate(session.startTime),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        " • ",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 10.sp
                    )
                    Text(
                        text = "${session.pagesCrawled} pages",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Status Badge
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .background(statusColor.copy(alpha = 0.1f))
                    .padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                Text(
                    text = when(session.status) {
                        "RUNNING" -> "Scanning"
                        "COMPLETED" -> "Done"
                        "FAILED" -> "Failed"
                        else -> session.status
                    },
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = statusColor
                )
            }
        }
    }
}

private fun formatDate(timestamp: Long): String {
    val now = System.currentTimeMillis()
    val diff = now - timestamp
    
    return when {
        diff < 60000 -> "Just now"
        diff < 3600000 -> "${diff / 60000}m ago"
        diff < 86400000 -> "${diff / 3600000}h ago"
        else -> SimpleDateFormat("MMM dd", Locale.getDefault()).format(Date(timestamp))
    }
}
