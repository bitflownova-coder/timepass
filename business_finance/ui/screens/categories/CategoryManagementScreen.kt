package com.bitflow.finance.ui.screens.categories

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.model.CategoryType

/**
 * Human-centric category management
 * - User can delete ANY category
 * - Smart merge logic when deleting
 * - Automatic sorting by usage
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun CategoryManagementScreen(
    viewModel: CategoryManagementViewModel = hiltViewModel(),
    onBackClick: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        "Manage Categories",
                        fontWeight = FontWeight.Bold
                    ) 
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.showAddCategoryDialog() }) {
                        Icon(Icons.Outlined.Add, contentDescription = "Add category")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Text(
                    "Sorted by most used",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(start = 4.dp, bottom = 4.dp)
                )
            }

            items(
                items = uiState.categories,
                key = { it.id }
            ) { category ->
                CategoryManagementItem(
                    category = category,
                    onEditClick = { viewModel.showEditDialog(category) },
                    onDeleteClick = { viewModel.showDeleteConfirmation(category) },
                    onVisibilityToggle = { viewModel.toggleCategoryVisibility(category) },
                    modifier = Modifier.animateItemPlacement()
                )
            }
        }
    }

    // Delete confirmation with merge options
    if (uiState.showDeleteDialog) {
        CategoryDeleteDialog(
            category = uiState.categoryToDelete!!,
            availableCategories = uiState.categories.filter { it.id != uiState.categoryToDelete?.id },
            onConfirm = { targetCategoryId ->
                viewModel.deleteCategory(uiState.categoryToDelete!!.id, targetCategoryId)
            },
            onDismiss = { viewModel.dismissDeleteDialog() }
        )
    }

    if (uiState.showAddEditDialog) {
        AddEditCategoryDialog(
            category = uiState.categoryToEdit,
            onDismiss = { viewModel.dismissAddEditDialog() },
            onSave = { name, icon, color, type ->
                viewModel.saveCategory(name, icon, color, type)
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddEditCategoryDialog(
    category: Category?,
    onDismiss: () -> Unit,
    onSave: (String, String, Int, CategoryType) -> Unit
) {
    var name by remember { mutableStateOf(category?.name ?: "") }
    var icon by remember { mutableStateOf(category?.icon ?: "📁") }
    var color by remember { mutableStateOf(category?.color ?: 0xFF4CAF50.toInt()) }
    var type by remember { mutableStateOf(category?.type ?: CategoryType.EXPENSE) }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (category == null) "Add Category" else "Edit Category") },
        text = {
            Column {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = icon,
                    onValueChange = { icon = it },
                    label = { Text("Icon (Emoji)") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                
                // Type Dropdown
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded }
                ) {
                    OutlinedTextField(
                        value = type.name,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Type") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        colors = ExposedDropdownMenuDefaults.outlinedTextFieldColors(),
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        CategoryType.values().forEach { t ->
                            DropdownMenuItem(
                                text = { Text(t.name) },
                                onClick = {
                                    type = t
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (name.isNotBlank()) {
                        onSave(name, icon, color, type)
                    }
                }
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

@Composable
fun CategoryManagementItem(
    category: Category,
    onEditClick: () -> Unit,
    onDeleteClick: () -> Unit,
    onVisibilityToggle: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (category.isHidden)
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            else
                MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icon/Emoji
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(
                        if (category.isHidden) 
                            MaterialTheme.colorScheme.surfaceVariant 
                        else 
                            MaterialTheme.colorScheme.primaryContainer
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = category.icon,
                    fontSize = 24.sp
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = category.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = if (category.isHidden) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = "Used ${category.usageCount} times",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Actions
            Row(
                horizontalArrangement = Arrangement.spacedBy(0.dp)
            ) {
                IconButton(onClick = onVisibilityToggle) {
                    Icon(
                        imageVector = if (category.isHidden) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,
                        contentDescription = if (category.isHidden) "Show" else "Hide",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                IconButton(onClick = onEditClick) {
                    Icon(
                        imageVector = Icons.Outlined.Edit,
                        contentDescription = "Edit",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (category.isUserDeletable) {
                    IconButton(onClick = onDeleteClick) {
                        Icon(
                            imageVector = Icons.Outlined.Delete,
                            contentDescription = "Delete",
                            tint = MaterialTheme.colorScheme.error
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun CategoryDeleteDialog(
    category: Category,
    availableCategories: List<Category>,
    onConfirm: (targetCategoryId: Long?) -> Unit,
    onDismiss: () -> Unit
) {
    var selectedMergeCategoryId by remember { mutableStateOf<Long?>(null) }
    var deleteOption by remember { mutableStateOf(DeleteOption.MERGE) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text("Delete \"${category.name}\"?")
        },
        text = {
            Column {
                Text(
                    "You have ${category.usageCount} activities in this category.",
                    style = MaterialTheme.typography.bodyMedium
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    "What should we do with them?",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(modifier = Modifier.height(12.dp))

                // Option 1: Merge
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .clickable { deleteOption = DeleteOption.MERGE }
                        .background(
                            if (deleteOption == DeleteOption.MERGE)
                                MaterialTheme.colorScheme.primaryContainer
                            else
                                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                        )
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = deleteOption == DeleteOption.MERGE,
                        onClick = { deleteOption = DeleteOption.MERGE }
                    )
                    Text("Move to another category")
                }

                // Category selector (only shown if merge is selected)
                if (deleteOption == DeleteOption.MERGE) {
                    Spacer(modifier = Modifier.height(8.dp))
                    LazyColumn(
                        modifier = Modifier.height(150.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        items(availableCategories) { targetCategory ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(8.dp))
                                    .clickable { selectedMergeCategoryId = targetCategory.id }
                                    .background(
                                        if (selectedMergeCategoryId == targetCategory.id)
                                            MaterialTheme.colorScheme.secondaryContainer
                                        else
                                            MaterialTheme.colorScheme.surface
                                    )
                                    .padding(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(text = targetCategory.icon, fontSize = 20.sp)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(targetCategory.name)
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Option 2: Uncategorized
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .clickable { deleteOption = DeleteOption.UNCATEGORIZED }
                        .background(
                            if (deleteOption == DeleteOption.UNCATEGORIZED)
                                MaterialTheme.colorScheme.primaryContainer
                            else
                                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                        )
                        .padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = deleteOption == DeleteOption.UNCATEGORIZED,
                        onClick = { deleteOption = DeleteOption.UNCATEGORIZED }
                    )
                    Text("Mark as Uncategorized")
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    when (deleteOption) {
                        DeleteOption.MERGE -> {
                            if (selectedMergeCategoryId != null) {
                                onConfirm(selectedMergeCategoryId)
                            }
                        }
                        DeleteOption.UNCATEGORIZED -> onConfirm(null)
                    }
                },
                enabled = deleteOption == DeleteOption.UNCATEGORIZED || selectedMergeCategoryId != null
            ) {
                Text("Delete")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

enum class DeleteOption {
    MERGE,
    UNCATEGORIZED
}
