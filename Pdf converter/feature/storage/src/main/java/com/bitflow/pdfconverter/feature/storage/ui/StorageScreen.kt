package com.bitflow.pdfconverter.feature.storage.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.platform.LocalContext
import com.bitflow.pdfconverter.core.domain.model.Folder
import com.bitflow.pdfconverter.core.domain.model.PdfDocument
import com.bitflow.pdfconverter.core.ui.components.PdfEmptyState
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar
import com.bitflow.pdfconverter.feature.storage.contract.SortOrder
import com.bitflow.pdfconverter.feature.storage.contract.StorageIntent
import com.bitflow.pdfconverter.feature.storage.contract.StorageSideEffect
import com.bitflow.pdfconverter.feature.storage.contract.StorageState
import com.bitflow.pdfconverter.feature.storage.contract.ViewMode
import com.bitflow.pdfconverter.feature.storage.viewmodel.StorageViewModel
import kotlinx.coroutines.flow.collectLatest

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StorageScreen(
    onNavigateBack: () -> Unit,
    onOpenPdf: (String) -> Unit,
    viewModel: StorageViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val context = LocalContext.current
    var showCreateFolderDialog by remember { mutableStateOf(false) }
    var showSortSheet by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.sideEffects.collectLatest { effect ->
            when (effect) {
                is StorageSideEffect.OpenPdf -> onOpenPdf(effect.filePath)
                is StorageSideEffect.ShowError -> snackbarHostState.showSnackbar(effect.message)
                is StorageSideEffect.ShowMessage -> snackbarHostState.showSnackbar(effect.message)
                is StorageSideEffect.SharePdf -> {
                    val shareIntent = Intent(Intent.ACTION_SEND).apply {
                        type = "application/pdf"
                        putExtra(Intent.EXTRA_STREAM, effect.uri)
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    context.startActivity(Intent.createChooser(shareIntent, "Share PDF"))
                }
            }
        }
    }

    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { viewModel.onIntent(StorageIntent.ImportFile(it)) }
    }

    Scaffold(
        topBar = {
            if (state.isSelectionMode) {
                SelectionTopBar(
                    selectedCount = state.selectedDocumentIds.size,
                    onClear = { viewModel.onIntent(StorageIntent.ClearSelection) },
                    onDeleteSelected = { viewModel.onIntent(StorageIntent.DeleteSelected) },
                    onSelectAll = { viewModel.onIntent(StorageIntent.SelectAll) }
                )
            } else {
                PdfTopBar(
                    title = state.currentFolderName,
                    onNavigateBack = onNavigateBack,
                    actions = {
                        IconButton(onClick = {
                            val newMode = if (state.viewMode == ViewMode.GRID) ViewMode.LIST else ViewMode.GRID
                            viewModel.onIntent(StorageIntent.ViewModeChanged(newMode))
                        }) {
                            Icon(
                                if (state.viewMode == ViewMode.GRID) Icons.Default.ViewList else Icons.Default.GridView,
                                contentDescription = "Toggle view"
                            )
                        }
                        IconButton(onClick = { showSortSheet = true }) {
                            Icon(Icons.Default.Sort, "Sort")
                        }
                    }
                )
            }
        },
        floatingActionButton = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp), horizontalAlignment = Alignment.End) {
                SmallFloatingActionButton(
                    onClick = { showCreateFolderDialog = true }
                ) { Icon(Icons.Default.CreateNewFolder, "New folder") }
                FloatingActionButton(
                    onClick = { filePicker.launch("application/pdf") }
                ) { Icon(Icons.Default.Add, "Import PDF") }
            }
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Search bar
            SearchBar(
                query = state.searchQuery,
                onQueryChange = { viewModel.onIntent(StorageIntent.SearchQueryChanged(it)) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp)
            )

            // Folder chips
            if (state.folders.isNotEmpty()) {
                FolderRow(
                    folders = state.folders,
                    currentFolderId = state.currentFolderId,
                    onFolderClick = { folder ->
                        viewModel.onIntent(StorageIntent.NavigateToFolder(folder.id, folder.name))
                    },
                    onRootClick = {
                        viewModel.onIntent(StorageIntent.NavigateToFolder(null, "All Files"))
                    }
                )
            }

            // Documents
            val filtered = state.documents.filter {
                state.searchQuery.isBlank() || it.name.contains(state.searchQuery, ignoreCase = true)
            }

            if (filtered.isEmpty()) {
                PdfEmptyState(message = "No PDFs found")
            } else if (state.viewMode == ViewMode.GRID) {
                DocumentGrid(
                    documents = filtered,
                    selectedIds = state.selectedDocumentIds,
                    onOpen = { viewModel.onIntent(StorageIntent.OpenDocument(it)) },
                    onLongPress = { viewModel.onIntent(StorageIntent.ToggleSelection(it.id)) },
                    onDelete = { viewModel.onIntent(StorageIntent.DeleteDocument(it.id)) },
                    onShare = { viewModel.onIntent(StorageIntent.ShareDocument(it)) }
                )
            } else {
                DocumentList(
                    documents = filtered,
                    selectedIds = state.selectedDocumentIds,
                    onOpen = { viewModel.onIntent(StorageIntent.OpenDocument(it)) },
                    onLongPress = { viewModel.onIntent(StorageIntent.ToggleSelection(it.id)) },
                    onDelete = { viewModel.onIntent(StorageIntent.DeleteDocument(it.id)) },
                    onShare = { viewModel.onIntent(StorageIntent.ShareDocument(it)) }
                )
            }
        }
    }

    if (showCreateFolderDialog) {
        CreateFolderDialog(
            onConfirm = { name ->
                viewModel.onIntent(StorageIntent.CreateFolder(name, state.currentFolderId))
                showCreateFolderDialog = false
            },
            onDismiss = { showCreateFolderDialog = false }
        )
    }

    if (showSortSheet) {
        SortBottomSheet(
            currentOrder = state.sortOrder,
            onOrderSelected = {
                viewModel.onIntent(StorageIntent.SortOrderChanged(it))
                showSortSheet = false
            },
            onDismiss = { showSortSheet = false }
        )
    }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

