package com.bitflow.finance.ui.screens.budget

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.CategoryEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BudgetScreen(
    viewModel: BudgetViewModel = hiltViewModel(),
    onBackClick: () -> Unit = {}
) {
    val budgetedCategories by viewModel.budgetedCategories.collectAsState()
    val allCategories by viewModel.allCategories.collectAsState()
    var showAddDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Spending Limits", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddDialog = true },
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Set Budget")
            }
        }
    ) { padding ->
        if (budgetedCategories.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("💰", style = MaterialTheme.typography.displayLarge)
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("No spending limits set", style = MaterialTheme.typography.titleMedium)
                    Text("Tap + to set a budget for a category", style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(budgetedCategories) { info ->
                    BudgetCard(info)
                }
            }
        }
    }

    if (showAddDialog) {
        SetBudgetDialog(
            categories = allCategories.filter { cat -> 
                budgetedCategories.none { it.categoryId == cat.id }
            },
            onDismiss = { showAddDialog = false },
            onConfirm = { categoryId, budget ->
                viewModel.setBudget(categoryId, budget)
                showAddDialog = false
            }
        )
    }
}

@Composable
fun BudgetCard(info: CategoryBudgetInfo) {
    val animatedProgress by animateFloatAsState(
        targetValue = info.progress,
        animationSpec = tween(600),
        label = "progress"
    )
    
    val progressColor = when {
        info.isOverBudget -> Color(0xFFEF4444) // Red
        info.isNearLimit -> Color(0xFFF59E0B) // Amber
        else -> Color(0xFF10B981) // Green
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(Color(info.color).copy(alpha = 0.15f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(info.icon, style = MaterialTheme.typography.titleMedium)
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(info.categoryName, fontWeight = FontWeight.Bold)
                    Text(
                        "₹${"%,.0f".format(info.spent)} / ₹${"%,.0f".format(info.monthlyBudget)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Gray
                    )
                }
                if (info.isOverBudget || info.isNearLimit) {
                    Icon(
                        Icons.Default.Warning,
                        contentDescription = "Warning",
                        tint = progressColor,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            LinearProgressIndicator(
                progress = animatedProgress,
                modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
                color = progressColor,
                trackColor = progressColor.copy(alpha = 0.2f),
                strokeCap = StrokeCap.Round
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                when {
                    info.isOverBudget -> "⚠️ Over budget by ₹${"%,.0f".format(info.spent - info.monthlyBudget)}"
                    info.isNearLimit -> "⚡ ${(info.progress * 100).toInt()}% used - almost at limit!"
                    else -> "✅ ${(info.progress * 100).toInt()}% used"
                },
                style = MaterialTheme.typography.labelMedium,
                color = progressColor
            )
        }
    }
}

@Composable
@OptIn(ExperimentalMaterial3Api::class)

fun SetBudgetDialog(
    categories: List<CategoryEntity>,
    onDismiss: () -> Unit,
    onConfirm: (Long, Double) -> Unit
) {
    var selectedCategory by remember { mutableStateOf<CategoryEntity?>(null) }
    var budget by remember { mutableStateOf("") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Set Spending Limit") },
        text = {
            Column {
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded }
                ) {
                    OutlinedTextField(
                        value = selectedCategory?.let { "${it.icon} ${it.name}" } ?: "",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Category") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier.menuAnchor().fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        categories.forEach { cat ->
                            DropdownMenuItem(
                                text = { Text("${cat.icon} ${cat.name}") },
                                onClick = {
                                    selectedCategory = cat
                                    expanded = false
                                }
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedTextField(
                    value = budget,
                    onValueChange = { budget = it },
                    label = { Text("Monthly Budget (₹)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val budgetVal = budget.toDoubleOrNull() ?: 0.0
                    if (selectedCategory != null && budgetVal > 0) {
                        onConfirm(selectedCategory!!.id, budgetVal)
                    }
                }
            ) { Text("Set") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}
