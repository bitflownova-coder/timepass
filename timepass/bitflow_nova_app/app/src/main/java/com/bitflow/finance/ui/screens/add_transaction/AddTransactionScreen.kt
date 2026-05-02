package com.bitflow.finance.ui.screens.add_transaction

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.ripple.rememberRipple
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Account
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.Category

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddTransactionScreen(
    viewModel: AddTransactionViewModel = hiltViewModel(),
    onBackClick: () -> Unit,
    onSuccess: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    // Camera launcher
    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success) {
            // Photo saved to URI
        }
    }
    
    // Gallery picker
    val galleryLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let { viewModel.setBillPhoto(it.toString()) }
    }

    // val uiState by viewModel.uiState.collectAsState() removed duplicate

    LaunchedEffect(uiState.saved) {
        if (uiState.saved) {
            onSuccess()
        }
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {},
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = MaterialTheme.colorScheme.onBackground)
                    }
                },
                actions = {
                    // Start thinking/listening state
                    var isListening by remember { mutableStateOf(false) }
                    val context = androidx.compose.ui.platform.LocalContext.current
                    
                    if (isListening) {
                        LaunchedEffect(Unit) {
                            com.bitflow.finance.util.VoiceInputHelper.startListening(context).collect { result ->
                                when (result) {
                                    is com.bitflow.finance.util.VoiceInputHelper.VoiceResult.Success -> {
                                        viewModel.processVoiceInput(result.rawText)
                                        isListening = false
                                    }
                                    is com.bitflow.finance.util.VoiceInputHelper.VoiceResult.Error -> {
                                        isListening = false
                                        // TODO: Show toast error
                                    }
                                    else -> {} // processing
                                }
                            }
                        }
                    }

                    // Microphone Button
                    IconButton(onClick = { isListening = !isListening }) {
                        Icon(
                            imageVector = if (isListening) Icons.Default.Mic else Icons.Default.MicNone,
                            contentDescription = "Voice Input",
                            tint = if (isListening) Color.Red else MaterialTheme.colorScheme.onBackground
                        )
                    }

                    // Bill Photo Button
                    IconButton(onClick = { galleryLauncher.launch("image/*") }) {
                        Icon(
                            imageVector = if (uiState.billPhotoUri != null) Icons.Default.Photo else Icons.Default.AddAPhoto,
                            contentDescription = "Add Bill Photo",
                            tint = if (uiState.billPhotoUri != null) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onBackground
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // 1. Top Section: Amount & Account Selection
            Spacer(modifier = Modifier.height(16.dp))
            
            // Account Selector
            uiState.selectedAccount?.let { account ->
                OutlinedButton(
                    onClick = { /* TODO: Show account selection bottom sheet */ },
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = MaterialTheme.colorScheme.primary
                    ),
                    modifier = Modifier.padding(bottom = 8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.AccountBalance,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(account.name, style = MaterialTheme.typography.titleSmall)
                    Spacer(modifier = Modifier.width(4.dp))
                    Icon(Icons.Default.ArrowDropDown, contentDescription = null)
                }
            }
            
            // Amount Display
            Text(
                text = if (uiState.amount.isEmpty()) "₹ 0" else "₹ ${uiState.amount}",
                style = MaterialTheme.typography.displayLarge.copy(
                    fontSize = 56.sp,
                    fontWeight = FontWeight.Bold
                ),
                color = MaterialTheme.colorScheme.onBackground
            )

            // Goal Selector (Phase 4)
            if (uiState.savingsGoals.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    contentPadding = PaddingValues(horizontal = 4.dp)
                ) {
                    item {
                        FilterChip(
                            selected = uiState.selectedGoal == null,
                            onClick = { viewModel.selectGoal(null) },
                            label = { Text("No Goal") },
                            leadingIcon = { Icon(Icons.Default.Clear, contentDescription = null, Modifier.size(16.dp)) }
                        )
                    }
                    items(uiState.savingsGoals) { goal ->
                        FilterChip(
                            selected = uiState.selectedGoal?.id == goal.id,
                            onClick = { viewModel.selectGoal(goal) },
                            label = { Text(goal.name) },
                            leadingIcon = { Text(goal.iconEmoji) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Color(android.graphics.Color.parseColor(goal.colorHex)).copy(alpha = 0.2f),
                                selectedLabelColor = Color(android.graphics.Color.parseColor(goal.colorHex))
                            )
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Segmented Pill Toggle
            Row(
                modifier = Modifier
                    .height(48.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .padding(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TypeToggleOption(
                    text = "Expense",
                    isSelected = uiState.type == ActivityType.EXPENSE,
                    selectedColor = Color(0xFFEF4444), // ErrorRed
                    onClick = { viewModel.setType(ActivityType.EXPENSE) },
                    modifier = Modifier.weight(1f)
                )
                TypeToggleOption(
                    text = "Income",
                    isSelected = uiState.type == ActivityType.INCOME,
                    selectedColor = Color(0xFF10B981), // SuccessGreen
                    onClick = { viewModel.setType(ActivityType.INCOME) },
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // 2. Middle Section: Category Grid
            Text(
                text = "Select Category",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.align(Alignment.Start)
            )
            Spacer(modifier = Modifier.height(16.dp))
            
            LazyVerticalGrid(
                columns = GridCells.Fixed(4),
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
            ) {
                items(uiState.categories) { category ->
                    CategoryGridItem(
                        category = category,
                        isSelected = uiState.selectedCategory?.id == category.id,
                        onClick = { viewModel.selectCategory(category) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 3. Bottom Section: Numeric Keypad
            NumericKeypad(
                onNumberClick = { num ->
                    if (uiState.amount.length < 9) { // Limit length
                        viewModel.setAmount(uiState.amount + num)
                    }
                },
                onBackspaceClick = {
                    if (uiState.amount.isNotEmpty()) {
                        viewModel.setAmount(uiState.amount.dropLast(1))
                    }
                },
                onDoneClick = {
                    // Default description if empty
                    if (uiState.description.isEmpty()) {
                        viewModel.setDescription(uiState.selectedCategory?.name ?: "Manual Transaction")
                    }
                    viewModel.saveTransaction()
                },
                isValid = uiState.amount.isNotEmpty() && uiState.selectedCategory != null
            )
            
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
fun TypeToggleOption(
    text: String,
    isSelected: Boolean,
    selectedColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxHeight()
            .clip(RoundedCornerShape(20.dp))
            .background(if (isSelected) selectedColor else Color.Transparent)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = if (isSelected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun CategoryGridItem(
    category: Category,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val scale by animateFloatAsState(if (isSelected) 1.1f else 1f, label = "scale")
    
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.scale(scale)
    ) {
        Box(
            modifier = Modifier
                .size(64.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .border(
                    width = if (isSelected) 2.dp else 0.dp,
                    color = if (isSelected) MaterialTheme.colorScheme.primary else Color.Transparent,
                    shape = CircleShape
                )
                .clickable(onClick = onClick),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = category.icon,
                fontSize = 28.sp
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = category.name,
            style = MaterialTheme.typography.bodySmall,
            color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Normal,
            maxLines = 1,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
fun NumericKeypad(
    onNumberClick: (String) -> Unit,
    onBackspaceClick: () -> Unit,
    onDoneClick: () -> Unit,
    isValid: Boolean
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        val rows = listOf(
            listOf("1", "2", "3"),
            listOf("4", "5", "6"),
            listOf("7", "8", "9"),
            listOf(".", "0", "back")
        )

        rows.forEachIndexed { index, row ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                row.forEach { key ->
                    if (key == "back") {
                        NumpadButton(
                            icon = Icons.Default.Backspace,
                            onClick = onBackspaceClick
                        )
                    } else if (index == 3 && key == ".") {
                         NumpadButton(
                             text = ".",
                             onClick = { onNumberClick(".") }
                         )
                    } else {
                        NumpadButton(
                            text = key,
                            onClick = { onNumberClick(key) }
                        )
                    }
                }
            }
        }
        
        Button(
            onClick = onDoneClick,
            enabled = isValid,
            modifier = Modifier
                .fillMaxWidth()
                .height(64.dp),
            shape = RoundedCornerShape(32.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
                disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Icon(
                imageVector = Icons.Default.Check,
                contentDescription = "Done",
                modifier = Modifier.size(32.dp)
            )
        }
    }
}

@Composable
fun NumpadButton(
    text: String? = null,
    icon: ImageVector? = null,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .size(80.dp)
            .clip(CircleShape)
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = rememberRipple(color = Color.White),
                onClick = onClick
            ),
        contentAlignment = Alignment.Center
    ) {
        if (text != null) {
            Text(
                text = text,
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onBackground,
                fontWeight = FontWeight.SemiBold
            )
        } else if (icon != null) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.size(28.dp)
            )
        }
    }
}