@Composable
private fun SearchBar(query: String, onQueryChange: (String) -> Unit, modifier: Modifier = Modifier) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        label = { Text("Search files…") },
        leadingIcon = { Icon(Icons.Default.Search, null) },
        singleLine = true,
        modifier = modifier
    )
}

@Composable
private fun FolderRow(
    folders: List<Folder>,
    currentFolderId: Long?,
    onFolderClick: (Folder) -> Unit,
    onRootClick: () -> Unit
) {
    androidx.compose.foundation.lazy.LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        item {
            FilterChip(
                selected = currentFolderId == null,
                onClick = onRootClick,
                label = { Text("All Files") },
                leadingIcon = { Icon(Icons.Default.Folder, null, modifier = Modifier.size(16.dp)) }
            )
        }
        items(folders) { folder ->
            FilterChip(
                selected = currentFolderId == folder.id,
                onClick = { onFolderClick(folder) },
                label = { Text(folder.name) },
                leadingIcon = { Icon(Icons.Default.Folder, null, modifier = Modifier.size(16.dp)) }
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun DocumentGrid(
    documents: List<PdfDocument>,
    selectedIds: Set<Long>,
    onOpen: (PdfDocument) -> Unit,
    onLongPress: (PdfDocument) -> Unit,
    onDelete: (PdfDocument) -> Unit,
    onShare: (PdfDocument) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(documents, key = { it.id }) { doc ->
            DocumentGridCard(
                document = doc,
                isSelected = doc.id in selectedIds,
                onOpen = { onOpen(doc) },
                onLongPress = { onLongPress(doc) },
                onDelete = { onDelete(doc) },
                onShare = { onShare(doc) }
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun DocumentGridCard(
    document: PdfDocument,
    isSelected: Boolean,
    onOpen: () -> Unit,
    onLongPress: () -> Unit,
    onDelete: () -> Unit,
    onShare: () -> Unit
) {
    var showMenu by remember { mutableStateOf(false) }

    ElevatedCard(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(onClick = onOpen, onLongClick = onLongPress),
        colors = CardDefaults.elevatedCardColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer
            else MaterialTheme.colorScheme.surface
        )
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Icon(
                    Icons.Default.PictureAsPdf,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error,
                    modifier = Modifier.size(32.dp)
                )
                Box {
                    IconButton(onClick = { showMenu = true }, modifier = Modifier.size(24.dp)) {
                        Icon(Icons.Default.MoreVert, null, modifier = Modifier.size(16.dp))
                    }
                    DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
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
            Spacer(Modifier.height(8.dp))
            Text(
                document.name,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Medium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                "${document.sizeBytes / 1024}KB · ${document.pageCount}p",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun DocumentList(
    documents: List<PdfDocument>,
    selectedIds: Set<Long>,
    onOpen: (PdfDocument) -> Unit,
    onLongPress: (PdfDocument) -> Unit,
    onDelete: (PdfDocument) -> Unit,
    onShare: (PdfDocument) -> Unit
) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(documents, key = { it.id }) { doc ->
            var showMenu by remember { mutableStateOf(false) }
            var showProperties by remember { mutableStateOf(false) }
            if (showProperties) {
                DocumentPropertiesDialog(document = doc, onDismiss = { showProperties = false })
            }
            ListItem(
                modifier = Modifier.combinedClickable(
                    onClick = { onOpen(doc) },
                    onLongClick = { onLongPress(doc) }
                ),
                headlineContent = { Text(doc.name, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                supportingContent = { Text("${doc.sizeBytes / 1024}KB · ${doc.pageCount} pages") },
                leadingContent = {
                    Icon(Icons.Default.PictureAsPdf, null, tint = MaterialTheme.colorScheme.error)
                },
                trailingContent = {
                    Box {
                        IconButton(onClick = { showMenu = true }) {
                            Icon(Icons.Default.MoreVert, null)
                        }
                        DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                            DropdownMenuItem(
                                text = { Text("Share") },
                                onClick = { showMenu = false; onShare(doc) }
                            )
                            DropdownMenuItem(
                                text = { Text("Properties") },
                                onClick = { showMenu = false; showProperties = true }
                            )
                            DropdownMenuItem(
                                text = { Text("Delete") },
                                onClick = { showMenu = false; onDelete(doc) }
                            )
                        }
                    }
                }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SelectionTopBar(
    selectedCount: Int,
    onClear: () -> Unit,
    onDeleteSelected: () -> Unit,
    onSelectAll: () -> Unit
) {
    TopAppBar(
        title = { Text("$selectedCount selected") },
        navigationIcon = {
            IconButton(onClick = onClear) { Icon(Icons.Default.Close, "Clear selection") }
        },
        actions = {
            IconButton(onClick = onSelectAll) { Icon(Icons.Default.SelectAll, "Select all") }
            IconButton(onClick = onDeleteSelected) { Icon(Icons.Default.Delete, "Delete") }
        }
    )
}

@Composable
private fun CreateFolderDialog(onConfirm: (String) -> Unit, onDismiss: () -> Unit) {
    var name by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Folder") },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Folder name") },
                singleLine = true
            )
        },
        confirmButton = {
            TextButton(onClick = { if (name.isNotBlank()) onConfirm(name) }, enabled = name.isNotBlank()) {
                Text("Create")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
private fun SortBottomSheet(
    currentOrder: SortOrder,
    onOrderSelected: (SortOrder) -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState()
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheetState) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("Sort by", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            val options = listOf(
                SortOrder.MODIFIED_DESC to "Modified (newest first)",
                SortOrder.MODIFIED_ASC to "Modified (oldest first)",
                SortOrder.NAME_ASC to "Name (A–Z)",
                SortOrder.NAME_DESC to "Name (Z–A)",
                SortOrder.SIZE_DESC to "Size (largest)",
                SortOrder.SIZE_ASC to "Size (smallest)"
            )
            options.forEach { (order, label) ->
                ListItem(
                    headlineContent = { Text(label) },
                    trailingContent = {
                        if (currentOrder == order) Icon(Icons.Default.Check, null)
                    },
                    modifier = Modifier.combinedClickable(onClick = { onOrderSelected(order) })
                )
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

@Composable
private fun DocumentPropertiesDialog(document: PdfDocument, onDismiss: () -> Unit) {
    val sizeKb = document.sizeBytes / 1024
    val sizeMb = sizeKb / 1024.0
    val sizeStr = if (sizeKb > 1024) "%.2f MB".format(sizeMb) else "$sizeKb KB"
    val dateAdded = java.text.SimpleDateFormat("MMM dd, yyyy HH:mm", java.util.Locale.getDefault())
        .format(java.util.Date(document.createdAt))
    val dateModified = java.text.SimpleDateFormat("MMM dd, yyyy HH:mm", java.util.Locale.getDefault())
        .format(java.util.Date(document.modifiedAt))

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Document Properties") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                PropertyRow("Name", document.name)
                PropertyRow("Pages", document.pageCount.toString())
                PropertyRow("Size", sizeStr)
                PropertyRow("Added", dateAdded)
                PropertyRow("Modified", dateModified)
                PropertyRow("Path", document.filePath, singleLine = false)
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Close") }
        }
    )
}

@Composable
private fun PropertyRow(label: String, value: String, singleLine: Boolean = true) {
    Column {
        Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(
            value,
            style = MaterialTheme.typography.bodySmall,
            maxLines = if (singleLine) 1 else Int.MAX_VALUE
        )
        HorizontalDivider(modifier = Modifier.padding(top = 4.dp))
    }
}
