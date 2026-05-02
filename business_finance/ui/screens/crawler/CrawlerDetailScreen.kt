package com.bitflow.finance.ui.screens.crawler

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
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
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.navigation.NavController
import coil.compose.rememberAsyncImagePainter
import java.io.File
import com.bitflow.finance.data.local.entity.CrawlSessionEntity
import com.bitflow.finance.domain.crawler.*
import com.bitflow.finance.domain.repository.SessionFiles

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CrawlerDetailScreen(
    viewModel: CrawlerViewModel,
    navController: NavController,
    sessionId: Long
) {
    val session by viewModel.getSession(sessionId).collectAsState(initial = null)
    val analysisReport by viewModel.analysisReport.collectAsState()
    val sessionFiles by viewModel.sessionFiles.collectAsState()
    val isLoadingAnalysis by viewModel.isLoadingAnalysis.collectAsState()
    
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Overview", "SEO", "Security", "OSINT", "Pages", "Media", "Files")
    
    val context = LocalContext.current
    
    // Load data when session is available
    LaunchedEffect(session) {
        session?.let {
            viewModel.loadSessionFiles(it.id)
            if (it.status == "COMPLETED") {
                viewModel.loadAnalysisReport(it.id)
            }
        }
    }
    
    // Also load analysis when crawl completes
    LaunchedEffect(session?.status) {
        if (session?.status == "COMPLETED") {
            viewModel.loadAnalysisReport(sessionId)
        }
    }
    
    DisposableEffect(Unit) {
        onDispose {
            viewModel.clearAnalysisData()
        }
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            session?.let { s ->
                val statusColor = getStatusColor(s.status)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(
                                    statusColor.copy(alpha = 0.2f),
                                    MaterialTheme.colorScheme.background
                                )
                            )
                        )
                ) {
                    TopAppBar(
                        title = { 
                            Column {
                                Text(
                                    "Crawl Results",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    s.startUrl
                                        .removePrefix("https://www.")
                                        .removePrefix("http://www.")
                                        .removePrefix("https://")
                                        .removePrefix("http://")
                                        .trimEnd('/'), 
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    maxLines = 1
                                ) 
                            } 
                        },
                        navigationIcon = {
                            IconButton(onClick = { navController.popBackStack() }) {
                                Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                            }
                        },
                        actions = {
                            StatusChip(s.status, statusColor)
                            
                            var showMenu by remember { mutableStateOf(false) }
                            
                            IconButton(onClick = { showMenu = true }) {
                                Icon(Icons.Default.MoreVert, contentDescription = "More")
                            }
                            
                            DropdownMenu(
                                expanded = showMenu,
                                onDismissRequest = { showMenu = false }
                            ) {
                                DropdownMenuItem(
                                    text = { Text("Export PDF Report") },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.generatePdf(s.id) { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.PictureAsPdf, contentDescription = null) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Export CSV") },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.exportData(s.id, "csv") { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.TableChart, contentDescription = null) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Export JSON") },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.exportData(s.id, "json") { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.DataObject, contentDescription = null) }
                                )
                                Divider()
                                DropdownMenuItem(
                                    text = { Text("Generate Sitemap") },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.generateSitemap(s.id) { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.Map, contentDescription = null) }
                                )
                                Divider()
                            }
                            Spacer(Modifier.width(8.dp))
                        },
                        colors = TopAppBarDefaults.topAppBarColors(
                            containerColor = Color.Transparent
                        )
                    )
                }
            }
        }
    ) { padding ->
        Column(modifier = Modifier
            .padding(padding)
            .fillMaxSize()) {
            
            // Tab Row
            ScrollableTabRow(
                selectedTabIndex = selectedTab,
                containerColor = MaterialTheme.colorScheme.background,
                contentColor = MaterialTheme.colorScheme.primary,
                edgePadding = 16.dp,
                indicator = { tabPositions ->
                    if (selectedTab < tabPositions.size) {
                        TabRowDefaults.Indicator(
                            modifier = Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                            height = 3.dp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                },
                divider = {}
            ) {
                tabs.forEachIndexed { index, title ->
                    val selected = selectedTab == index
                    Tab(
                        selected = selected,
                        onClick = { selectedTab = index },
                        text = { 
                            Text(title, fontWeight = if(selected) FontWeight.Bold else FontWeight.Normal)
                        }
                    )
                }
            }
            
            Divider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha=0.3f))

            Box(modifier = Modifier.weight(1f)) {
                 when (selectedTab) {
                    0 -> OverviewTab(session, analysisReport, isLoadingAnalysis, viewModel) { tabIndex ->
                        selectedTab = tabIndex
                    }
                    1 -> SeoTab(analysisReport)
                    2 -> SecurityTab(analysisReport)
                    3 -> OsintTab(analysisReport)
                    4 -> PagesTab(analysisReport)
                    5 -> MediaTab(sessionFiles)
                    6 -> FilesTab(sessionFiles)
                }
            }
        }
    }
}

