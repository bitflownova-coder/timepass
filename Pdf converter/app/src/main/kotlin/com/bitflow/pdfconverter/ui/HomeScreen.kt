package com.bitflow.pdfconverter.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.bitflow.pdfconverter.R
import com.bitflow.pdfconverter.core.domain.model.Folder
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.feature.storage.contract.StorageIntent
import com.bitflow.pdfconverter.feature.storage.contract.StorageSideEffect
import com.bitflow.pdfconverter.feature.storage.viewmodel.StorageViewModel
import com.bitflow.pdfconverter.navigation.Screen
import kotlinx.coroutines.flow.collectLatest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// ─── Data classes ─────────────────────────────────────────────────────────────

private data class FeaturedTool(
    val titleRes: Int,
    val descRes: Int,
    val icon: ImageVector,
    val route: String,
    val gradientColors: List<Color>
)

private data class ToolItem(
    val titleRes: Int,
    val descRes: Int,
    val icon: ImageVector,
    val route: String,
    val iconTint: Color,
    val iconBgColor: Color
)

// ─── Bottom nav items ─────────────────────────────────────────────────────────

private enum class BottomTab(val label: String, val icon: ImageVector, val selectedIcon: ImageVector) {
    HOME("Home", Icons.Outlined.Home, Icons.Filled.Home),
    FILES("Files", Icons.Outlined.Folder, Icons.Filled.Folder),
    TOOLS("Tools", Icons.Outlined.Construction, Icons.Filled.Construction),
    SAVED("Saved", Icons.Outlined.FavoriteBorder, Icons.Filled.Favorite)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavController,
    storageViewModel: StorageViewModel = hiltViewModel()
) {
    val state by storageViewModel.state.collectAsState()
    var selectedTab by remember { mutableIntStateOf(0) }
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(Unit) {
        storageViewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is StorageSideEffect.OpenPdf ->
                    navController.navigate(Screen.Editor.withFile(effect.filePath))
                is StorageSideEffect.ShowError ->
                    snackbarHostState.showSnackbar(effect.message)
                is StorageSideEffect.ShowMessage ->
                    snackbarHostState.showSnackbar(effect.message)
                is StorageSideEffect.SharePdf -> Unit
            }
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            Box {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surface,
                    tonalElevation = 8.dp
                ) {
                    BottomTab.entries.forEachIndexed { index, tab ->
                        NavigationBarItem(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            icon = {
                                Icon(
                                    if (selectedTab == index) tab.selectedIcon else tab.icon,
                                    contentDescription = tab.label
                                )
                            },
                            label = {
                                Text(
                                    tab.label,
                                    style = MaterialTheme.typography.labelSmall,
                                    fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Normal
                                )
                            }
                        )
                    }
                }
                // Floating scan button
                FloatingActionButton(
                    onClick = { navController.navigate(Screen.Scanner.route) },
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .offset(y = (-28).dp)
                        .size(56.dp),
                    shape = CircleShape,
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                    elevation = FloatingActionButtonDefaults.elevation(defaultElevation = 6.dp)
                ) {
                    Icon(
                        Icons.Default.Add,
                        contentDescription = "Scan",
                        modifier = Modifier.size(28.dp)
                    )
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (selectedTab) {
                0 -> HomeTab(navController = navController)
                1 -> FilesTab(
                    documents = state.documents,
                    folders = state.folders,
                    isLoading = state.isLoading,
                    onOpen = { storageViewModel.onIntent(StorageIntent.OpenDocument(it)) },
                    onDelete = { storageViewModel.onIntent(StorageIntent.DeleteDocument(it.id)) },
                    onShare = { storageViewModel.onIntent(StorageIntent.ShareDocument(it)) },
                    onFolderClick = { folder ->
                        storageViewModel.onIntent(StorageIntent.NavigateToFolder(folder.id, folder.name))
                    }
                )
                2 -> AllToolsTab(navController = navController)
                3 -> SavedTab(
                    documents = state.documents,
                    folders = state.folders,
                    isLoading = state.isLoading,
                    onOpen = { storageViewModel.onIntent(StorageIntent.OpenDocument(it)) },
                    onDelete = { storageViewModel.onIntent(StorageIntent.DeleteDocument(it.id)) },
                    onShare = { storageViewModel.onIntent(StorageIntent.ShareDocument(it)) },
                    navController = navController
                )
            }
        }
    }
}

