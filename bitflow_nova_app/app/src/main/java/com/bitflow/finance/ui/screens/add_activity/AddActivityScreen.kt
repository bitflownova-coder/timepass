package com.bitflow.finance.ui.screens.add_activity

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CalendarToday
import androidx.compose.material.icons.filled.MoreHoriz
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.Category
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/**
 * Speed-optimized "Add Activity" screen
 * Philosophy: Type amount → Tap category → Done. No confirmation needed.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddActivityScreen(
    viewModel: AddActivityViewModel = hiltViewModel(),
    onBackClick: () -> Unit,
    onActivityAdded: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(uiState.isActivitySaved) {
        if (uiState.isActivitySaved) {
            onActivityAdded()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Add Activity") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
        ) {
            // Top: Big Amount Input with Type Toggle
            AmountInputSection(
                amount = uiState.amount,
                activityType = uiState.activityType,
                currencySymbol = uiState.currencySymbol,
                onAmountChange = { viewModel.updateAmount(it) },
                onTypeToggle = { viewModel.toggleActivityType() }
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Middle: Category Grid (Top 8 most used + "More")
            Text(
                "Choose Category",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(12.dp))

            CategoryGrid(
                categories = uiState.topCategories,
                selectedCategoryId = uiState.selectedCategoryId,
                onCategoryClick = { category ->
                    viewModel.selectCategory(category)
                    // Auto-save if amount is entered
                    if (uiState.amount.isNotEmpty() && uiState.amount.toDoubleOrNull() != null) {
                        viewModel.saveActivity()
                    }
                },
                onMoreClick = { viewModel.showAllCategories() }
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Bottom: Optional Note and Date
            OptionalDetailsSection(
                note = uiState.note,
                date = uiState.activityDate,
                onNoteChange = { viewModel.updateNote(it) },
                onDateClick = { viewModel.showDatePicker() }
            )

            Spacer(modifier = Modifier.weight(1f))

            // Custom Numpad
            CustomNumpad(
                onNumberClick = { viewModel.appendToAmount(it) },
                onDecimalClick = { viewModel.appendToAmount(".") },
                onBackspaceClick = { viewModel.removeLastDigit() }
            )
        }
    }

    // Show all categories dialog
    if (uiState.showAllCategoriesDialog) {
        AllCategoriesDialog(
            categories = uiState.allCategories,
            onCategoryClick = { category ->
                viewModel.selectCategory(category)
                viewModel.dismissAllCategories()
                if (uiState.amount.isNotEmpty() && uiState.amount.toDoubleOrNull() != null) {
                    viewModel.saveActivity()
                }
            },
            onDismiss = { viewModel.dismissAllCategories() }
        )
    }
}

@Composable
fun AmountInputSection(
    amount: String,
    activityType: ActivityType,
    currencySymbol: String,
    onAmountChange: (String) -> Unit,
    onTypeToggle: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.fillMaxWidth()
    ) {
        // Type Toggle (Expense / Income)
        Row(
            modifier = Modifier
                .clip(RoundedCornerShape(16.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .padding(4.dp)
        ) {
            TypeToggleButton(
                text = "Expense",
                isSelected = activityType == ActivityType.EXPENSE,
                color = Color(0xFFEF5350),
                onClick = { if (activityType != ActivityType.EXPENSE) onTypeToggle() }
            )
            TypeToggleButton(
                text = "Income",
                isSelected = activityType == ActivityType.INCOME,
                color = Color(0xFF66BB6A),
                onClick = { if (activityType != ActivityType.INCOME) onTypeToggle() }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Big Amount Display
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                text = currencySymbol,
                style = TextStyle(
                    fontSize = 36.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = if (amount.isEmpty()) "0" else amount,
                style = TextStyle(
                    fontSize = 56.sp,
                    fontWeight = FontWeight.Bold,
                    color = when (activityType) {
                        ActivityType.EXPENSE -> Color(0xFFEF5350)
                        ActivityType.INCOME -> Color(0xFF66BB6A)
                        ActivityType.TRANSFER -> MaterialTheme.colorScheme.primary
                    }
                )
            )
        }
    }
}

@Composable
fun TypeToggleButton(
    text: String,
    isSelected: Boolean,
    color: Color,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(if (isSelected) color else Color.Transparent)
            .clickable(onClick = onClick)
            .padding(horizontal = 32.dp, vertical = 12.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            color = if (isSelected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
        )
    }
}

@Composable
fun CategoryGrid(
    categories: List<Category>,
    selectedCategoryId: Long?,
    onCategoryClick: (Category) -> Unit,
    onMoreClick: () -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(4),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.height(200.dp)
    ) {
        items(categories.take(7)) { category ->
            CategoryItem(
                category = category,
                isSelected = category.id == selectedCategoryId,
                onClick = { onCategoryClick(category) }
            )
        }
        
        // "More" button
        item {
            CategoryMoreButton(onClick = onMoreClick)
        }
    }
}

@Composable
fun CategoryItem(
    category: Category,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(
                if (isSelected)
                    MaterialTheme.colorScheme.primaryContainer
                else
                    MaterialTheme.colorScheme.surfaceVariant
            )
            .clickable(onClick = onClick)
            .padding(12.dp)
    ) {
        // Emoji/Icon (3D-style would be added here)
        Text(
            text = category.icon,
            style = TextStyle(fontSize = 32.sp)
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = category.name,
            style = MaterialTheme.typography.labelSmall,
            textAlign = TextAlign.Center,
            maxLines = 1,
            color = if (isSelected)
                MaterialTheme.colorScheme.onPrimaryContainer
            else
                MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun CategoryMoreButton(onClick: () -> Unit) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .clickable(onClick = onClick)
            .padding(12.dp)
    ) {
        Icon(
            imageVector = Icons.Default.MoreHoriz,
            contentDescription = "More categories",
            modifier = Modifier.size(32.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = "More",
            style = MaterialTheme.typography.labelSmall,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
fun OptionalDetailsSection(
    note: String,
    date: LocalDate,
    onNoteChange: (String) -> Unit,
    onDateClick: () -> Unit
) {
    Column {
        // Note field
        OutlinedTextField(
            value = note,
            onValueChange = onNoteChange,
            label = { Text("Note (Optional)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Date selector
        OutlinedButton(
            onClick = onDateClick,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(
                imageVector = Icons.Default.CalendarToday,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = if (date == LocalDate.now()) "Today" else date.format(
                    DateTimeFormatter.ofPattern("MMM dd, yyyy")
                )
            )
        }
    }
}

@Composable
fun CustomNumpad(
    onNumberClick: (String) -> Unit,
    onDecimalClick: () -> Unit,
    onBackspaceClick: () -> Unit
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Row 1: 1, 2, 3
        NumpadRow(
            buttons = listOf("1", "2", "3"),
            onButtonClick = onNumberClick
        )
        // Row 2: 4, 5, 6
        NumpadRow(
            buttons = listOf("4", "5", "6"),
            onButtonClick = onNumberClick
        )
        // Row 3: 7, 8, 9
        NumpadRow(
            buttons = listOf("7", "8", "9"),
            onButtonClick = onNumberClick
        )
        // Row 4: ., 0, ⌫
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            NumpadButton(
                text = ".",
                onClick = onDecimalClick,
                modifier = Modifier.weight(1f)
            )
            NumpadButton(
                text = "0",
                onClick = { onNumberClick("0") },
                modifier = Modifier.weight(1f)
            )
            NumpadButton(
                text = "⌫",
                onClick = onBackspaceClick,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
fun NumpadRow(
    buttons: List<String>,
    onButtonClick: (String) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        buttons.forEach { button ->
            NumpadButton(
                text = button,
                onClick = { onButtonClick(button) },
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
fun NumpadButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(56.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            contentColor = MaterialTheme.colorScheme.onSurfaceVariant
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Text(
            text = text,
            style = TextStyle(
                fontSize = 24.sp,
                fontWeight = FontWeight.Medium
            )
        )
    }
}

@Composable
fun AllCategoriesDialog(
    categories: List<Category>,
    onCategoryClick: (Category) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("All Categories") },
        text = {
            LazyVerticalGrid(
                columns = GridCells.Fixed(3),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.height(300.dp)
            ) {
                items(categories) { category ->
                    CategoryItem(
                        category = category,
                        isSelected = false,
                        onClick = { onCategoryClick(category) }
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Close")
            }
        }
    )
}