@Composable
fun OverviewTab(
    session: CrawlSessionEntity?, 
    report: AnalysisReport?,
    isLoading: Boolean,
    viewModel: CrawlerViewModel,
    onTabSelected: (Int) -> Unit = {}
) {
    if (session == null) return

    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Live Progress Section (when running)
        if (session.status == "RUNNING") {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            // Animated scanning indicator
                            val infiniteTransition = rememberInfiniteTransition(label = "scan")
                            val alpha by infiniteTransition.animateFloat(
                                initialValue = 0.3f,
                                targetValue = 1f,
                                animationSpec = infiniteRepeatable(
                                    animation = tween(800),
                                    repeatMode = RepeatMode.Reverse
                                ),
                                label = "pulse"
                            )
                            Box(
                                modifier = Modifier
                                    .size(12.dp)
                                    .clip(CircleShape)
                                    .background(MaterialTheme.colorScheme.primary.copy(alpha = alpha))
                            )
                            Spacer(Modifier.width(12.dp))
                            Text(
                                "Scanning...",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                        
                        Spacer(Modifier.height(12.dp))
                        
                        // Progress bar
                        val progress = if (session.pagesTotal > 0) {
                            session.pagesCrawled.toFloat() / session.pagesTotal
                        } else 0.1f
                        
                        LinearProgressIndicator(
                            progress = progress.coerceIn(0f, 1f),
                            modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
                            color = MaterialTheme.colorScheme.primary,
                            trackColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
                        )
                        
                        Spacer(Modifier.height(8.dp))
                        
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                "${session.pagesCrawled} pages crawled",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                            Text(
                                "${session.pagesQueued} queued",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }
                        
                        if (session.currentUrl.isNotBlank()) {
                            Spacer(Modifier.height(8.dp))
                            Text(
                                "Currently: ${session.currentUrl}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
            }
        }
        
        // Controls Section
        if (session.status == "RUNNING" || session.status == "PAUSED") {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(
                        onClick = { viewModel.stopCrawl(session.id) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                         Icon(Icons.Default.Stop, contentDescription = null)
                         Spacer(Modifier.width(8.dp))
                         Text("Stop Crawl")
                    }
                }
            }
        }

        // Health Score Card
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(2.dp)
            ) {
                Column(Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    
                    // Health Score Circle
                    val score = report?.healthScore ?: 0
                    val scoreColor = when {
                        score >= 80 -> Color(0xFF10B981) // Green
                        score >= 50 -> Color(0xFFF59E0B) // Yellow
                        else -> Color(0xFFEF4444) // Red
                    }
                    
                    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(160.dp)) {
                        Canvas(modifier = Modifier.size(140.dp)) {
                            val strokeWidth = 12.dp.toPx()
                            
                            // Background circle
                            drawCircle(
                                color = scoreColor.copy(alpha = 0.1f),
                                style = Stroke(width = strokeWidth)
                            )
                            
                            // Progress arc
                            val sweepAngle = (score / 100f) * 360f
                            drawArc(
                                color = scoreColor,
                                startAngle = -90f,
                                sweepAngle = sweepAngle,
                                useCenter = false,
                                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                            )
                        }
                        
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            if (isLoading || session.status == "RUNNING") {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(32.dp),
                                    strokeWidth = 3.dp
                                )
                            } else {
                                // Show grade letter if available, else score
                                val grade = report?.securityGrade
                                if (grade != null) {
                                    Text(
                                        grade,
                                        style = MaterialTheme.typography.displayLarge,
                                        fontWeight = FontWeight.Black,
                                        color = scoreColor
                                    )
                                } else {
                                    Text(
                                        "$score",
                                        style = MaterialTheme.typography.displayMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = scoreColor
                                    )
                                }
                            }
                            Text(
                                if (report?.securityGrade != null) "SECURITY GRADE" else "HEALTH SCORE",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    
                    if (report != null && score < 100) {
                        Spacer(Modifier.height(16.dp))
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(MaterialTheme.colorScheme.errorContainer.copy(alpha=0.1f), RoundedCornerShape(8.dp))
                                .padding(12.dp)
                        ) {
                            Text(
                                "Why this score?",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Spacer(Modifier.height(4.dp))
                            
                            if (report.seoIssues.isNotEmpty()) {
                                Text(
                                    "• -${(report.seoIssues.size * 2).coerceAtMost(30)} pts: ${report.seoIssues.size} SEO Issues",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.error
                                )
                            }
                            if (report.securityIssues.isNotEmpty()) {
                                Text(
                                    "• -${(report.securityIssues.size * 3).coerceAtMost(30)} pts: ${report.securityIssues.size} Security Issues",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.error
                                )
                            }
                            if (report.ssl?.valid != true) {
                                Text(
                                    "• -20 pts: Missing or Invalid SSL",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.error
                                )
                            }
                        }
                    }
                    
                    Spacer(Modifier.height(24.dp))
                    
                    // Stats Row
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                        StatItem(label = "Pages", value = "${session.pagesCrawled}")
                        StatItem(label = "Depth", value = "${session.depth}")
                        StatItem(label = "Duration", value = formatDuration(session.startTime, session.endTime))
                    }
                }
            }
        }
        
        // Quick Stats Cards
        if (report != null) {
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Search,
                        label = "SEO Issues",
                        value = "${report.seoIssues.size}",
                        color = if (report.seoIssues.isEmpty()) Color(0xFF10B981) else Color(0xFFF59E0B),
                        description = if (report.seoIssues.isEmpty()) "Well optimized!" else "Needs improvement",
                        onClick = { onTabSelected(1) } // Navigate to SEO tab
                    )
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Security,
                        label = "Security Issues",
                        value = "${report.securityIssues.size}",
                        color = if (report.securityIssues.isEmpty()) Color(0xFF10B981) else Color(0xFFEF4444),
                        description = if (report.securityIssues.isEmpty()) "Secure headers" else "Headers missing",
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                }
            }
            
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Lock,
                        label = "SSL",
                        value = if (report.ssl?.valid == true) "Valid" else "Invalid",
                        color = if (report.ssl?.valid == true) Color(0xFF10B981) else Color(0xFFEF4444),
                        description = if (report.ssl?.valid == true) "HTTPS secured" else "Not secure!",
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Visibility,
                        label = "Hidden Paths",
                        value = "${report.hiddenPaths.size}",
                        color = if (report.hiddenPaths.isEmpty()) Color(0xFF10B981) else Color(0xFF6366F1),
                        description = if (report.hiddenPaths.isEmpty()) "No exposed paths" else "Exposed endpoints",
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                }
            }
            
            // NEW: Secrets & Vulnerabilities Row
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.VpnKey,
                        label = "Secrets Leaked",
                        value = "${report.secretsFound.size}",
                        color = if (report.secretsFound.isEmpty()) Color(0xFF10B981) else Color(0xFFEF4444),
                        description = if (report.secretsFound.isEmpty()) "No leaks found" else "CRITICAL! Fix now",
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.BugReport,
                        label = "Vulnerabilities",
                        value = "${report.vulnerabilities.size}",
                        color = when {
                            report.vulnerabilities.isEmpty() -> Color(0xFF10B981)
                            report.criticalVulnerabilities > 0 -> Color(0xFFEF4444)
                            report.highVulnerabilities > 0 -> Color(0xFFF97316)
                            else -> Color(0xFFF59E0B)
                        },
                        description = when {
                            report.vulnerabilities.isEmpty() -> "No vulns detected"
                            report.criticalVulnerabilities > 0 -> "${report.criticalVulnerabilities} CRITICAL!"
                            report.highVulnerabilities > 0 -> "${report.highVulnerabilities} high severity"
                            else -> "Low/Medium issues"
                        },
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                }
            }
            
            // NEW: Technologies & OSINT Row
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Code,
                        label = "Technologies",
                        value = "${report.technologies.size}",
                        color = if (report.technologies.isEmpty()) Color(0xFF6B7280) else Color(0xFF8B5CF6),
                        description = if (report.technologies.isEmpty()) "Not detected" else "Stack identified",
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.PersonSearch,
                        label = "OSINT Data",
                        value = "${(report.osintSummary?.counts?.emails ?: 0) + (report.osintSummary?.counts?.phones ?: 0)}",
                        color = if ((report.osintSummary?.counts?.emails ?: 0) > 0) Color(0xFF06B6D4) else Color(0xFF6B7280),
                        description = if ((report.osintSummary?.counts?.emails ?: 0) > 0) "Contacts found" else "No data found",
                        onClick = { onTabSelected(3) } // Navigate to OSINT tab
                    )
                }
            }
            
            // NEW: Forms & Cookies Row  
            item {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    val formsWithoutCsrf = report.formsFound.count { !it.effectiveHasCsrf }
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Description,
                        label = "Forms Found",
                        value = "${report.formsFound.size}",
                        color = when {
                            report.formsFound.isEmpty() -> Color(0xFF6B7280)
                            formsWithoutCsrf > 0 -> Color(0xFFF59E0B)
                            else -> Color(0xFF14B8A6)
                        },
                        description = when {
                            report.formsFound.isEmpty() -> "No forms detected"
                            formsWithoutCsrf > 0 -> "$formsWithoutCsrf without CSRF"
                            else -> "All have CSRF"
                        },
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                    val insecureCookies = report.cookiesFound.count { it.issues.isNotEmpty() }
                    QuickStatCard(
                        modifier = Modifier.weight(1f),
                        icon = Icons.Outlined.Storage,
                        label = "Cookies",
                        value = "${report.cookiesFound.size}",
                        color = when {
                            report.cookiesFound.isEmpty() -> Color(0xFF6B7280)
                            insecureCookies > 0 -> Color(0xFFF59E0B)
                            else -> Color(0xFF10B981)
                        },
                        description = when {
                            report.cookiesFound.isEmpty() -> "No cookies found"
                            insecureCookies > 0 -> "$insecureCookies insecure"
                            else -> "All secure"
                        },
                        onClick = { onTabSelected(2) } // Navigate to Security tab
                    )
                }
            }
        }
    }
}