// ─── Home Tab (main page like the image) ──────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeTab(navController: NavController) {
    val featuredTools = listOf(
        FeaturedTool(
            R.string.tool_scan_to_pdf, R.string.tool_scan_to_pdf_desc,
            Icons.Default.DocumentScanner, Screen.Scanner.route,
            listOf(Color(0xFF1B2838), Color(0xFF253545))
        ),
        FeaturedTool(
            R.string.tool_image_to_pdf, R.string.tool_image_to_pdf_desc,
            Icons.Default.Image, Screen.ImageToPdf.route,
            listOf(Color(0xFF324A5E), Color(0xFF1B2838))
        )
    )

    // Daily-use tools only
    val editTools = listOf(
        ToolItem(R.string.tool_merge, R.string.tool_merge_desc, Icons.Default.CallMerge, Screen.MergePdf.route, Color(0xFF3A8F96), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_split, R.string.tool_split_desc, Icons.Default.ContentCut, Screen.SplitPdf.route, Color(0xFF1B2838), Color(0xFFE2E8F0)),
        ToolItem(R.string.tool_edit_text, R.string.tool_edit_text_desc, Icons.Default.Edit, Screen.Editor.route, Color(0xFF6BB8BE), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_compress, R.string.tool_compress_desc, Icons.Default.Compress, Screen.Optimization.route, Color(0xFF324A5E), Color(0xFFE2E8F0))
    )

    Column(modifier = Modifier.fillMaxSize()) {
        // ── Top bar ──
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // App icon
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.PictureAsPdf,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimary,
                    modifier = Modifier.size(24.dp)
                )
            }
            Spacer(Modifier.width(10.dp))
            Text(
                stringResource(R.string.app_name),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
            IconButton(onClick = { navController.navigate(Screen.Settings.route) }) {
                Icon(Icons.Outlined.Settings, contentDescription = "Settings")
            }
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.tertiaryContainer),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.Person,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp),
                    tint = MaterialTheme.colorScheme.onTertiaryContainer
                )
            }
        }

        // ── Scrollable content ──
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(bottom = 16.dp)
        ) {
            // ── Scan Document Banner ──
            Card(
                onClick = { navController.navigate(Screen.Scanner.route) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.Transparent),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            brush = Brush.horizontalGradient(
                                listOf(Color(0xFF1B2838), Color(0xFF324A5E))
                            ),
                            shape = RoundedCornerShape(16.dp)
                        )
                        .padding(20.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "Scan Document",
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "Tap to scan & convert to PDF instantly",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.White.copy(alpha = 0.85f)
                            )
                        }
                        Spacer(Modifier.width(12.dp))
                        Box(
                            modifier = Modifier
                                .size(56.dp)
                                .clip(CircleShape)
                                .background(Color.White.copy(alpha = 0.2f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.DocumentScanner,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(32.dp)
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // ── Featured Tools ──
            SectionHeader(title = "Featured Tools")

            LazyRow(
                contentPadding = PaddingValues(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.height(150.dp)
            ) {
                items(featuredTools.size) { index ->
                    FeaturedToolCard(
                        tool = featuredTools[index],
                        onClick = { navController.navigate(featuredTools[index].route) }
                    )
                }
            }

            Spacer(Modifier.height(24.dp))

            // ── Edit & Markup (daily tools) ──
            SectionHeader(title = "Edit & Markup")
            ToolGrid(tools = editTools, navController = navController)
        }
    }
}

// ─── Section Header ───────────────────────────────────────────────────────────

@Composable
private fun SectionHeader(
    title: String,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.weight(1f)
        )
        if (actionLabel != null && onAction != null) {
            TextButton(onClick = onAction) {
                Text(
                    actionLabel,
                    color = MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.labelLarge
                )
            }
        }
    }
}

// ─── Featured Tool Card (large horizontal card) ──────────────────────────────

