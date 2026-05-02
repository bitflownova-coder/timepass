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
import androidx.compose.ui.text.font.FontFamily
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
        containerColor = Cyber.Bg
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
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "// ",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 13.sp,
                                color = Cyber.TextSecondary,
                                fontWeight = FontWeight.Normal
                            )
                            Text(
                                "CYBER_RECON",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Black,
                                color = Cyber.Green
                            )
                        }
                        Text(
                            "website intelligence & threat analysis",
                            fontFamily = FontFamily.Monospace,
                            style = MaterialTheme.typography.bodySmall,
                            color = Cyber.TextSecondary
                        )
                    }
                    // Show scanner pulse when a scan is running
                    if (runningCount > 0) {
                        ScannerPulse(color = Cyber.Cyan, rings = true)
                    } else {
                        FilledTonalButton(
                            onClick = { showNewCrawlDialog = true },
                            colors = ButtonDefaults.filledTonalButtonColors(
                                containerColor = Cyber.Green.copy(alpha = 0.15f),
                                contentColor = Cyber.Green
                            ),
                            shape = RoundedCornerShape(8.dp),
                            border = BorderStroke(1.dp, Cyber.Green.copy(alpha = 0.5f))
                        ) {
                            Icon(Icons.Rounded.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "INIT SCAN",
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
                    }
                }
            }
            
            // Floating new scan button when running
            if (runningCount > 0) {
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        FilledTonalButton(
                            onClick = { showNewCrawlDialog = true },
                            colors = ButtonDefaults.filledTonalButtonColors(
                                containerColor = Cyber.Green.copy(alpha = 0.15f),
                                contentColor = Cyber.Green
                            ),
                            shape = RoundedCornerShape(8.dp),
                            border = BorderStroke(1.dp, Cyber.Green.copy(alpha = 0.5f))
                        ) {
                            Icon(Icons.Rounded.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text(
                                "INIT SCAN",
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
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
                            color = Cyber.Blue,
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            count = runningCount,
                            label = "Running",
                            color = Cyber.Cyan,
                            modifier = Modifier.weight(1f)
                        )
                        StatCard(
                            count = completedCount,
                            label = "Done",
                            color = Cyber.Green,
                            modifier = Modifier.weight(1f)
                        )
                        if (failedCount > 0) {
                            StatCard(
                                count = failedCount,
                                label = "Failed",
                                color = Cyber.Red,
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
                                    selectedContainerColor = Cyber.Green.copy(alpha = 0.15f),
                                    selectedLabelColor = Cyber.Green,
                                    containerColor = Cyber.BgCard,
                                    labelColor = Cyber.TextSecondary
                                ),
                                border = FilterChipDefaults.filterChipBorder(
                                    enabled = true,
                                    selected = selectedFilter == filter,
                                    selectedBorderColor = Cyber.Green.copy(alpha = 0.5f),
                                    borderColor = Cyber.Border
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
                                tint = Cyber.TextSecondary
                            )
                        }
                        DropdownMenu(
                            expanded = showSortMenu,
                            onDismissRequest = { showSortMenu = false },
                            modifier = Modifier.background(Cyber.BgElevated)
                        ) {
                            CrawlSort.entries.forEach { sort ->
                                DropdownMenuItem(
                                    text = { 
                                        Text(
                                            sort.label,
                                            color = if (selectedSort == sort) Cyber.Green else Cyber.TextPrimary,
                                            fontWeight = if (selectedSort == sort) FontWeight.Bold else FontWeight.Normal,
                                            fontFamily = FontFamily.Monospace,
                                            fontSize = 13.sp
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
                                                tint = Cyber.Green
                                            )
                                        }
                                    },
                                    colors = MenuDefaults.itemColors(
                                        textColor = Cyber.TextSecondary
                                    )
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
                        fontFamily = FontFamily.Monospace,
                        color = Cyber.TextSecondary
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
                            shape = RoundedCornerShape(8.dp),
                            border = BorderStroke(1.dp, Cyber.Green.copy(alpha = 0.4f)),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = Cyber.Green
                            )
                        ) {
                            Text(
                                "[ LOAD MORE: ${filteredSessions.size - visibleCount} remaining ]",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 12.sp
                            )
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
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(Cyber.BgCard)
            .border(1.dp, color.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
            .padding(12.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                "$count",
                fontFamily = FontFamily.Monospace,
                fontSize = 22.sp,
                fontWeight = FontWeight.Black,
                color = color
            )
            Text(
                label.uppercase(),
                fontFamily = FontFamily.Monospace,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = color.copy(alpha = 0.7f),
                letterSpacing = 1.sp
            )
        }
    }
}

@Composable
fun NoResultsContent(searchQuery: String, filter: CrawlFilter) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Cyber.BgCard)
            .border(1.dp, Cyber.Border, RoundedCornerShape(12.dp))
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                Icons.Outlined.SearchOff,
                contentDescription = null,
                modifier = Modifier.size(40.dp),
                tint = Cyber.TextSecondary
            )
            Spacer(Modifier.height(10.dp))
            Text(
                "// NO_RESULTS",
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = Cyber.TextSecondary
            )
            Text(
                if (searchQuery.isNotEmpty()) "try a different search term"
                else "no ${filter.label.lowercase()} scans recorded",
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                color = Cyber.TextSecondary.copy(alpha = 0.6f)
            )
        }
    }
}