@Composable
fun QuickStatCard(
    modifier: Modifier = Modifier,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
    color: Color,
    description: String? = null,
    onClick: (() -> Unit)? = null
) {
    Card(
        modifier = modifier.then(
            if (onClick != null) Modifier.clickable { onClick() } else Modifier
        ),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(24.dp))
            Spacer(Modifier.width(12.dp))
            Column {
                Text(value, fontWeight = FontWeight.Bold, fontSize = 18.sp, color = color)
                Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (description != null) {
                    Text(
                        description, 
                        style = MaterialTheme.typography.labelSmall, 
                        color = color.copy(alpha = 0.8f),
                        fontSize = 9.sp
                    )
                }
            }
        }
    }
}

@Composable
fun SeoTab(report: AnalysisReport?) {
    if (report == null) {
        EmptyState("Complete crawl to see SEO analysis", Icons.Outlined.Search)
        return
    }
    
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        if (report.seoIssues.isEmpty()) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981))
                        Spacer(Modifier.width(12.dp))
                        Text("No SEO issues found!", fontWeight = FontWeight.Medium)
                    }
                }
            }
        } else {
            items(report.seoIssues) { issue ->
                IssueCard(url = issue.url, issue = issue.issue, color = Color(0xFFF59E0B))
            }
        }
    }
}