@Composable
private fun FeaturedToolCard(
    tool: FeaturedTool,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier
            .width(200.dp)
            .fillMaxHeight(),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.linearGradient(tool.gradientColors),
                    shape = RoundedCornerShape(16.dp)
                )
                .padding(16.dp)
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(Color.White.copy(alpha = 0.2f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        tool.icon,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                }
                Column {
                    Text(
                        stringResource(tool.titleRes),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        stringResource(tool.descRes),
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.White.copy(alpha = 0.85f),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }
    }
}

// ─── Tool Grid (2 columns with icon + title + subtitle) ──────────────────────

@Composable
private fun ToolGrid(
    tools: List<ToolItem>,
    navController: NavController
) {
    val rows = tools.chunked(2)
    Column(
        modifier = Modifier.padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        rows.forEach { rowItems ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                rowItems.forEach { tool ->
                    ToolGridItem(
                        tool = tool,
                        modifier = Modifier.weight(1f),
                        onClick = { navController.navigate(tool.route) }
                    )
                }
                // Fill empty space if odd number
                if (rowItems.size == 1) {
                    Spacer(Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun ToolGridItem(
    tool: ToolItem,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainerLowest
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Circular icon
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(tool.iconBgColor),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    tool.icon,
                    contentDescription = null,
                    tint = tool.iconTint,
                    modifier = Modifier.size(22.dp)
                )
            }
            Column {
                Text(
                    stringResource(tool.titleRes),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    stringResource(tool.descRes).uppercase(),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    letterSpacing = 0.5.sp
                )
            }
        }
    }
}

// ─── Files Tab ────────────────────────────────────────────────────────────────

@Composable
private fun FilesTab(
    documents: List<PdfDocument>,
    folders: List<Folder>,
    isLoading: Boolean,
    onOpen: (PdfDocument) -> Unit,
    onDelete: (PdfDocument) -> Unit,
    onShare: (PdfDocument) -> Unit,
    onFolderClick: (Folder) -> Unit
) {
    when {
        isLoading -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        }
        documents.isEmpty() && folders.isEmpty() -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Icon(
                        Icons.Default.PictureAsPdf,
                        contentDescription = null,
                        modifier = Modifier.size(72.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.35f)
                    )
                    Text(
                        "No PDFs yet",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "Tap + to create your first document",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                }
            }
        }
        else -> {
            LazyColumn(
                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                // Folders section
                if (folders.isNotEmpty()) {
                    item {
                        Text(
                            "Folders",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 8.dp)
                        )
                    }
                    items(folders, key = { "folder_${it.id}" }) { folder ->
                        Card(
                            onClick = { onFolderClick(folder) },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Row(
                                modifier = Modifier.padding(14.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                Icon(
                                    Icons.Default.Folder,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(32.dp)
                                )
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(folder.name, fontWeight = FontWeight.SemiBold)
                                    Text(
                                        "${folder.documentCount} file${if (folder.documentCount != 1) "s" else ""}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Icon(Icons.Default.ChevronRight, contentDescription = null)
                            }
                        }
                    }
                    item {
                        Text(
                            "Documents",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 8.dp)
                        )
                    }
                }

                items(documents, key = { it.id }) { doc ->
                    val folderName = folders.find { it.id == doc.folderId }?.name
                    PdfListItem(
                        document = doc,
                        folderName = folderName,
                        onOpen = { onOpen(doc) },
                        onDelete = { onDelete(doc) },
                        onShare = { onShare(doc) }
                    )
                }
            }
        }
    }
}

