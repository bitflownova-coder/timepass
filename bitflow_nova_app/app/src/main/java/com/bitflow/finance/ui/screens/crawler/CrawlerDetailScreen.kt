package com.bitflow.finance.ui.screens.crawler

import android.content.Intent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Image
import androidx.compose.material.icons.filled.InsertDriveFile
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.outlined.Description
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.outlined.Image
import androidx.compose.material.icons.outlined.InsertDriveFile
import androidx.compose.material3.*
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import androidx.navigation.NavController
import coil.compose.rememberAsyncImagePainter
import java.io.File
import com.bitflow.finance.data.local.entity.CrawlSessionEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CrawlerDetailScreen(
    viewModel: CrawlerViewModel,
    navController: NavController,
    sessionId: Long
) {
    val session by viewModel.getSession(sessionId).collectAsState(initial = null)
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Content", "Images", "Documents")
    
    val context = LocalContext.current
    
    // Resolve files
    var files by remember { mutableStateOf(SessionFiles(emptyList(), emptyList(), emptyList())) }
    
    LaunchedEffect(session) {
        session?.let {
            // Fetch from API via ViewModel/Repo
            // We need to expose a suspend function in ViewModel
             val report = viewModel.getReport(it.id)
             if (report != null) {
                 files = report
             }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text(
                            "Crawl Report",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                        session?.let { 
                            Text(
                                it.startUrl, 
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            ) 
                        }
                    } 
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    session?.let { s ->
                        StatusBadge(s.status)
                        Spacer(Modifier.width(8.dp))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Column(modifier = Modifier
            .padding(padding)
            .fillMaxSize()) {
            
            // Stats Header
            session?.let { s ->
                 // Controls
                 if (s.status == "RUNNING" || s.status == "PAUSED") {
                     Row(
                         modifier = Modifier
                             .fillMaxWidth()
                             .padding(horizontal = 16.dp, vertical = 8.dp),
                         horizontalArrangement = Arrangement.spacedBy(12.dp)
                     ) {
                        val isPaused = s.status == "PAUSED"
                        Button(
                            onClick = { 
                                if (isPaused) viewModel.resumeCrawl(s.id) else viewModel.pauseCrawl(s.id) 
                            },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isPaused) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary
                            ),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                             Icon(if (isPaused) Icons.Default.PlayArrow else Icons.Default.Pause, contentDescription = null)
                             Spacer(Modifier.width(8.dp))
                             Text(if (isPaused) "Resume" else "Pause")
                        }
                         
                        Button(
                            onClick = { viewModel.stopCrawl(s.id) },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                             Icon(Icons.Default.Stop, contentDescription = null)
                             Spacer(Modifier.width(8.dp))
                             Text("Stop")
                        }
                     }
                 }
            }

            // Stats Grid
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                StatCard("Pages", files.content.size.toString(), Modifier.weight(1f), MaterialTheme.colorScheme.primaryContainer)
                StatCard("Images", files.images.size.toString(), Modifier.weight(1f), MaterialTheme.colorScheme.secondaryContainer)
                StatCard("Docs", files.documents.size.toString(), Modifier.weight(1f), MaterialTheme.colorScheme.tertiaryContainer)
            }
            
            Spacer(Modifier.height(8.dp))
            
            TabRow(
                selectedTabIndex = selectedTab,
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.primary,
                indicator = { tabPositions ->
                    TabRowDefaults.Indicator(
                        modifier = Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                        height = 3.dp,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            ) {
                tabs.forEachIndexed { index, title ->
                    val selected = selectedTab == index
                    Tab(
                        selected = selected,
                        onClick = { selectedTab = index },
                        text = { 
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    when(index) {
                                        0 -> if(selected) Icons.Default.Description else Icons.Outlined.Description
                                        1 -> if(selected) Icons.Default.Image else Icons.Outlined.Image
                                        else -> if(selected) Icons.Default.InsertDriveFile else Icons.Outlined.InsertDriveFile
                                    },
                                    contentDescription = null,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(Modifier.width(8.dp))
                                Text(title, fontWeight = if(selected) FontWeight.Bold else FontWeight.Normal)
                            }
                        }
                    )
                }
            }
            
            Surface(modifier = Modifier.weight(1f), color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha=0.3f)) {
                // Pass sessionId to lists for construction of Download URLs
                 val remoteId = session?.remoteId
                 
                 when (selectedTab) {
                    0 -> ContentList(files.content, remoteId)
                    1 -> ImagesGrid(files.images, remoteId)
                    2 -> DocumentList(files.documents, remoteId)
                }
            }
        }
    }
}