@Composable
fun SecurityTab(report: AnalysisReport?) {
    if (report == null) {
        EmptyState("Complete crawl to see security analysis", Icons.Outlined.Security)
        return
    }
    
    // Track which sections are expanded
    var expandedSection by remember { mutableStateOf<String?>("summary") }
    
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Show error if one exists (Debugging)
        if (report.error != null) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Warning, null, tint = MaterialTheme.colorScheme.onErrorContainer)
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "Scanner Error", 
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                        }
                        Spacer(Modifier.height(4.dp))
                        Text(
                            report.error, 
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }
            }
        }

        // ============ SECURITY SUMMARY HEADER ============
        item {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Grade Circle
                    val grade = report.securityGrade ?: "?"
                    val score = report.healthScore
                    val gradeColor = when {
                        score >= 90 -> Color(0xFF10B981)
                        score >= 70 -> Color(0xFFF59E0B)
                        score >= 50 -> Color(0xFFF97316)
                        else -> Color(0xFFEF4444)
                    }
                    
                    Box(
                        modifier = Modifier
                            .size(80.dp)
                            .clip(CircleShape)
                            .background(gradeColor.copy(alpha = 0.15f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            grade,
                            style = MaterialTheme.typography.displaySmall,
                            fontWeight = FontWeight.Black,
                            color = gradeColor
                        )
                    }
                    
                    Spacer(Modifier.height(8.dp))
                    Text("Security Score: $score/100", fontWeight = FontWeight.Bold)
                    
                    Spacer(Modifier.height(16.dp))
                    
                    // Quick stats row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        MiniStat(
                            value = "${report.criticalVulnerabilities}",
                            label = "Critical",
                            color = if (report.criticalVulnerabilities > 0) Color(0xFFEF4444) else Color(0xFF10B981)
                        )
                        MiniStat(
                            value = "${report.highVulnerabilities}",
                            label = "High",
                            color = if (report.highVulnerabilities > 0) Color(0xFFF97316) else Color(0xFF10B981)
                        )
                        MiniStat(
                            value = "${report.secretsFound.size}",
                            label = "Secrets",
                            color = if (report.secretsFound.isNotEmpty()) Color(0xFFEF4444) else Color(0xFF10B981)
                        )
                        MiniStat(
                            value = if (report.ssl?.valid == true) "✓" else "✗",
                            label = "SSL",
                            color = if (report.ssl?.valid == true) Color(0xFF10B981) else Color(0xFFEF4444)
                        )
                    }
                }
            }
        }
        
        // ============ FEATURE SECTIONS ============
        
        // 1. SSL/TLS Analysis
        item {
            val hasData = report.ssl != null || report.sslAnalysis != null
            FeatureSection(
                title = "🔒 SSL/TLS Certificate",
                subtitle = when {
                    report.sslAnalysis != null -> "Grade: ${report.sslAnalysis.grade}"
                    report.ssl?.valid == true -> "Valid certificate"
                    report.ssl != null -> "Issues found"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "ssl",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "ssl") null else "ssl" }
            ) {
                report.ssl?.let { ssl ->
                    DetailRow("Status", if (ssl.valid) "✓ Valid" else "✗ Invalid")
                    ssl.issuer?.let { DetailRow("Issuer", it) }
                    ssl.expires?.let { DetailRow("Expires", it) }
                    ssl.protocol?.let { DetailRow("Protocol", it) }
                }
                report.sslAnalysis?.let { analysis ->
                    Spacer(Modifier.height(8.dp))
                    Text("Detailed Analysis", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    analysis.certificate?.let { cert ->
                        DetailRow("Days Until Expiry", "${cert.daysUntilExpiry}")
                    }
                }
            }
        }
        
        // 2. Security Headers
        item {
            val hasData = report.securityHeaders != null
            FeatureSection(
                title = "🛡️ Security Headers",
                subtitle = report.securityHeaders?.let { "Grade: ${it.grade} (${it.score}/100)" } ?: "Not scanned",
                expanded = expandedSection == "headers",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "headers") null else "headers" }
            ) {
                report.securityHeaders?.let { headers ->
                    if (headers.missingHeaders.isNotEmpty()) {
                        Text("Missing Headers:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFFEF4444))
                        Spacer(Modifier.height(4.dp))
                        headers.missingHeaders.forEach { h ->
                            Text("• ${h.displayName}", fontSize = 12.sp)
                        }
                    }
                    if (headers.presentHeaders.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Present Headers:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFF10B981))
                        Spacer(Modifier.height(4.dp))
                        headers.presentHeaders.take(5).forEach { h ->
                            Text("✓ ${h.displayName}", fontSize = 12.sp, color = Color(0xFF10B981))
                        }
                    }
                }
            }
        }
        
        // 3. DNS Reconnaissance
        item {
            val hasData = report.dnsRecon != null
            FeatureSection(
                title = "🌐 DNS Reconnaissance",
                subtitle = report.dnsRecon?.let { "Domain: ${it.domain}" } ?: "Not scanned",
                expanded = expandedSection == "dns",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "dns") null else "dns" }
            ) {
                report.dnsRecon?.let { dns ->
                    DetailRow("Domain", dns.domain)
                    dns.nameServers.takeIf { it.isNotEmpty() }?.let {
                        DetailRow("Nameservers", it.take(3).joinToString(", "))
                    }
                    dns.mxRecords.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(8.dp))
                        Text("MX Records:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        it.take(3).forEach { mx ->
                            Text("• ${mx.host} (priority: ${mx.priority})", fontSize = 12.sp)
                        }
                    }
                }
            }
        }
        
        // 4. Email Security
        item {
            val hasData = report.emailSecurity != null
            FeatureSection(
                title = "📧 Email Security",
                subtitle = report.emailSecurity?.let { "Grade: ${it.grade}" } ?: "Not scanned",
                expanded = expandedSection == "email",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "email") null else "email" }
            ) {
                report.emailSecurity?.let { email ->
                    email.spf?.let { spf ->
                        DetailRow("SPF", if (spf.present) "✓ Present" else "✗ Missing")
                    }
                    email.dmarc?.let { dmarc ->
                        DetailRow("DMARC", if (dmarc.present) "✓ Present (${dmarc.policy})" else "✗ Missing")
                    }
                    email.dkim?.let { dkim ->
                        DetailRow("DKIM", if (dkim.checked && dkim.selectorsFound.isNotEmpty()) "✓ Found" else "✗ Not found")
                    }
                }
            }
        }
        
        // 5. Subdomain Enumeration
        item {
            val count = report.subdomainEnum?.subdomains?.size ?: report.subdomains.size
            val hasData = count > 0 || report.subdomainEnum != null
            FeatureSection(
                title = "🔍 Subdomain Discovery",
                subtitle = if (count > 0) "$count subdomains found" else "Not scanned",
                expanded = expandedSection == "subdomains",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "subdomains") null else "subdomains" }
            ) {
                report.subdomainEnum?.let { subEnum ->
                    DetailRow("Total Found", "${subEnum.totalFound}")
                    DetailRow("Live", "${subEnum.liveCount}")
                    if (subEnum.subdomains.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Discovered:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        subEnum.subdomains.take(10).forEach { sub ->
                            val status = if (sub.live) "🟢" else "🔴"
                            Text("$status ${sub.subdomain}", fontSize = 12.sp)
                        }
                    }
                } ?: run {
                    report.subdomains.take(10).forEach { sub ->
                        Text("• ${sub.url}", fontSize = 12.sp)
                    }
                }
            }
        }
        
        // 6. API Discovery
        item {
            val hasData = report.apiDiscovery != null && report.apiDiscovery.totalEndpoints > 0
            FeatureSection(
                title = "📡 API Discovery",
                subtitle = report.apiDiscovery?.let { "${it.totalEndpoints} endpoints found" } ?: "Not scanned",
                expanded = expandedSection == "api",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "api") null else "api" }
            ) {
                report.apiDiscovery?.let { api ->
                    if (api.swaggerSpecs.isNotEmpty()) {
                        Text("Swagger/OpenAPI:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFF10B981))
                        api.swaggerSpecs.take(3).forEach { spec ->
                            Text("• ${spec.title.ifEmpty { spec.url }}", fontSize = 12.sp)
                        }
                    }
                    if (api.graphqlEndpoints.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("GraphQL Endpoints:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFFE535AB))
                        api.graphqlEndpoints.take(3).forEach { ep ->
                            Text("• ${ep.url}", fontSize = 12.sp)
                        }
                    }
                    if (api.restEndpoints.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("REST Endpoints:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFF3B82F6))
                        api.restEndpoints.take(5).forEach { ep ->
                            Text("• ${ep.method} ${ep.path}", fontSize = 12.sp)
                        }
                    }
                }
            }
        }
        
        // 7. Parameter Fuzzing
        item {
            val hasData = report.paramFuzzing != null && report.paramFuzzing.totalFound > 0
            FeatureSection(
                title = "⚡ Parameter Discovery",
                subtitle = report.paramFuzzing?.let { "${it.totalFound} params, ${it.reflectedParams.size} reflected" } ?: "Not scanned",
                expanded = expandedSection == "params",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "params") null else "params" }
            ) {
                report.paramFuzzing?.let { params ->
                    if (params.reflectedParams.isNotEmpty()) {
                        Text("⚠️ Reflected Parameters (XSS Risk):", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFFEF4444))
                        params.reflectedParams.take(5).forEach { p ->
                            Text("• ${p.name}", fontSize = 12.sp, color = Color(0xFFEF4444))
                        }
                    }
                    if (params.discoveredParams.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Discovered Parameters:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        params.discoveredParams.take(10).forEach { p ->
                            Text("• ${p.name} (${p.method})", fontSize = 12.sp)
                        }
                    }
                }
            }
        }
        
        // 8. Authentication Testing
        item {
            val hasData = report.authTesting != null && report.authTesting.loginPages.isNotEmpty()
            FeatureSection(
                title = "🔑 Authentication",
                subtitle = report.authTesting?.let { "${it.loginPages.size} login pages" } ?: "Not scanned",
                expanded = expandedSection == "auth",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "auth") null else "auth" }
            ) {
                report.authTesting?.let { auth ->
                    auth.rateLimiting?.let { rate ->
                        DetailRow("Rate Limiting", if (rate.implemented) "✓ Implemented" else "✗ Not detected")
                    }
                    if (auth.loginPages.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Login Pages:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        auth.loginPages.take(5).forEach { page ->
                            Text("• ${page.url}", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                }
            }
        }
        
        // 9. Cloud Storage
        item {
            val exposedCount = report.cloudScanner?.exposedBuckets?.size ?: 0
            val hasData = report.cloudScanner != null && report.cloudScanner.bucketsFound.isNotEmpty()
            FeatureSection(
                title = "☁️ Cloud Storage",
                subtitle = report.cloudScanner?.let { 
                    "${it.bucketsFound.size} found, $exposedCount exposed" 
                } ?: "Not scanned",
                expanded = expandedSection == "cloud",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "cloud") null else "cloud" }
            ) {
                report.cloudScanner?.let { cloud ->
                    if (cloud.exposedBuckets.isNotEmpty()) {
                        Text("⚠️ Exposed Buckets:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Color(0xFFEF4444))
                        cloud.exposedBuckets.take(5).forEach { bucket ->
                            Text("• ${bucket.url}", fontSize = 12.sp, color = Color(0xFFEF4444))
                        }
                    }
                    if (cloud.bucketsFound.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Detected Buckets:", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        cloud.bucketsFound.take(5).forEach { bucket ->
                            Text("• ${bucket.name} (${bucket.provider})", fontSize = 12.sp)
                        }
                    }
                }
            }
        }
        
        // ============ FINDINGS LISTS ============
        
        // Vulnerabilities List
        if (report.vulnerabilities.isNotEmpty()) {
            item {
                Spacer(Modifier.height(16.dp))
                Text(
                    "🐛 Vulnerabilities (${report.vulnerabilities.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }
            items(report.vulnerabilities.take(10)) { vuln ->
                val severityColor = when(vuln.severity) {
                    "Critical" -> Color(0xFFEF4444)
                    "High" -> Color(0xFFF97316)
                    "Medium" -> Color(0xFFF59E0B)
                    else -> Color(0xFF6B7280)
                }
                Card(
                    colors = CardDefaults.cardColors(containerColor = severityColor.copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(vuln.severity)
                            Spacer(Modifier.width(8.dp))
                            Text(vuln.type, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        vuln.cve?.let { cve ->
                            Text(cve, style = MaterialTheme.typography.bodySmall, color = severityColor)
                        }
                        vuln.description?.let { desc ->
                            Text(desc, style = MaterialTheme.typography.bodySmall, maxLines = 2)
                        }
                    }
                }
            }
        }
        
        // Secrets Found
        if (report.secretsFound.isNotEmpty()) {
            item {
                Spacer(Modifier.height(16.dp))
                Text(
                    "🔐 Secrets Leaked (${report.secretsFound.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFEF4444)
                )
            }
            items(report.secretsFound.take(10)) { secret ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(secret.type, fontWeight = FontWeight.Bold, color = Color(0xFFEF4444))
                        Text("File: ${secret.file}", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
        
        // Hidden Paths
        if (report.hiddenPaths.isNotEmpty()) {
            item {
                Spacer(Modifier.height(16.dp))
                Text(
                    "📂 Hidden Paths (${report.hiddenPaths.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }
            items(report.hiddenPaths.take(15)) { path ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF6366F1).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        StatusBadge(path.status)
                        Spacer(Modifier.width(12.dp))
                        Text(path.path, fontWeight = FontWeight.Medium, fontSize = 13.sp)
                    }
                }
            }
        }
        
        // Technologies
        if (report.technologies.isNotEmpty()) {
            item {
                Spacer(Modifier.height(16.dp))
                Text(
                    "💻 Technologies (${report.technologies.size})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    report.technologies.take(10).forEach { tech ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("•", color = Color(0xFF8B5CF6))
                            Spacer(Modifier.width(8.dp))
                            Text(tech.name, fontWeight = FontWeight.Medium)
                            tech.version?.let {
                                Spacer(Modifier.width(4.dp))
                                Text("v$it", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
            }
        }
        
        item { Spacer(Modifier.height(32.dp)) }
    }
}

@Composable
fun MiniStat(value: String, label: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, fontWeight = FontWeight.Black, fontSize = 18.sp, color = color)
        Text(label, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun FeatureSection(
    title: String,
    subtitle: String,
    expanded: Boolean,
    hasData: Boolean,
    onClick: () -> Unit,
    content: @Composable ColumnScope.() -> Unit
) {
    val bgColor = if (hasData) 
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f) 
    else 
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = hasData, onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = bgColor),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(title, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                    Text(
                        subtitle,
                        fontSize = 12.sp,
                        color = if (hasData) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (hasData) {
                    Icon(
                        if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    Text(
                        "N/A",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                    )
                }
            }
            
            AnimatedVisibility(visible = expanded && hasData) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 16.dp, end = 16.dp, bottom = 16.dp)
                ) {
                    Divider(modifier = Modifier.padding(bottom = 12.dp))
                    content()
                }
            }
        }
    }
}

@Composable
fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}
@Composable
fun AdvancedScanSection(
    title: String,
    subtitle: String,
    icon: ImageVector,
    gradeColor: Color
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = gradeColor.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = gradeColor, modifier = Modifier.size(28.dp))
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun MissingHeaderChip(name: String, weight: Int) {
    val severity = when {
        weight >= 20 -> Color(0xFFEF4444)
        weight >= 10 -> Color(0xFFF59E0B)
        else -> Color(0xFF6B7280)
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = severity.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.padding(vertical = 2.dp)
    ) {
        Row(Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("✗", color = severity)
            Spacer(Modifier.width(8.dp))
            Text(name, fontSize = 13.sp, fontWeight = FontWeight.Medium)
        }
    }
}

@Composable
fun SubdomainChip(subdomain: String, live: Boolean, riskLevel: String) {
    val color = when(riskLevel.lowercase()) {
        "high" -> Color(0xFFEF4444)
        "medium" -> Color(0xFFF59E0B)
        else -> if (live) Color(0xFF10B981) else Color(0xFF6B7280)
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.padding(vertical = 2.dp)
    ) {
        Row(Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .background(if (live) Color(0xFF10B981) else Color(0xFF6B7280), CircleShape)
            )
            Spacer(Modifier.width(8.dp))
            Text(subdomain, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
fun ExposedBucketCard(bucket: com.bitflow.finance.domain.crawler.ExposedBucket) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f)),
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFEF4444), modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(bucket.name, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
            Text("Provider: ${bucket.provider}", style = MaterialTheme.typography.bodySmall)
            if (bucket.listingEnabled) {
                Text("⚠️ Directory listing enabled!", style = MaterialTheme.typography.bodySmall, color = Color(0xFFEF4444))
            }
        }
    }
}