@Composable
private fun PdfListItem(
    document: PdfDocument,
    folderName: String?,
    onOpen: () -> Unit,
    onDelete: () -> Unit,
    onShare: () -> Unit
) {
    var showMenu by remember { mutableStateOf(false) }
    val dateStr = remember(document.modifiedAt) {
        SimpleDateFormat("d MMM yyyy", Locale.getDefault()).format(Date(document.modifiedAt))
    }

    Card(
        onClick = onOpen,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(10.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Row(
            modifier = Modifier.padding(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(width = 50.dp, height = 64.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(MaterialTheme.colorScheme.errorContainer),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.PictureAsPdf,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error,
                    modifier = Modifier.size(28.dp)
                )
            }

            Spacer(Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = document.name,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "$dateStr  ·  ${document.pageCount}p  ·  ${document.sizeBytes / 1024}KB",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Box {
                IconButton(onClick = { showMenu = true }, modifier = Modifier.size(32.dp)) {
                    Icon(Icons.Default.MoreVert, contentDescription = "Options")
                }
                DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                    DropdownMenuItem(
                        text = { Text("Open") },
                        onClick = { showMenu = false; onOpen() },
                        leadingIcon = { Icon(Icons.Default.OpenInNew, null) }
                    )
                    DropdownMenuItem(
                        text = { Text("Share") },
                        onClick = { showMenu = false; onShare() },
                        leadingIcon = { Icon(Icons.Default.Share, null) }
                    )
                    DropdownMenuItem(
                        text = { Text("Delete") },
                        onClick = { showMenu = false; onDelete() },
                        leadingIcon = { Icon(Icons.Default.Delete, null) }
                    )
                }
            }
        }
    }
}

// ─── Saved Tab (user's saved PDFs) ────────────────────────────────────────────

@Composable
private fun SavedTab(
    documents: List<PdfDocument>,
    folders: List<Folder>,
    isLoading: Boolean,
    onOpen: (PdfDocument) -> Unit,
    onDelete: (PdfDocument) -> Unit,
    onShare: (PdfDocument) -> Unit,
    navController: NavController
) {
    Column(modifier = Modifier.fillMaxSize()) {
        Text(
            "Saved Files",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(16.dp)
        )

        when {
            isLoading -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            documents.isEmpty() -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(
                            Icons.Default.FolderOpen,
                            contentDescription = null,
                            modifier = Modifier.size(72.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.35f)
                        )
                        Text(
                            "No saved PDFs yet",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            "Your created and downloaded PDFs will appear here",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                        )
                    }
                }
            }
            else -> {
                LazyColumn(
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    items(documents, key = { it.id }) { doc ->
                        val folderName = folders.find { it.id == doc.folderId }?.name
                        PdfListItem(
                            document = doc,
                            folderName = folderName,
                            onOpen = { onOpen(doc) },
                            onDelete = { onDelete(doc) },
                            onShare = { onShare(doc) }
                        )
                    }
                }
            }
        }
    }
}

// ─── All Tools Tab (categorized with H+V mix) ───────────────────────────────

