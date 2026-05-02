package com.bitflow.finance.ui.screens.crawler

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.ui.text.font.FontFamily
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
        containerColor = Cyber.Bg,
        topBar = {
            session?.let { s ->
                val statusColor = getStatusColor(s.status)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(
                                    statusColor.copy(alpha = 0.15f),
                                    Cyber.Bg
                                )
                            )
                        )
                ) {
                    TopAppBar(
                        title = { 
                            Column {
                                Text(
                                    "SCAN_RESULTS",
                                    fontFamily = FontFamily.Monospace,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp,
                                    color = Cyber.TextPrimary
                                )
                                Text(
                                    s.startUrl
                                        .removePrefix("https://www.")
                                        .removePrefix("http://www.")
                                        .removePrefix("https://")
                                        .removePrefix("http://")
                                        .trimEnd('/'), 
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 11.sp,
                                    color = Cyber.TextSecondary,
                                    maxLines = 1
                                ) 
                            } 
                        },
                        navigationIcon = {
                            IconButton(onClick = { navController.popBackStack() }) {
                                Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = Cyber.TextPrimary)
                            }
                        },
                        actions = {
                            StatusChip(s.status, statusColor)
                            
                            var showMenu by remember { mutableStateOf(false) }
                            
                            IconButton(onClick = { showMenu = true }) {
                                Icon(Icons.Default.MoreVert, contentDescription = "More", tint = Cyber.TextSecondary)
                            }
                            
                            DropdownMenu(
                                expanded = showMenu,
                                onDismissRequest = { showMenu = false },
                                modifier = Modifier.background(Cyber.BgElevated)
                            ) {
                                DropdownMenuItem(
                                    text = { Text("Export PDF Report", color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 13.sp) },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.generatePdf(s.id) { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.PictureAsPdf, contentDescription = null, tint = Cyber.Red) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Export CSV", color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 13.sp) },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.exportData(s.id, "csv") { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.TableChart, contentDescription = null, tint = Cyber.Green) }
                                )
                                DropdownMenuItem(
                                    text = { Text("Export JSON", color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 13.sp) },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.exportData(s.id, "json") { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.DataObject, contentDescription = null, tint = Cyber.Blue) }
                                )
                                HorizontalDivider(color = Cyber.Border)
                                DropdownMenuItem(
                                    text = { Text("Generate Sitemap", color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 13.sp) },
                                    onClick = { 
                                        showMenu = false
                                        viewModel.generateSitemap(s.id) { result ->
                                            handleExportResult(context, result)
                                        }
                                    },
                                    leadingIcon = { Icon(Icons.Default.Map, contentDescription = null, tint = Cyber.Purple) }
                                )
                                HorizontalDivider(color = Cyber.Border)
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
                containerColor = Cyber.Bg,
                contentColor = Cyber.Green,
                edgePadding = 16.dp,
                indicator = { tabPositions ->
                    if (selectedTab < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            modifier = Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                            height = 2.dp,
                            color = Cyber.Green
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
                            Text(
                                title.uppercase(),
                                fontFamily = FontFamily.Monospace,
                                fontSize = 11.sp,
                                fontWeight = if(selected) FontWeight.Bold else FontWeight.Normal,
                                color = if(selected) Cyber.Green else Cyber.TextSecondary
                            )
                        }
                    )
                }
            }
            
            HorizontalDivider(color = Cyber.Border)

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
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(Cyber.BgCard)
                        .border(1.dp, Cyber.Cyan.copy(alpha = 0.4f), RoundedCornerShape(10.dp))
                ) {
                    Box(
                        modifier = Modifier
                            .width(3.dp)
                            .matchParentSize()
                            .background(Brush.verticalGradient(listOf(Cyber.Cyan, Cyber.Cyan.copy(alpha = 0.2f))))
                    )
                    Column(Modifier.padding(start = 16.dp, end = 16.dp, top = 14.dp, bottom = 14.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ScannerPulse(color = Cyber.Cyan, rings = false)
                            Spacer(Modifier.width(10.dp))
                            Text(
                                "SCANNING_IN_PROGRESS",
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                color = Cyber.Cyan
                            )
                        }
                        
                        Spacer(Modifier.height(12.dp))
                        
                        // Progress bar
                        val progress = if (session.pagesTotal > 0) {
                            session.pagesCrawled.toFloat() / session.pagesTotal
                        } else 0.1f
                        
                        LinearProgressIndicator(
                            progress = { progress.coerceIn(0f, 1f) },
                            modifier = Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp)),
                            color = Cyber.Cyan,
                            trackColor = Cyber.Border
                        )
                        
                        Spacer(Modifier.height(8.dp))
                        
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                "${session.pagesCrawled} crawled",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 11.sp,
                                color = Cyber.TextSecondary
                            )
                            Text(
                                "${session.pagesQueued} queued",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 11.sp,
                                color = Cyber.TextSecondary
                            )
                        }
                        
                        if (session.currentUrl.isNotBlank()) {
                            Spacer(Modifier.height(6.dp))
                            Text(
                                "> ${session.currentUrl}",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 10.sp,
                                color = Cyber.TextSecondary.copy(alpha = 0.6f),
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
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Cyber.Red.copy(alpha = 0.15f),
                            contentColor = Cyber.Red
                        ),
                        border = BorderStroke(1.dp, Cyber.Red.copy(alpha = 0.5f)),
                        elevation = ButtonDefaults.buttonElevation(0.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                         Icon(Icons.Default.Stop, contentDescription = null)
                         Spacer(Modifier.width(8.dp))
                         Text(
                             "TERMINATE_SCAN",
                             fontFamily = FontFamily.Monospace,
                             fontWeight = FontWeight.Bold,
                             fontSize = 12.sp
                         )
                    }
                }
            }
        }

        // Health Score Card
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(Cyber.BgCard)
                    .border(1.dp, Cyber.Border, RoundedCornerShape(12.dp))
            ) {
                Column(Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    
                    // Health Score Circle
                    val score = report?.healthScore ?: 0
                    val scoreColor = Cyber.gradeColor(report?.securityGrade ?: when {
                        score >= 80 -> "A"
                        score >= 65 -> "B"
                        score >= 50 -> "C"
                        score >= 35 -> "D"
                        else -> "F"
                    })
                    
                    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(140.dp)) {
                        Canvas(modifier = Modifier.size(120.dp)) {
                            val strokeWidth = 10.dp.toPx()
                            
                            // Background circle
                            drawCircle(
                                color = scoreColor.copy(alpha = 0.08f),
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
                                    modifier = Modifier.size(28.dp),
                                    strokeWidth = 2.dp,
                                    color = Cyber.Cyan
                                )
                            } else {
                                // Show grade letter if available, else score
                                val grade = report?.securityGrade
                                if (grade != null) {
                                    Text(
                                        grade,
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 48.sp,
                                        fontWeight = FontWeight.Black,
                                        color = scoreColor
                                    )
                                } else {
                                    Text(
                                        "$score",
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 40.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = scoreColor
                                    )
                                }
                            }
                            Text(
                                if (report?.securityGrade != null) "SECURITY" else "HEALTH",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                letterSpacing = 1.sp,
                                color = Cyber.TextSecondary
                            )
                        }
                    }
                    
                    if (report != null && score < 100) {
                        Spacer(Modifier.height(12.dp))
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Cyber.Red.copy(alpha = 0.05f), RoundedCornerShape(6.dp))
                                .border(1.dp, Cyber.Red.copy(alpha = 0.2f), RoundedCornerShape(6.dp))
                                .padding(10.dp)
                        ) {
                            Text(
                                "// SCORE_BREAKDOWN",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Cyber.TextSecondary
                            )
                            Spacer(Modifier.height(4.dp))
                            
                            if (report.seoIssues.isNotEmpty()) {
                                Text(
                                    "-${(report.seoIssues.size * 2).coerceAtMost(30)}pts :: ${report.seoIssues.size} SEO issues",
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 11.sp,
                                    color = Cyber.Yellow
                                )
                            }
                            if (report.securityIssues.isNotEmpty()) {
                                Text(
                                    "-${(report.securityIssues.size * 3).coerceAtMost(30)}pts :: ${report.securityIssues.size} SECURITY issues",
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 11.sp,
                                    color = Cyber.Red
                                )
                            }
                            if (report.ssl?.valid != true) {
                                Text(
                                    "-20pts :: SSL invalid/missing",
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 11.sp,
                                    color = Cyber.Red
                                )
                            }
                        }
                    }
                    
                    Spacer(Modifier.height(20.dp))
                    
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
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(Cyber.BgCard)
            .border(1.dp, color.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
    ) {
        // Left accent bar
        Box(
            modifier = Modifier
                .width(2.dp)
                .matchParentSize()
                .background(color.copy(alpha = 0.6f))
        )
        Row(
            Modifier.padding(start = 12.dp, end = 10.dp, top = 12.dp, bottom = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(10.dp))
            Column {
                Text(
                    value,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Black,
                    fontSize = 18.sp,
                    color = color
                )
                Text(
                    label.uppercase(),
                    fontFamily = FontFamily.Monospace,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp,
                    color = Cyber.TextSecondary
                )
                if (description != null) {
                    Text(
                        description, 
                        fontFamily = FontFamily.Monospace,
                        fontSize = 9.sp,
                        color = color.copy(alpha = 0.75f)
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
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.Green.copy(alpha = 0.06f))
                        .border(1.dp, Cyber.Green.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                        .padding(16.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Cyber.Green)
                        Spacer(Modifier.width(10.dp))
                        Text(
                            "// NO_SEO_ISSUES_DETECTED",
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Medium,
                            color = Cyber.Green
                        )
                    }
                }
            }
        } else {
            items(report.seoIssues) { issue ->
                IssueCard(url = issue.url, issue = issue.issue, color = Cyber.Yellow)
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
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Cyber.RedDim)
                        .border(1.dp, Cyber.BorderDanger, RoundedCornerShape(12.dp))
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Warning, null, tint = Cyber.Red, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "SCANNER ERROR",
                                fontWeight = FontWeight.Bold,
                                color = Cyber.Red,
                                fontFamily = FontFamily.Monospace,
                                fontSize = 13.sp
                            )
                        }
                        Spacer(Modifier.height(6.dp))
                        Text(
                            report.error,
                            fontSize = 12.sp,
                            color = Cyber.TextSecondary,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }

        // ============ SECURITY SUMMARY HEADER ============
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(Cyber.BgCard)
                    .border(1.dp, Cyber.Border, RoundedCornerShape(16.dp))
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Grade Circle
                    val grade = report.securityGrade ?: "?"
                    val score = report.healthScore
                    val gradeColor = when {
                        score >= 90 -> Cyber.Green
                        score >= 70 -> Cyber.Yellow
                        score >= 50 -> Cyber.Orange
                        else -> Cyber.Red
                    }

                    Box(
                        modifier = Modifier
                            .size(88.dp)
                            .clip(CircleShape)
                            .background(gradeColor.copy(alpha = 0.12f))
                            .border(2.dp, gradeColor.copy(alpha = 0.6f), CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            grade,
                            style = MaterialTheme.typography.displaySmall,
                            fontWeight = FontWeight.Black,
                            color = gradeColor,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Spacer(Modifier.height(8.dp))
                    Text("Security Score: $score/100", fontWeight = FontWeight.Bold, color = Cyber.TextPrimary)
                    
                    Spacer(Modifier.height(16.dp))
                    
                    // Quick stats row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        MiniStat(
                            value = "${report.criticalVulnerabilities}",
                            label = "Critical",
                            color = if (report.criticalVulnerabilities > 0) Cyber.Red else Cyber.Green
                        )
                        MiniStat(
                            value = "${report.highVulnerabilities}",
                            label = "High",
                            color = if (report.highVulnerabilities > 0) Cyber.Orange else Cyber.Green
                        )
                        MiniStat(
                            value = "${report.secretsFound.size}",
                            label = "Secrets",
                            color = if (report.secretsFound.isNotEmpty()) Cyber.Red else Cyber.Green
                        )
                        MiniStat(
                            value = if (report.ssl?.valid == true) "✓" else "✗",
                            label = "SSL",
                            color = if (report.ssl?.valid == true) Cyber.Green else Cyber.Red
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
                    Text("Detailed Analysis", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
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
                        Text("Missing Headers:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Red)
                        Spacer(Modifier.height(4.dp))
                        headers.missingHeaders.forEach { h ->
                            Text("• ${h.displayName}", fontSize = 12.sp, color = Cyber.TextPrimary)
                        }
                    }
                    if (headers.presentHeaders.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Present Headers:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Green)
                        Spacer(Modifier.height(4.dp))
                        headers.presentHeaders.take(5).forEach { h ->
                            Text("✓ ${h.displayName}", fontSize = 12.sp, color = Cyber.Green)
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
                        Text("MX Records:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
                        it.take(3).forEach { mx ->
                            Text("• ${mx.host} (priority: ${mx.priority})", fontSize = 12.sp, color = Cyber.TextPrimary)
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
                        Text("Discovered:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
                        subEnum.subdomains.take(10).forEach { sub ->
                            val status = if (sub.live) "🟢" else "🔴"
                            Text("$status ${sub.subdomain}", fontSize = 12.sp, color = Cyber.TextPrimary)
                        }
                    }
                } ?: run {
                    report.subdomains.take(10).forEach { sub ->
                        Text("• ${sub.url}", fontSize = 12.sp, color = Cyber.TextPrimary)
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
                        Text("Swagger/OpenAPI:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Green)
                        api.swaggerSpecs.take(3).forEach { spec ->
                            Text("• ${spec.title.ifEmpty { spec.url }}", fontSize = 12.sp, color = Cyber.TextPrimary)
                        }
                    }
                    if (api.graphqlEndpoints.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("GraphQL Endpoints:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Purple)
                        api.graphqlEndpoints.take(3).forEach { ep ->
                            Text("• ${ep.url}", fontSize = 12.sp, color = Cyber.Cyan)
                        }
                    }
                    if (api.restEndpoints.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("REST Endpoints:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Blue)
                        api.restEndpoints.take(5).forEach { ep ->
                            Text("• ${ep.method} ${ep.path}", fontSize = 12.sp, color = Cyber.TextPrimary)
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
                        Text("⚠️ Reflected Parameters (XSS Risk):", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Red)
                        params.reflectedParams.take(5).forEach { p ->
                            Text("• ${p.name}", fontSize = 12.sp, color = Cyber.Red)
                        }
                    }
                    if (params.discoveredParams.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Discovered Parameters:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
                        params.discoveredParams.take(10).forEach { p ->
                            Text("• ${p.name} (${p.method})", fontSize = 12.sp, color = Cyber.TextPrimary)
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
                        Text("Login Pages:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
                        auth.loginPages.take(5).forEach { page ->
                            Text("• ${page.url}", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, color = Cyber.TextPrimary)
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
                        Text("⚠️ Exposed Buckets:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Red)
                        cloud.exposedBuckets.take(5).forEach { bucket ->
                            Text("• ${bucket.url}", fontSize = 12.sp, color = Cyber.Red, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                    if (cloud.bucketsFound.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Detected Buckets:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.TextPrimary)
                        cloud.bucketsFound.take(5).forEach { bucket ->
                            Text("• ${bucket.name} (${bucket.provider})", fontSize = 12.sp, color = Cyber.TextPrimary)
                        }
                    }
                }
            }
        }
        
        // ============ PRO SECURITY MODULES ============

        // 10. Open Redirect Testing
        item {
            val hasData = report.redirectTesting != null
            val vulnCount = report.redirectTesting?.vulnerableCount ?: 0
            FeatureSection(
                title = "↗️ Open Redirect Testing",
                subtitle = when {
                    vulnCount > 0 -> "⚠️ $vulnCount vulnerable endpoints"
                    hasData -> "✓ No open redirects found"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "redirects",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "redirects") null else "redirects" }
            ) {
                report.redirectTesting?.let { rt ->
                    DetailRow("Params Tested", "${rt.testedParams}")
                    DetailRow("Vulnerable", "${rt.vulnerableCount}")
                    if (rt.findings.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Vulnerable Endpoints:", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = Cyber.Red)
                        rt.findings.take(5).forEach { f ->
                            Text("• [${f.method}] ${f.url}", fontSize = 12.sp, color = Cyber.Orange,
                                maxLines = 1, overflow = TextOverflow.Ellipsis, fontFamily = FontFamily.Monospace)
                            Text("  → ${f.redirectTo}", fontSize = 11.sp, color = Cyber.Red,
                                maxLines = 1, overflow = TextOverflow.Ellipsis, fontFamily = FontFamily.Monospace)
                        }
                    }
                    rt.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 11. Header Injection
        item {
            val totalIssues = report.headerInjection?.totalIssues ?: 0
            val hasData = report.headerInjection != null
            FeatureSection(
                title = "💉 Header Injection (CRLF)",
                subtitle = when {
                    totalIssues > 0 -> "⚠️ $totalIssues injection vulnerabilities"
                    hasData -> "✓ No injection vulnerabilities"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "headerinject",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "headerinject") null else "headerinject" }
            ) {
                report.headerInjection?.let { hi ->
                    DetailRow("CRLF Findings", "${hi.crlfFindings.size}")
                    DetailRow("Host Header Findings", "${hi.hostHeaderFindings.size}")
                    hi.crlfFindings.take(3).forEach { f ->
                        Spacer(Modifier.height(4.dp))
                        Text("CRLF: ${f.url}", fontSize = 12.sp, color = Cyber.Orange,
                            maxLines = 1, overflow = TextOverflow.Ellipsis, fontFamily = FontFamily.Monospace)
                    }
                    hi.hostHeaderFindings.take(3).forEach { f ->
                        Text("Host: ${f.injectedHost}", fontSize = 12.sp, color = Cyber.Yellow, fontFamily = FontFamily.Monospace)
                    }
                    hi.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 12. JWT Token Analysis
        item {
            val jwtCount = report.jwtAnalysis?.uniqueTokensAnalyzed ?: 0
            val vulnTokens = report.jwtAnalysis?.vulnerableTokens ?: 0
            val hasData = report.jwtAnalysis != null && jwtCount > 0
            FeatureSection(
                title = "🎫 JWT Token Analysis",
                subtitle = when {
                    vulnTokens > 0 -> "⚠️ $jwtCount tokens, $vulnTokens vulnerable"
                    hasData -> "✓ $jwtCount tokens found (secure)"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "jwt",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "jwt") null else "jwt" }
            ) {
                report.jwtAnalysis?.let { ja ->
                    DetailRow("Tokens Analyzed", "${ja.uniqueTokensAnalyzed}")
                    DetailRow("Vulnerable", "${ja.vulnerableTokens}")
                    if (ja.critical > 0) DetailRow("Critical Issues", "${ja.critical}")
                    if (ja.high > 0) DetailRow("High Issues", "${ja.high}")
                    ja.findings.take(3).forEach { finding ->
                        if (finding.issues.isNotEmpty()) {
                            Spacer(Modifier.height(6.dp))
                            Text("alg:${finding.algorithm}", fontSize = 11.sp, color = Cyber.Cyan,
                                fontFamily = FontFamily.Monospace)
                            finding.issues.take(2).forEach { issue ->
                                Text("  ⚠ ${issue.issue}", fontSize = 12.sp,
                                    color = Cyber.severityColor(issue.severity))
                            }
                        }
                    }
                    ja.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 13. GraphQL Security
        item {
            val endpointCount = report.graphqlTesting?.endpointsTested?.size ?: 0
            val vulnCount = report.graphqlTesting?.vulnerableCount ?: 0
            val hasData = report.graphqlTesting != null && endpointCount > 0
            FeatureSection(
                title = "🔮 GraphQL Security",
                subtitle = when {
                    vulnCount > 0 -> "⚠️ $vulnCount vulnerabilities in $endpointCount endpoints"
                    hasData -> "✓ $endpointCount endpoints tested"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "graphql",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "graphql") null else "graphql" }
            ) {
                report.graphqlTesting?.let { gql ->
                    DetailRow("Endpoints Tested", "${gql.endpointsTested.size}")
                    DetailRow("Vulnerable", "${gql.vulnerableCount}")
                    gql.endpointsTested.take(3).forEach { ep ->
                        Spacer(Modifier.height(4.dp))
                        val epColor = if (ep.introspectionEnabled) Cyber.Red else Cyber.Green
                        Text(
                            "${if (ep.introspectionEnabled) "⚠️" else "✓"} ${ep.url}",
                            fontSize = 12.sp, color = epColor, maxLines = 1,
                            overflow = TextOverflow.Ellipsis, fontFamily = FontFamily.Monospace
                        )
                        if (ep.introspectionEnabled) {
                            Text("  Introspection enabled (${ep.typeCount} types)", fontSize = 11.sp, color = Cyber.Orange)
                        }
                    }
                    gql.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 14. Information Disclosure
        item {
            val totalIssues = report.infoDisclosure?.totalIssues ?: 0
            val hasData = report.infoDisclosure != null
            FeatureSection(
                title = "📁 Information Disclosure",
                subtitle = when {
                    totalIssues > 0 -> "⚠️ $totalIssues sensitive files exposed"
                    hasData -> "✓ No sensitive files found"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "infodisclosure",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "infodisclosure") null else "infodisclosure" }
            ) {
                report.infoDisclosure?.let { id ->
                    DetailRow("Total Issues", "${id.totalIssues}")
                    if (id.critical > 0) DetailRow("Critical", "${id.critical}")
                    if (id.high > 0) DetailRow("High", "${id.high}")
                    id.securityTxt?.let {
                        Spacer(Modifier.height(4.dp))
                        Text("✓ security.txt present", fontSize = 12.sp, color = Cyber.Green)
                    }
                    id.findings.take(5).forEach { f ->
                        Spacer(Modifier.height(4.dp))
                        val fc = Cyber.severityColor(f.severity)
                        Text("${f.path} (${f.statusCode})", fontSize = 12.sp, color = fc,
                            fontFamily = FontFamily.Monospace, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(f.description, fontSize = 11.sp, color = Cyber.TextSecondary, maxLines = 1)
                    }
                    id.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 15. SQL Injection Detection
        item {
            val activeHits = report.sqliDetection?.activeHits ?: 0
            val passiveHits = report.sqliDetection?.passiveHits ?: 0
            val hasData = report.sqliDetection != null
            FeatureSection(
                title = "🗄️ SQL Injection",
                subtitle = when {
                    activeHits > 0 -> "🚨 $activeHits active SQLi confirmed"
                    passiveHits > 0 -> "⚠️ $passiveHits error patterns detected"
                    hasData -> "✓ No SQL injection detected"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "sqli",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "sqli") null else "sqli" }
            ) {
                report.sqliDetection?.let { sql ->
                    DetailRow("Params Tested", "${sql.paramsTested}")
                    DetailRow("Passive Hits", "${sql.passiveHits}")
                    DetailRow("Active Hits", "${sql.activeHits}")
                    if (sql.critical > 0) DetailRow("Critical", "${sql.critical}")
                    sql.findings.take(5).forEach { f ->
                        Spacer(Modifier.height(4.dp))
                        val fc = Cyber.severityColor(f.severity)
                        Text("[${f.method}] ${f.url}", fontSize = 12.sp, color = fc,
                            fontFamily = FontFamily.Monospace, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("${f.type}: ${f.payloadDescription}", fontSize = 11.sp, color = Cyber.TextSecondary)
                    }
                    sql.summary.takeIf { it.isNotEmpty() }?.let {
                        Spacer(Modifier.height(4.dp))
                        Text(it, fontSize = 12.sp, color = Cyber.TextSecondary)
                    }
                }
            }
        }

        // 16. Rate Limit Audit
        item {
            val unprotected = report.rateLimitCheck?.endpointsUnprotected ?: 0
            val protected = report.rateLimitCheck?.endpointsProtected ?: 0
            val hasData = report.rateLimitCheck != null
            FeatureSection(
                title = "⏱️ Rate Limit Audit",
                subtitle = when {
                    unprotected > 0 -> "⚠️ $unprotected endpoints unprotected"
                    hasData -> "✓ $protected endpoints protected"
                    else -> "Not scanned"
                },
                expanded = expandedSection == "ratelimit",
                hasData = hasData,
                onClick = { expandedSection = if (expandedSection == "ratelimit") null else "ratelimit" }
            ) {
                report.rateLimitCheck?.let { rl ->
                    DetailRow("Endpoints Tested", "${rl.endpointsTested.size}")
                    DetailRow("Protected", "${rl.endpointsProtected}")
                    DetailRow("Unprotected", "${rl.endpointsUnprotected}")
                    rl.endpointsTested.take(5).forEach { ep ->
                        Spacer(Modifier.height(4.dp))
                        val epColor = if (ep.rateLimited) Cyber.Green else Cyber.Red
                        Text(
                            "${if (ep.rateLimited) "✓" else "✗"} ${ep.method} ${ep.url}",
                            fontSize = 12.sp, color = epColor, maxLines = 1,
                            overflow = TextOverflow.Ellipsis, fontFamily = FontFamily.Monospace
                        )
                        if (!ep.rateLimited) {
                            Text("  No rate limiting detected", fontSize = 11.sp, color = Cyber.Orange)
                        }
                    }
                    rl.findings.take(3).forEach { f ->
                        Spacer(Modifier.height(4.dp))
                        Text("⚠ ${f.description}", fontSize = 12.sp, color = Cyber.Yellow)
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
                    fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary
                )
            }
            items(report.vulnerabilities.take(10)) { vuln ->
                val severityColor = Cyber.severityColor(vuln.severity)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.severityDim(vuln.severity))
                        .border(1.dp, severityColor.copy(alpha = 0.4f), RoundedCornerShape(8.dp))
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(vuln.severity)
                            Spacer(Modifier.width(8.dp))
                            Text(vuln.type, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Cyber.TextPrimary)
                        }
                        vuln.cve?.let { cve ->
                            Text(cve, style = MaterialTheme.typography.bodySmall, color = severityColor, fontFamily = FontFamily.Monospace)
                        }
                        vuln.description?.let { desc ->
                            Text(desc, style = MaterialTheme.typography.bodySmall, maxLines = 2, color = Cyber.TextSecondary)
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
                    color = Cyber.Red
                )
            }
            items(report.secretsFound.take(10)) { secret ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.RedDim)
                        .border(1.dp, Cyber.BorderDanger, RoundedCornerShape(8.dp))
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(secret.type, fontWeight = FontWeight.Bold, color = Cyber.Red, fontFamily = FontFamily.Monospace)
                        Text("File: ${secret.file}", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis, color = Cyber.TextSecondary)
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
                    fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary
                )
            }
            items(report.hiddenPaths.take(15)) { path ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.PurpleDim)
                        .border(1.dp, Cyber.Purple.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        StatusBadge(path.status)
                        Spacer(Modifier.width(12.dp))
                        Text(path.path, fontWeight = FontWeight.Medium, fontSize = 13.sp, color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace)
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
                    fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary
                )
            }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    report.technologies.take(10).forEach { tech ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("•", color = Cyber.Purple)
                            Spacer(Modifier.width(8.dp))
                            Text(tech.name, fontWeight = FontWeight.Medium, color = Cyber.TextPrimary)
                            tech.version?.let {
                                Spacer(Modifier.width(4.dp))
                                Text("v$it", fontSize = 12.sp, color = Cyber.TextSecondary, fontFamily = FontFamily.Monospace)
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
        Text(value, fontWeight = FontWeight.Black, fontSize = 18.sp, color = color, fontFamily = FontFamily.Monospace)
        Text(label, fontSize = 11.sp, color = Cyber.TextSecondary)
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
    val borderColor = if (hasData) Cyber.BorderActive else Cyber.Border
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Cyber.BgCard)
            .border(1.dp, borderColor, RoundedCornerShape(12.dp))
            .clickable(enabled = hasData, onClick = onClick)
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
                    Text(title, fontWeight = FontWeight.Bold, fontSize = 15.sp, color = Cyber.TextPrimary)
                    Text(
                        subtitle,
                        fontSize = 12.sp,
                        color = if (hasData) Cyber.Cyan else Cyber.TextSecondary
                    )
                }
                if (hasData) {
                    Icon(
                        if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = null,
                        tint = Cyber.TextSecondary
                    )
                } else {
                    Text(
                        "N/A",
                        fontSize = 12.sp,
                        color = Cyber.TextMuted
                    )
                }
            }

            AnimatedVisibility(visible = expanded && hasData) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 16.dp, end = 16.dp, bottom = 16.dp)
                ) {
                    HorizontalDivider(color = Cyber.Border, modifier = Modifier.padding(bottom = 12.dp))
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
        Text(label, fontSize = 13.sp, color = Cyber.TextSecondary)
        Text(value, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = Cyber.TextPrimary)
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
        weight >= 20 -> Cyber.Red
        weight >= 10 -> Cyber.Yellow
        else -> Cyber.TextSecondary
    }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(severity.copy(alpha = 0.08f))
            .border(1.dp, severity.copy(alpha = 0.4f), RoundedCornerShape(8.dp))
            .padding(vertical = 2.dp)
    ) {
        Row(Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("✗", color = severity, fontFamily = FontFamily.Monospace)
            Spacer(Modifier.width(8.dp))
            Text(name, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = Cyber.TextPrimary)
        }
    }
}

@Composable
fun SubdomainChip(subdomain: String, live: Boolean, riskLevel: String) {
    val color = when(riskLevel.lowercase()) {
        "high" -> Cyber.Red
        "medium" -> Cyber.Yellow
        else -> if (live) Cyber.Green else Cyber.TextSecondary
    }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(color.copy(alpha = 0.08f))
            .border(1.dp, color.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
            .padding(vertical = 2.dp)
    ) {
        Row(Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .background(if (live) Cyber.Green else Cyber.TextSecondary, CircleShape)
            )
            Spacer(Modifier.width(8.dp))
            Text(subdomain, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace)
        }
    }
}

@Composable
fun ExposedBucketCard(bucket: com.bitflow.finance.domain.crawler.ExposedBucket) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(Cyber.RedDim)
            .border(1.dp, Cyber.BorderDanger, RoundedCornerShape(8.dp))
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = Cyber.Red, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(bucket.name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Cyber.TextPrimary,
                    fontFamily = FontFamily.Monospace)
            }
            Text("Provider: ${bucket.provider}", style = MaterialTheme.typography.bodySmall, color = Cyber.TextSecondary)
            if (bucket.listingEnabled) {
                Text("⚠️ Directory listing enabled!", style = MaterialTheme.typography.bodySmall, color = Cyber.Red)
            }
        }
    }
}

fun getGradeColor(grade: String): Color {
    return when(grade.uppercase()) {
        "A", "A+" -> Cyber.Green
        "B" -> Cyber.Green.copy(alpha = 0.7f)
        "C" -> Cyber.Yellow
        "D" -> Cyber.Orange
        "E", "F" -> Cyber.Red
        else -> Cyber.TextSecondary
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
    val color = Cyber.severityColor(severity)
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.2f))
            .border(1.dp, color.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(severity.uppercase(), fontSize = 10.sp, fontWeight = FontWeight.Bold, color = color, fontFamily = FontFamily.Monospace)
    }
}

@Composable
fun TechChip(name: String, version: String?) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Cyber.BgElevated)
            .border(1.dp, Cyber.Border, RoundedCornerShape(16.dp))
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            if (version != null) "$name v$version" else name,
            fontSize = 12.sp,
            color = Cyber.TextPrimary,
            fontFamily = FontFamily.Monospace
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
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Cyber.BgCard)
                        .border(1.dp, Cyber.Border, RoundedCornerShape(12.dp))
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text("OSINT Summary", fontWeight = FontWeight.Bold, color = Cyber.Cyan,
                            fontFamily = FontFamily.Monospace)
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
                Text("Emails Found (${emails.size})", style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = Cyber.TextPrimary)
            }
            items(emails.take(15)) { email ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.BlueDim)
                        .border(1.dp, Cyber.Blue.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Email, contentDescription = null, tint = Cyber.Blue, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(email, fontSize = 14.sp, color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
        
        // Phone Numbers
        osint?.uniquePhones?.takeIf { it.isNotEmpty() }?.let { phones ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Phone Numbers (${phones.size})", style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = Cyber.TextPrimary)
            }
            items(phones.take(10)) { phone ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.GreenDim)
                        .border(1.dp, Cyber.Green.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Phone, contentDescription = null, tint = Cyber.Green, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(phone, fontSize = 14.sp, color = Cyber.TextPrimary, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
        
        // Social Media Presence
        osint?.socialPresence?.takeIf { it.isNotEmpty() }?.let { social ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Social Media Presence (${social.size} platforms)", style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = Cyber.TextPrimary)
            }
            social.forEach { (platform, links) ->
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(Cyber.PurpleDim)
                            .border(1.dp, Cyber.Purple.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(platform.replaceFirstChar { it.uppercase() }, fontWeight = FontWeight.Bold,
                                color = Cyber.Purple)
                            links.take(3).forEach { link ->
                                Text(link, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                                    color = Cyber.TextSecondary, fontFamily = FontFamily.Monospace)
                            }
                            if (links.size > 3) {
                                Text("+${links.size - 3} more", fontSize = 12.sp, color = Cyber.TextMuted)
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
                Text("Names/Employees (${names.size})", style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = Cyber.TextPrimary)
            }
            items(names.take(10)) { name ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.YellowDim)
                        .border(1.dp, Cyber.Yellow.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Person, contentDescription = null, tint = Cyber.Yellow, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(name, fontSize = 14.sp, color = Cyber.TextPrimary)
                    }
                }
            }
        }
        
        // PII Findings
        osint?.piiFindings?.takeIf { it.isNotEmpty() }?.let { pii ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("PII Leaked (${pii.size})", style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold, color = Cyber.Red)
            }
            items(pii.take(10)) { finding ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.RedDim)
                        .border(1.dp, Cyber.BorderDanger, RoundedCornerShape(8.dp))
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(finding.severity)
                            Spacer(Modifier.width(8.dp))
                            Text(finding.description, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Cyber.TextPrimary)
                        }
                        Text("Value: ${finding.valueMasked}", fontSize = 12.sp, color = Cyber.TextSecondary, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
        
        // CT Log Subdomains
        osint?.ctSubdomains?.takeIf { it.isNotEmpty() }?.let { subs ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Certificate Transparency Subdomains (${subs.size})",
                    style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary)
            }
            items(subs.take(15)) { sub ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.BgElevated)
                        .border(1.dp, Cyber.Border, RoundedCornerShape(8.dp))
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(sub.subdomain, fontWeight = FontWeight.Medium, fontSize = 14.sp,
                            color = Cyber.Cyan, fontFamily = FontFamily.Monospace)
                        sub.issuer?.let {
                            Text("Issuer: $it", fontSize = 12.sp, color = Cyber.TextSecondary)
                        }
                    }
                }
            }
        }
        
        // Wayback Machine URLs
        osint?.waybackUrls?.takeIf { it.isNotEmpty() }?.let { urls ->
            item {
                Spacer(Modifier.height(8.dp))
                Text("Wayback Machine History (${urls.size})",
                    style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold,
                    color = Cyber.TextPrimary)
            }
            items(urls.take(10)) { wayback ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Cyber.BgElevated)
                        .border(1.dp, Cyber.Border, RoundedCornerShape(8.dp))
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(wayback.url, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                            color = Cyber.Cyan, fontFamily = FontFamily.Monospace)
                        Text("Archived: ${wayback.timestamp}", fontSize = 12.sp, color = Cyber.TextSecondary)
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
        Text(count.toString(), fontWeight = FontWeight.Bold, fontSize = 20.sp, color = Cyber.Cyan,
            fontFamily = FontFamily.Monospace)
        Text(label, fontSize = 12.sp, color = Cyber.TextSecondary)
    }
}

@Composable
fun StatusBadge(status: Int) {
    val (color, text) = when (status) {
        200 -> Pair(Cyber.Green, "200")
        403 -> Pair(Cyber.Yellow, "403")
        301, 302 -> Pair(Cyber.Blue, "$status")
        else -> Pair(Cyber.TextSecondary, "$status")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(color.copy(alpha = 0.15f))
            .border(1.dp, color.copy(alpha = 0.5f), RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Text(text, fontSize = 12.sp, fontWeight = FontWeight.Bold, color = color,
            fontFamily = FontFamily.Monospace)
    }
}

@Composable
fun IssueCard(url: String, issue: String, color: Color) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(6.dp))
            .background(Cyber.BgCard)
            .border(1.dp, color.copy(alpha = 0.3f), RoundedCornerShape(6.dp))
    ) {
        Box(
            modifier = Modifier
                .width(2.dp)
                .matchParentSize()
                .background(color.copy(alpha = 0.5f))
        )
        Column(Modifier.padding(start = 10.dp, end = 10.dp, top = 10.dp, bottom = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = color, modifier = Modifier.size(14.dp))
                Spacer(Modifier.width(6.dp))
                Text(
                    issue,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Medium,
                    fontSize = 12.sp,
                    color = Cyber.TextPrimary
                )
            }
            Text(
                url,
                fontFamily = FontFamily.Monospace,
                fontSize = 10.sp,
                color = Cyber.TextSecondary,
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
        Text(
            value,
            fontFamily = FontFamily.Monospace,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Cyber.TextPrimary
        )
        Text(
            label.uppercase(),
            fontFamily = FontFamily.Monospace,
            fontSize = 9.sp,
            letterSpacing = 1.sp,
            color = Cyber.TextSecondary
        )
    }
}

@Composable
fun EmptyState(message: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
             Icon(icon, contentDescription = null, modifier = Modifier.size(40.dp), tint = Cyber.Border)
             Spacer(Modifier.height(12.dp))
             Text(
                 "// ${message.lowercase().replace(" ", "_")}",
                 fontFamily = FontFamily.Monospace,
                 fontSize = 12.sp,
                 color = Cyber.TextSecondary
             )
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