@Composable
fun EmptyDashboardContent(onNewCrawl: () -> Unit = {}) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Cyber.BgCard)
            .border(1.dp, Cyber.Green.copy(alpha = 0.25f), RoundedCornerShape(12.dp))
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .background(
                        Cyber.Green.copy(alpha = 0.08f),
                        CircleShape
                    )
                    .border(1.dp, Cyber.Green.copy(alpha = 0.3f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Rounded.Language,
                    contentDescription = null,
                    modifier = Modifier.size(36.dp),
                    tint = Cyber.Green
                )
            }
            Spacer(Modifier.height(16.dp))
            Text(
                "// NO_SCANS_RECORDED",
                fontFamily = FontFamily.Monospace,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Cyber.TextPrimary
            )
            Spacer(Modifier.height(6.dp))
            Text(
                "initialize a recon mission to get started",
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                color = Cyber.TextSecondary
            )
            Spacer(Modifier.height(20.dp))
            Button(
                onClick = onNewCrawl,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Cyber.Green.copy(alpha = 0.15f),
                    contentColor = Cyber.Green
                ),
                border = BorderStroke(1.dp, Cyber.Green.copy(alpha = 0.5f)),
                shape = RoundedCornerShape(8.dp),
                elevation = ButtonDefaults.buttonElevation(0.dp)
            ) {
                Icon(Icons.Rounded.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    "INIT SCAN",
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
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
        containerColor = Cyber.BgCard,
        titleContentColor = Cyber.Green,
        textContentColor = Cyber.TextPrimary,
        title = { 
            Column {
                Text(
                    "// INIT_RECON_MISSION",
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = Cyber.Green
                )
                Text(
                    "configure target & scan modules",
                    fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp,
                    color = Cyber.TextSecondary
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
                        label = { Text("Target URL", color = Cyber.TextSecondary, fontFamily = FontFamily.Monospace) },
                        placeholder = { Text("https://example.com", color = Cyber.TextSecondary) },
                        leadingIcon = { Icon(Icons.Default.Language, contentDescription = null, tint = Cyber.Cyan) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 16.dp),
                        shape = RoundedCornerShape(8.dp),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            unfocusedBorderColor = Cyber.Border,
                            focusedBorderColor = Cyber.Green,
                            unfocusedContainerColor = Cyber.Bg,
                            focusedContainerColor = Cyber.Bg,
                            cursorColor = Cyber.Green,
                            focusedTextColor = Cyber.TextPrimary,
                            unfocusedTextColor = Cyber.TextPrimary
                        )
                    )
                }
                
                // Scan Mode Selection - VISIBLE BY DEFAULT
                item {
                    Text(
                        "SCAN_MODE",
                        fontFamily = FontFamily.Monospace,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Cyber.TextSecondary,
                        letterSpacing = 1.sp,
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
                            color = Cyber.Green,
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
                            color = Cyber.Cyan,
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
                            color = Cyber.Purple,
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
                            "SELECT_MODULES",
                            fontFamily = FontFamily.Monospace,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp,
                            color = Cyber.TextSecondary
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
                    HorizontalDivider(color = Cyber.Border)
                    Spacer(Modifier.height(12.dp))
                }
                
                // Crawl depth
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "CRAWL_DEPTH",
                            fontFamily = FontFamily.Monospace,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Cyber.TextSecondary
                        )
                        Text(
                            "${depth.toInt()} levels deep",
                            fontFamily = FontFamily.Monospace,
                            fontSize = 11.sp,
                            color = Cyber.Cyan,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Slider(
                        value = depth,
                        onValueChange = { depth = it },
                        valueRange = 1f..5f,
                        steps = 3,
                        colors = SliderDefaults.colors(
                            thumbColor = Cyber.Green,
                            activeTrackColor = Cyber.Green,
                            inactiveTrackColor = Cyber.Border
                        )
                    )
                }

                // Mobile toggle
                item {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(Cyber.Bg)
                            .border(1.dp, Cyber.Border, RoundedCornerShape(8.dp))
                            .clickable { isMobile = !isMobile }
                            .padding(horizontal = 12.dp, vertical = 8.dp)
                    ) {
                        Checkbox(
                            checked = isMobile,
                            onCheckedChange = { isMobile = it },
                            colors = CheckboxDefaults.colors(
                                checkedColor = Cyber.Green,
                                uncheckedColor = Cyber.Border
                            )
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "Mobile User-Agent",
                            fontFamily = FontFamily.Monospace,
                            fontSize = 12.sp,
                            color = Cyber.TextPrimary
                        )
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
                enabled = !isProcessing && url.length > 8 && categories.values.any { it },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Cyber.Green.copy(alpha = 0.2f),
                    contentColor = Cyber.Green,
                    disabledContainerColor = Cyber.BgElevated,
                    disabledContentColor = Cyber.TextSecondary
                ),
                border = BorderStroke(1.dp, Cyber.Green.copy(alpha = 0.5f)),
                elevation = ButtonDefaults.buttonElevation(0.dp)
            ) {
                if (isProcessing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(16.dp),
                        strokeWidth = 2.dp,
                        color = Cyber.Green
                    )
                    Spacer(Modifier.width(8.dp))
                }
                Text(
                    if(isProcessing) "LAUNCHING..." else "LAUNCH SCAN",
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
            }
        },
        dismissButton = {
            TextButton(
                onClick = { onDismiss() },
                enabled = !isProcessing,
                colors = ButtonDefaults.textButtonColors(contentColor = Cyber.TextSecondary)
            ) {
                Text(
                    "ABORT",
                    fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp
                )
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
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (selected) color.copy(alpha = 0.12f) else Cyber.Bg)
            .border(
                width = if (selected) 2.dp else 1.dp,
                color = if (selected) color else Cyber.Border,
                shape = RoundedCornerShape(8.dp)
            )
            .clickable(onClick = onClick)
            .padding(10.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(icon, fontSize = 20.sp)
            Spacer(Modifier.height(4.dp))
            Text(
                title.uppercase(),
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                fontSize = 11.sp,
                color = if (selected) color else Cyber.TextSecondary
            )
            Text(
                subtitle,
                fontFamily = FontFamily.Monospace,
                fontSize = 10.sp,
                color = if (selected) color.copy(alpha = 0.7f) else Cyber.TextSecondary.copy(alpha = 0.5f)
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
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(if (selected) Cyber.Green.copy(alpha = 0.08f) else Cyber.Bg)
            .border(
                width = 1.dp,
                color = if (selected) Cyber.Green.copy(alpha = 0.5f) else Cyber.Border,
                shape = RoundedCornerShape(6.dp)
            )
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 7.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(icon, fontSize = 14.sp)
            Spacer(Modifier.width(5.dp))
            Text(
                name,
                fontFamily = FontFamily.Monospace,
                fontSize = 11.sp,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                color = if (selected) Cyber.Green else Cyber.TextSecondary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f)
            )
            if (selected) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    modifier = Modifier.size(12.dp),
                    tint = Cyber.Green
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
    
    val domain = session.startUrl
        .removePrefix("https://www.")
        .removePrefix("http://www.")
        .removePrefix("https://")
        .removePrefix("http://")
        .trimEnd('/')
    
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(Cyber.BgCard)
            .border(1.dp, statusColor.copy(alpha = if (isRunning) 0.6f else 0.2f), RoundedCornerShape(10.dp))
            .clickable(onClick = onClick)
    ) {
        // Left accent bar
        Box(
            modifier = Modifier
                .width(3.dp)
                .matchParentSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(statusColor, statusColor.copy(alpha = 0.3f))
                    )
                )
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 14.dp, end = 14.dp, top = 12.dp, bottom = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Status Indicator
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(statusColor.copy(alpha = 0.1f))
                    .border(1.dp, statusColor.copy(alpha = 0.3f), RoundedCornerShape(6.dp)),
                contentAlignment = Alignment.Center
            ) {
                if (isRunning) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = statusColor
                    )
                } else {
                    Icon(
                        if (isCompleted) Icons.Default.CheckCircle else Icons.Default.Warning,
                        contentDescription = null,
                        tint = statusColor,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
            
            Spacer(Modifier.width(12.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = domain.take(35) + if (domain.length > 35) "..." else "",
                    fontFamily = FontFamily.Monospace,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                
                Spacer(Modifier.height(3.dp))
                
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = formatDate(session.startTime),
                        fontFamily = FontFamily.Monospace,
                        fontSize = 10.sp,
                        color = Cyber.TextSecondary
                    )
                    Text(
                        " │ ",
                        fontFamily = FontFamily.Monospace,
                        color = Cyber.Border,
                        fontSize = 10.sp
                    )
                    Text(
                        text = "${session.pagesCrawled}p",
                        fontFamily = FontFamily.Monospace,
                        fontSize = 10.sp,
                        color = Cyber.TextSecondary
                    )
                }
            }
            
            // Status Badge
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(4.dp))
                    .background(statusColor.copy(alpha = 0.1f))
                    .border(1.dp, statusColor.copy(alpha = 0.3f), RoundedCornerShape(4.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Text(
                    text = when(session.status) {
                        "RUNNING" -> "SCAN"
                        "COMPLETED" -> "DONE"
                        "FAILED" -> "FAIL"
                        else -> session.status
                    },
                    fontFamily = FontFamily.Monospace,
                    fontSize = 10.sp,
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