fun getGradeColor(grade: String): Color {
    return when(grade.uppercase()) {
        "A", "A+" -> Color(0xFF10B981)
        "B" -> Color(0xFF22C55E)
        "C" -> Color(0xFFF59E0B)
        "D" -> Color(0xFFF97316)
        "E", "F" -> Color(0xFFEF4444)
        else -> Color(0xFF6B7280)
    }
}

@Composable
fun SecurityInfoCard(title: String, subtitle: String, icon: androidx.compose.ui.graphics.vector.ImageVector, color: Color) {
    Card(
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = color)
            Spacer(Modifier.width(12.dp))
            Column {
                Text(title, fontWeight = FontWeight.Bold)
                Text(subtitle, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
fun SeverityBadge(severity: String) {
    val color = when(severity) {
        "Critical" -> Color(0xFFEF4444)
        "High" -> Color(0xFFF97316)
        "Medium" -> Color(0xFFF59E0B)
        else -> Color(0xFF6B7280)
    }
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color)
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(severity, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.White)
    }
}

@Composable
fun TechChip(name: String, version: String?) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.secondaryContainer)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            if (version != null) "$name v$version" else name,
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSecondaryContainer
        )
    }
}

@Composable
fun OsintTab(report: AnalysisReport?) {
    if (report == null) {
        EmptyState("Complete crawl to see OSINT data", Icons.Outlined.PersonSearch)
        return
    }
    
    val osint = report.osintSummary
    
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Summary Card
        osint?.counts?.let { counts ->
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text("OSINT Summary", fontWeight = FontWeight.Bold)
                        Spacer(Modifier.height(12.dp))
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                            OsintStatItem("Emails", counts.emails)
                            OsintStatItem("Phones", counts.phones)
                            OsintStatItem("Social", counts.socialPlatforms)
                            OsintStatItem("Names", counts.names)
                        }
                    }
                }
            }
        }
        
        // Emails Found
        osint?.uniqueEmails?.takeIf { it.isNotEmpty() }?.let { emails ->
            item {
                Text("Emails Found (${emails.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            items(emails.take(15)) { email ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF3B82F6).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Email, contentDescription = null, tint = Color(0xFF3B82F6), modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(email, fontSize = 14.sp)
                    }
                }
            }
        }
        
        // Phone Numbers
        osint?.uniquePhones?.takeIf { it.isNotEmpty() }?.let { phones ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Phone Numbers (${phones.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            items(phones.take(10)) { phone ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF10B981).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Phone, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(phone, fontSize = 14.sp)
                    }
                }
            }
        }
        
        // Social Media Presence
        osint?.socialPresence?.takeIf { it.isNotEmpty() }?.let { social ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Social Media Presence (${social.size} platforms)", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            social.forEach { (platform, links) ->
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF6366F1).copy(alpha = 0.1f)),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(platform.replaceFirstChar { it.uppercase() }, fontWeight = FontWeight.Bold, color = Color(0xFF6366F1))
                            links.take(3).forEach { link ->
                                Text(link, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            }
                            if (links.size > 3) {
                                Text("+${links.size - 3} more", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
            }
        }
        
        // Names/Employees Found
        osint?.uniqueNames?.takeIf { it.isNotEmpty() }?.let { names ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Names/Employees (${names.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            items(names.take(10)) { name ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFF59E0B).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Person, contentDescription = null, tint = Color(0xFFF59E0B), modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(name, fontSize = 14.sp)
                    }
                }
            }
        }
        
        // PII Findings
        osint?.piiFindings?.takeIf { it.isNotEmpty() }?.let { pii ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("PII Leaked (${pii.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold, color = Color(0xFFEF4444))
            }
            items(pii.take(10)) { finding ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(finding.severity)
                            Spacer(Modifier.width(8.dp))
                            Text(finding.description, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        Text("Value: ${finding.valueMasked}", fontSize = 12.sp)
                    }
                }
            }
        }
        
        // CT Log Subdomains
        osint?.ctSubdomains?.takeIf { it.isNotEmpty() }?.let { subs ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Certificate Transparency Subdomains (${subs.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            items(subs.take(15)) { sub ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(sub.subdomain, fontWeight = FontWeight.Medium, fontSize = 14.sp)
                        sub.issuer?.let {
                            Text("Issuer: $it", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
        
        // Wayback Machine URLs
        osint?.waybackUrls?.takeIf { it.isNotEmpty() }?.let { urls ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Wayback Machine History (${urls.size})", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            }
            items(urls.take(10)) { wayback ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(wayback.url, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("Archived: ${wayback.timestamp}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
        
        // Empty state if no OSINT data
        if (osint == null || (osint.uniqueEmails.isEmpty() && osint.uniquePhones.isEmpty() && osint.socialPresence.isEmpty())) {
            item {
                EmptyState("No OSINT data collected", Icons.Outlined.PersonSearch)
            }
        }
    }
}

@Composable
fun OsintStatItem(label: String, count: Int) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(count.toString(), fontWeight = FontWeight.Bold, fontSize = 20.sp)
        Text(label, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun StatusBadge(status: Int) {
    val (color, text) = when (status) {
        200 -> Pair(Color(0xFF10B981), "200")
        403 -> Pair(Color(0xFFF59E0B), "403")
        301, 302 -> Pair(Color(0xFF3B82F6), "$status")
        else -> Pair(Color.Gray, "$status")
    }
    
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.2f))
            .padding(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Text(text, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = color)
    }
}

@Composable
fun IssueCard(url: String, issue: String, color: Color) {
    Card(
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = color, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(issue, fontWeight = FontWeight.Medium, fontSize = 14.sp)
            }
            Text(
                url,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
fun PagesTab(report: AnalysisReport?) {
    if (report == null || report.allPages.isEmpty()) {
        EmptyState("No pages discovered yet", Icons.Outlined.Language)
        return
    }
    
    val context = LocalContext.current
    
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        item {
            Text(
                "${report.allPages.size} pages discovered",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(8.dp))
        }
        
        items(report.allPages) { page ->
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.clickable { openUrl(context, page.url) }
            ) {
                Row(
                    Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    StatusBadge(page.status ?: 0)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(
                            page.url,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            style = MaterialTheme.typography.bodyMedium
                        )
                        if (page.loadTime != null || page.size != null) {
                            Text(
                                "${page.loadTime ?: "-"}ms • ${formatFileSize(page.size)}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun MediaTab(files: SessionFiles?) {
    if (files == null || (files.images.isEmpty() && files.documents.isEmpty())) {
        EmptyState("No media files found", Icons.Outlined.Image)
        return
    }
    
    val context = LocalContext.current
    
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        if (files.images.isNotEmpty()) {
            item {
                Text("Images (${files.images.size})", fontWeight = FontWeight.Bold)
            }
            item {
                LazyVerticalGrid(
                    columns = GridCells.Adaptive(100.dp),
                    modifier = Modifier.height(220.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(files.images.take(6)) { file ->
                        Card(
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .aspectRatio(1f)
                                .clickable { openFile(context, file) }
                        ) {
                            Image(
                                painter = rememberAsyncImagePainter(file),
                                contentDescription = null,
                                modifier = Modifier.fillMaxSize(),
                                contentScale = ContentScale.Crop
                            )
                        }
                    }
                }
            }
        }
        
        if (files.documents.isNotEmpty()) {
            item {
                Text("Documents (${files.documents.size})", fontWeight = FontWeight.Bold)
            }
            items(files.documents) { file ->
                DocumentRow(file)
            }
        }
    }
}

@Composable
fun FilesTab(files: SessionFiles?) {
    if (files == null || files.totalFiles == 0) {
        EmptyState("No files extracted yet", Icons.Outlined.Folder)
        return
    }

    var searchQuery by remember { mutableStateOf("") }
    var selectedCategory by remember { mutableStateOf("All") }
    val categories = listOf("All", "Content", "HTML", "Styles", "Scripts")

    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                label = { Text("Search files") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )
            
            Spacer(Modifier.height(8.dp))
            
            ScrollableTabRow(
                selectedTabIndex = categories.indexOf(selectedCategory),
                containerColor = Color.Transparent,
                divider = {},
                edgePadding = 0.dp,
                indicator = { tabPositions ->
                    if (categories.indexOf(selectedCategory) < tabPositions.size) {
                        TabRowDefaults.Indicator(
                            Modifier.tabIndicatorOffset(tabPositions[categories.indexOf(selectedCategory)]),
                            height = 3.dp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            ) {
                categories.forEach { category ->
                    Tab(
                        selected = selectedCategory == category,
                        onClick = { selectedCategory = category },
                        text = { Text(category) }
                    )
                }
            }
        }
        
        // Filter Logic
        val allFiles = mutableListOf<Pair<String, List<File>>>()
        if (selectedCategory == "All" || selectedCategory == "Content") 
            allFiles.add("Content" to files.content)
        if (selectedCategory == "All" || selectedCategory == "HTML") 
            allFiles.add("HTML Source" to files.html)
        if (selectedCategory == "All" || selectedCategory == "Styles") 
            allFiles.add("Stylesheets" to files.stylesheets)
        if (selectedCategory == "All" || selectedCategory == "Scripts") 
            allFiles.add("Scripts" to files.scripts)

        allFiles.forEach { (header, list) ->
            val filteredList = if (searchQuery.isBlank()) list else list.filter { 
                it.name.contains(searchQuery, ignoreCase = true) 
            }
            
            if (filteredList.isNotEmpty()) {
                item { SectionHeader("$header (${filteredList.size})") }
                items(filteredList) { file -> 
                    FileRow(file, getFileIcon(header)) 
                }
            }
        }
    }
}

fun getFileIcon(category: String): ImageVector = when(category) {
    "Content" -> Icons.Default.Description
    "HTML Source" -> Icons.Default.Code
    "Stylesheets" -> Icons.Default.Style
    "Scripts" -> Icons.Default.Javascript
    else -> Icons.Default.InsertDriveFile
}

@Composable
fun SectionHeader(text: String) {
    Text(
        text,
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.primary,
        fontWeight = FontWeight.Bold
    )
}

@Composable
fun FileRow(file: File, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    val context = LocalContext.current
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.clickable { openFile(context, file) }
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.width(12.dp))
            Text(file.name, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
fun DocumentRow(file: File) {
    val context = LocalContext.current
    val ext = file.extension.lowercase()
    val color = when (ext) {
        "pdf" -> Color(0xFFE57373)
        "doc", "docx" -> Color(0xFF64B5F6)
        "xls", "xlsx" -> Color(0xFF81C784)
        else -> Color.Gray
    }
    
    Card(
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f)),
        shape = RoundedCornerShape(8.dp),
        modifier = Modifier.clickable { openFile(context, file) }
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(
                if (ext == "pdf") Icons.Default.PictureAsPdf else Icons.Default.InsertDriveFile,
                contentDescription = null,
                tint = color
            )
            Spacer(Modifier.width(12.dp))
            Text(file.name, fontWeight = FontWeight.Medium)
        }
    }
}

@Composable
fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun EmptyState(message: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
             Icon(icon, contentDescription = null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.surfaceVariant)
             Spacer(Modifier.height(16.dp))
             Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun formatDuration(start: Long, end: Long?): String {
    val endTime = end ?: System.currentTimeMillis()
    val diff = endTime - start
    val sec = diff / 1000
    val min = sec / 60
    return if (min > 0) "${min}m ${sec % 60}s" else "${sec}s"
}

private fun openUrl(context: android.content.Context, url: String) {
    try {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        context.startActivity(intent)
    } catch (e: Exception) {
        Toast.makeText(context, "Could not open link: ${e.message}", Toast.LENGTH_SHORT).show()
    }
}

private fun openFile(context: android.content.Context, file: File) {
    try {
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, getMimeType(file))
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Open file with"))
    } catch (e: Exception) {
        Toast.makeText(context, "No app found to open this file: ${e.message}", Toast.LENGTH_SHORT).show()
    }
}

private fun getMimeType(file: File): String {
    return when(file.extension.lowercase()) {
        "pdf" -> "application/pdf"
        "doc", "docx" -> "application/msword"
        "xls", "xlsx" -> "application/vnd.ms-excel"
        "ppt", "pptx" -> "application/vnd.ms-powerpoint"
        "jpg", "jpeg", "png", "webp" -> "image/*"
        "html", "htm" -> "text/html"
        "txt", "md", "csv" -> "text/plain"
        "json" -> "application/json"
        "js" -> "application/javascript"
        "css" -> "text/css"
        "xml" -> "text/xml"
        "zip", "rar", "7z" -> "application/zip"
        else -> "*/*"
    }
}

private fun handleExportResult(context: android.content.Context, jsonResult: String) {
    try {
        val jsonObject = org.json.JSONObject(jsonResult)
        if (jsonObject.has("success") && jsonObject.getBoolean("success")) {
            val path = jsonObject.getString("path")
            val file = File(path)
            if (file.exists()) {
                shareFile(context, file)
            } else {
                Toast.makeText(context, "Export failed: File not found", Toast.LENGTH_SHORT).show()
            }
        } else {
            val error = if(jsonObject.has("error")) jsonObject.getString("error") else "Unknown error"
            Toast.makeText(context, "Export failed: $error", Toast.LENGTH_LONG).show()
        }
    } catch (e: Exception) {
        Toast.makeText(context, "Error processing result: ${e.message}", Toast.LENGTH_SHORT).show()
    }
}

private fun shareFile(context: android.content.Context, file: File) {
    try {
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = getMimeType(file)
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Share Export"))
    } catch (e: Exception) {
        Toast.makeText(context, "Share failed: ${e.message}", Toast.LENGTH_SHORT).show()
    }
}