@Composable
fun StatCard(label: String, value: String, modifier: Modifier = Modifier, color: Color) {
    Card(
        modifier = modifier, 
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha=0.5f)),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(0.dp)
    ) {
        Column(
            Modifier.padding(vertical = 12.dp, horizontal = 4.dp), 
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label.uppercase(), style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface.copy(alpha=0.7f))
            Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun ContentList(files: List<File>, remoteId: String?) {
    val context = LocalContext.current
    if(files.isEmpty()) EmptyState("No Markdown content found")
    else
        LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(files) { file ->
                Card(
                    modifier = Modifier.fillMaxWidth().clickable { 
                        // Download and View Logic
                        // For now, show Toast as placeholder or implement download util
                         android.widget.Toast.makeText(context, "Viewing remote file: ${file.name}", android.widget.Toast.LENGTH_SHORT).show()
                    },
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(1.dp)
                ) {
                    Row(
                        Modifier.padding(16.dp), 
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(RoundedCornerShape(8.dp))
                                .background(MaterialTheme.colorScheme.primaryContainer),
                            contentAlignment = Alignment.Center
                        ) {
                             Icon(Icons.Default.Description, contentDescription = null, tint = MaterialTheme.colorScheme.onPrimaryContainer)
                        }
                        
                        Spacer(Modifier.width(16.dp))
                        
                        Column(Modifier.weight(1f)) {
                            Text(file.name.removeSuffix(".md"), fontWeight = FontWeight.SemiBold, maxLines = 1)
                        }
                        
                        IconButton(onClick = { /* ViewerUtils.shareFile(context, file) */ android.widget.Toast.makeText(context, "Sharing remote file: ${file.name}", android.widget.Toast.LENGTH_SHORT).show() }) {
                            Icon(Icons.Default.Share, contentDescription = "Share", tint = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
        }
}

@Composable
fun ImagesGrid(files: List<File>, remoteId: String?) {
    val context = LocalContext.current
    if (files.isEmpty()) {
        EmptyState("No images captured")
    } else {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(minSize = 100.dp),
            contentPadding = PaddingValues(8.dp),
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(files) { file ->
                Card(
                     shape = RoundedCornerShape(8.dp),
                     elevation = CardDefaults.cardElevation(2.dp),
                     modifier = Modifier.clickable { /* Download and View Logic */ android.widget.Toast.makeText(context, "Viewing remote image: ${file.name}", android.widget.Toast.LENGTH_SHORT).show() }
                ) {
                    Box {
                        // Coil URL
                        val imageUrl = if (remoteId != null) "http://10.0.2.2:5000/download/$remoteId/image/${file.name}" else null
                        Image(
                            painter = rememberAsyncImagePainter(
                                model = imageUrl ?: file, // Fallback to file if no remote ID (shouldn't happen)
                                contentScale = ContentScale.Crop
                            ),
                            contentDescription = null,
                            modifier = Modifier.aspectRatio(1f),
                            contentScale = ContentScale.Crop
                        )
                        // Share overlay
                        // IconButton(
                        //     onClick = { ViewerUtils.shareFile(context, file) },
                        //     modifier = Modifier.align(Alignment.TopEnd).padding(4.dp).background(MaterialTheme.colorScheme.surface.copy(alpha=0.5f), CircleShape).size(24.dp)
                        // ) {
                        //      Icon(Icons.Default.Share, contentDescription = null, modifier = Modifier.padding(4.dp), tint = MaterialTheme.colorScheme.onSurface)
                        // }
                    }
                }
            }
        }
    }
}

@Composable
fun DocumentList(files: List<File>, remoteId: String?) {
     val context = LocalContext.current
    if (files.isEmpty()) {
        EmptyState("No documents found")
    } else {
        LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(files) { file ->
                val ext = file.extension.lowercase()
                val icon = if (ext == "pdf") Icons.Default.PictureAsPdf else Icons.Default.InsertDriveFile
                Card(
                    modifier = Modifier.fillMaxWidth().clickable { /* Download and View Logic */ android.widget.Toast.makeText(context, "Viewing remote document: ${file.name}", android.widget.Toast.LENGTH_SHORT).show() },
                    elevation = CardDefaults.cardElevation(1.dp)
                ) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                         Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.tertiary)
                         Spacer(Modifier.width(16.dp))
                         Column(Modifier.weight(1f)) {
                             Text(file.name, fontWeight = FontWeight.Medium)
                         }
                         IconButton(onClick = { /* ViewerUtils.shareFile(context, file) */ android.widget.Toast.makeText(context, "Sharing remote document: ${file.name}", android.widget.Toast.LENGTH_SHORT).show() }) {
                            Icon(Icons.Default.Share, contentDescription = "Share")
                        }
                    }
                }
            }
        }
    }
}


@Composable
fun EmptyState(message: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

object ViewerUtils {
    fun viewFile(context: android.content.Context, file: File, mimeType: String) {
        try {
            val uri = androidx.core.content.FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                file
            )
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, mimeType)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(intent, "Open with"))
        } catch (e: Exception) {
            android.widget.Toast.makeText(context, "Cannot open file: ${e.localizedMessage}", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

    fun shareFile(context: android.content.Context, file: File) {
        try {
             val uri = androidx.core.content.FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                file
            )
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "*/*" 
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(intent, "Share file"))
        } catch (e: Exception) {
            android.widget.Toast.makeText(context, "Cannot share file", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
}