@Composable
private fun AllToolsTab(navController: NavController) {
    // Create & Convert — horizontal scrolling cards
    val createTools = listOf(
        FeaturedTool(R.string.tool_scan_to_pdf, R.string.tool_scan_to_pdf_desc, Icons.Default.DocumentScanner, Screen.Scanner.route, listOf(Color(0xFF1B2838), Color(0xFF253545))),
        FeaturedTool(R.string.tool_image_to_pdf, R.string.tool_image_to_pdf_desc, Icons.Default.Image, Screen.ImageToPdf.route, listOf(Color(0xFF324A5E), Color(0xFF1B2838))),
        FeaturedTool(R.string.tool_office_to_pdf, R.string.tool_office_to_pdf_desc, Icons.Default.Description, Screen.OfficeToPdf.route, listOf(Color(0xFF3A8F96), Color(0xFF2A6F74))),
        FeaturedTool(R.string.tool_downloader, R.string.tool_downloader_desc, Icons.Default.Download, Screen.PdfDownloader.route, listOf(Color(0xFF253545), Color(0xFF324A5E)))
    )

    // Edit & Organize — vertical grid
    val editTools = listOf(
        ToolItem(R.string.tool_merge, R.string.tool_merge_desc, Icons.Default.CallMerge, Screen.MergePdf.route, Color(0xFF3A8F96), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_split, R.string.tool_split_desc, Icons.Default.ContentCut, Screen.SplitPdf.route, Color(0xFF1B2838), Color(0xFFE2E8F0)),
        ToolItem(R.string.tool_edit_text, R.string.tool_edit_text_desc, Icons.Default.Edit, Screen.Editor.route, Color(0xFF6BB8BE), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_compress, R.string.tool_compress_desc, Icons.Default.Compress, Screen.Optimization.route, Color(0xFF324A5E), Color(0xFFE2E8F0))
    )

    // Security — horizontal scrolling
    val securityTools = listOf(
        FeaturedTool(R.string.tool_password, R.string.tool_password_desc, Icons.Default.Lock, Screen.Security.withSection("PASSWORD"), listOf(Color(0xFF253545), Color(0xFF1B2838))),
        FeaturedTool(R.string.tool_watermark, R.string.tool_watermark_desc, Icons.Default.BrandingWatermark, Screen.Security.withSection("WATERMARK"), listOf(Color(0xFF3A8F96), Color(0xFF2A6F74))),
        FeaturedTool(R.string.tool_redact, R.string.tool_redact_desc, Icons.Default.VisibilityOff, Screen.Security.withSection("REDACT"), listOf(Color(0xFF324A5E), Color(0xFF253545)))
    )

    // Smart Tools — vertical grid
    val smartTools = listOf(
        ToolItem(R.string.tool_ocr, R.string.tool_ocr_desc, Icons.Default.TextSnippet, Screen.SmartTools.withSection("OCR"), Color(0xFF1B2838), Color(0xFFE2E8F0)),
        ToolItem(R.string.tool_qr_scan, R.string.tool_qr_scan_desc, Icons.Default.QrCodeScanner, Screen.SmartTools.withSection("QR_SCAN"), Color(0xFF3A8F96), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_qr_gen, R.string.tool_qr_gen_desc, Icons.Default.QrCode, Screen.SmartTools.withSection("QR_GEN"), Color(0xFF6BB8BE), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_pdf_search, R.string.tool_pdf_search_desc, Icons.Default.Search, Screen.SmartTools.withSection("PDF_SEARCH"), Color(0xFF324A5E), Color(0xFFE2E8F0))
    )

    // Utility — vertical grid
    val utilityTools = listOf(
        ToolItem(R.string.tool_stamp, R.string.tool_stamp_desc, Icons.Default.Approval, Screen.Utility.withSection("STAMP"), Color(0xFF3A8F96), Color(0xFFE6F6F7)),
        ToolItem(R.string.tool_form, R.string.tool_form_desc, Icons.Default.ListAlt, Screen.Utility.withSection("FORM"), Color(0xFF1B2838), Color(0xFFE2E8F0)),
        ToolItem(R.string.tool_storage, R.string.tool_storage_desc, Icons.Default.FolderOpen, Screen.Storage.route, Color(0xFF324A5E), Color(0xFFE2E8F0))
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            "All Tools",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)
        )

        // ── Create & Convert (horizontal) ──
        SectionHeader(title = "Create & Convert")
        LazyRow(
            contentPadding = PaddingValues(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.height(140.dp)
        ) {
            items(createTools.size) { i ->
                FeaturedToolCard(
                    tool = createTools[i],
                    onClick = { navController.navigate(createTools[i].route) }
                )
            }
        }

        Spacer(Modifier.height(20.dp))

        // ── Edit & Organize (vertical grid) ──
        SectionHeader(title = "Edit & Organize")
        ToolGrid(tools = editTools, navController = navController)

        Spacer(Modifier.height(20.dp))

        // ── Security & Protection (horizontal) ──
        SectionHeader(title = "Security & Protection")
        LazyRow(
            contentPadding = PaddingValues(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.height(140.dp)
        ) {
            items(securityTools.size) { i ->
                FeaturedToolCard(
                    tool = securityTools[i],
                    onClick = { navController.navigate(securityTools[i].route) }
                )
            }
        }

        Spacer(Modifier.height(20.dp))

        // ── Smart Tools (vertical grid) ──
        SectionHeader(title = "Smart Tools")
        ToolGrid(tools = smartTools, navController = navController)

        Spacer(Modifier.height(20.dp))

        // ── Utility & More (vertical grid) ──
        SectionHeader(title = "Utility & More")
        ToolGrid(tools = utilityTools, navController = navController)

        Spacer(Modifier.height(24.dp))
    }
}
