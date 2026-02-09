package com.bitflow.finance.ui.screens.dev_tools

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.PasswordHistoryEntity
import java.security.SecureRandom
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PasswordGeneratorScreen(
    viewModel: DevToolsViewModel = hiltViewModel(),
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    val passwordHistory by viewModel.passwordHistory.collectAsState()
    
    var passwordLength by remember { mutableStateOf(16f) }
    var includeUppercase by remember { mutableStateOf(true) }
    var includeLowercase by remember { mutableStateOf(true) }
    var includeNumbers by remember { mutableStateOf(true) }
    var includeSpecial by remember { mutableStateOf(true) }
    var excludeAmbiguous by remember { mutableStateOf(false) }
    var generatedPassword by remember { mutableStateOf("") }
    var passwordType by remember { mutableStateOf("random") } // random, passphrase, pronounceable
    var showHistory by remember { mutableStateOf(false) }
    
    // Generate initial password
    LaunchedEffect(Unit) {
        generatedPassword = generatePassword(
            length = passwordLength.toInt(),
            uppercase = includeUppercase,
            lowercase = includeLowercase,
            numbers = includeNumbers,
            special = includeSpecial,
            excludeAmbiguous = excludeAmbiguous
        )
    }
    
    fun regeneratePassword() {
        generatedPassword = when (passwordType) {
            "passphrase" -> generatePassphrase(4)
            "pronounceable" -> generatePronounceable(passwordLength.toInt())
            else -> generatePassword(
                length = passwordLength.toInt(),
                uppercase = includeUppercase,
                lowercase = includeLowercase,
                numbers = includeNumbers,
                special = includeSpecial,
                excludeAmbiguous = excludeAmbiguous
            )
        }
    }
    
    fun copyToClipboard(text: String) {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("Password", text)
        clipboard.setPrimaryClip(clip)
        Toast.makeText(context, "Password copied!", Toast.LENGTH_SHORT).show()
    }
    
    fun getPasswordStrength(password: String): Pair<String, Color> {
        var score = 0
        if (password.length >= 8) score++
        if (password.length >= 12) score++
        if (password.length >= 16) score++
        if (password.any { it.isUpperCase() }) score++
        if (password.any { it.isLowerCase() }) score++
        if (password.any { it.isDigit() }) score++
        if (password.any { !it.isLetterOrDigit() }) score++
        
        return when {
            score <= 2 -> "Weak" to Color(0xFFEF4444)
            score <= 4 -> "Medium" to Color(0xFFF59E0B)
            score <= 5 -> "Strong" to Color(0xFF10B981)
            else -> "Very Strong" to Color(0xFF059669)
        }
    }
    
    val (strengthText, strengthColor) = getPasswordStrength(generatedPassword)
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Password Generator", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { showHistory = !showHistory }) {
                        Icon(
                            Icons.Default.History,
                            "History",
                            tint = if (showHistory) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            )
        }
    ) { padding ->
        if (showHistory) {
            // History View
            PasswordHistoryView(
                history = passwordHistory,
                onCopy = { copyToClipboard(it) },
                onDelete = { viewModel.deletePasswordFromHistory(it) },
                onClearAll = { viewModel.clearPasswordHistory() },
                modifier = Modifier.padding(padding)
            )
        } else {
            // Generator View
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Generated Password Display
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = generatedPassword,
                                    style = MaterialTheme.typography.titleLarge,
                                    fontFamily = FontFamily.Monospace,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.weight(1f),
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis
                                )
                                
                                Row {
                                    IconButton(onClick = { regeneratePassword() }) {
                                        Icon(Icons.Default.Refresh, "Regenerate")
                                    }
                                    IconButton(onClick = { copyToClipboard(generatedPassword) }) {
                                        Icon(Icons.Default.ContentCopy, "Copy")
                                    }
                                }
                            }
                            
                            Spacer(modifier = Modifier.height(12.dp))
                            
                            // Strength Indicator
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(12.dp)
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(strengthColor)
                                    )
                                    Text(
                                        text = strengthText,
                                        style = MaterialTheme.typography.labelLarge,
                                        color = strengthColor,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                                Text(
                                    text = "${generatedPassword.length} characters",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                                )
                            }
                            
                            // Strength Bar
                            Spacer(modifier = Modifier.height(8.dp))
                            LinearProgressIndicator(
                                progress = when (strengthText) {
                                    "Weak" -> 0.25f
                                    "Medium" -> 0.5f
                                    "Strong" -> 0.75f
                                    else -> 1f
                                },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(6.dp)
                                    .clip(RoundedCornerShape(3.dp)),
                                color = strengthColor,
                                trackColor = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.2f)
                            )
                        }
                    }
                }
                
                // Save to History Button
                item {
                    Button(
                        onClick = {
                            viewModel.savePasswordToHistory(
                                password = generatedPassword,
                                length = generatedPassword.length,
                                type = passwordType,
                                strength = strengthText.lowercase().replace(" ", "_")
                            )
                            Toast.makeText(context, "Saved to history", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.Save, null, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Save to History")
                    }
                }
                
                // Password Type Selection
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text("Password Type", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            
                            SingleChoiceSegmentedButtonRow(
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                SegmentedButton(
                                    selected = passwordType == "random",
                                    onClick = {
                                        passwordType = "random"
                                        regeneratePassword()
                                    },
                                    shape = SegmentedButtonDefaults.itemShape(0, 3)
                                ) {
                                    Text("Random")
                                }
                                SegmentedButton(
                                    selected = passwordType == "passphrase",
                                    onClick = {
                                        passwordType = "passphrase"
                                        regeneratePassword()
                                    },
                                    shape = SegmentedButtonDefaults.itemShape(1, 3)
                                ) {
                                    Text("Passphrase")
                                }
                                SegmentedButton(
                                    selected = passwordType == "pronounceable",
                                    onClick = {
                                        passwordType = "pronounceable"
                                        regeneratePassword()
                                    },
                                    shape = SegmentedButtonDefaults.itemShape(2, 3)
                                ) {
                                    Text("Pronounceable")
                                }
                            }
                        }
                    }
                }
                
                // Options (only for random type)
                if (passwordType == "random") {
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.padding(16.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                Text("Options", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                                
                                // Length Slider
                                Column {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Text("Length")
                                        Text(
                                            "${passwordLength.toInt()}",
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                    Slider(
                                        value = passwordLength,
                                        onValueChange = {
                                            passwordLength = it
                                            regeneratePassword()
                                        },
                                        valueRange = 8f..64f,
                                        steps = 55
                                    )
                                }
                                
                                HorizontalDivider()
                                
                                // Character Options
                                OptionCheckbox(
                                    label = "Uppercase (A-Z)",
                                    checked = includeUppercase,
                                    onCheckedChange = {
                                        includeUppercase = it
                                        regeneratePassword()
                                    }
                                )
                                
                                OptionCheckbox(
                                    label = "Lowercase (a-z)",
                                    checked = includeLowercase,
                                    onCheckedChange = {
                                        includeLowercase = it
                                        regeneratePassword()
                                    }
                                )
                                
                                OptionCheckbox(
                                    label = "Numbers (0-9)",
                                    checked = includeNumbers,
                                    onCheckedChange = {
                                        includeNumbers = it
                                        regeneratePassword()
                                    }
                                )
                                
                                OptionCheckbox(
                                    label = "Special (!@#\$%^&*)",
                                    checked = includeSpecial,
                                    onCheckedChange = {
                                        includeSpecial = it
                                        regeneratePassword()
                                    }
                                )
                                
                                OptionCheckbox(
                                    label = "Exclude Ambiguous (0O1lI)",
                                    checked = excludeAmbiguous,
                                    onCheckedChange = {
                                        excludeAmbiguous = it
                                        regeneratePassword()
                                    }
                                )
                            }
                        }
                    }
                }
                
                // Bulk Generate
                item {
                    var bulkCount by remember { mutableStateOf(5) }
                    var bulkPasswords by remember { mutableStateOf<List<String>>(emptyList()) }
                    
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Text("Bulk Generate", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                            
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                OutlinedButton(
                                    onClick = { if (bulkCount > 1) bulkCount-- }
                                ) {
                                    Text("-")
                                }
                                
                                Text(
                                    "$bulkCount passwords",
                                    style = MaterialTheme.typography.bodyLarge,
                                    fontWeight = FontWeight.Bold
                                )
                                
                                OutlinedButton(
                                    onClick = { if (bulkCount < 20) bulkCount++ }
                                ) {
                                    Text("+")
                                }
                                
                                Spacer(modifier = Modifier.weight(1f))
                                
                                Button(
                                    onClick = {
                                        bulkPasswords = (1..bulkCount).map {
                                            when (passwordType) {
                                                "passphrase" -> generatePassphrase(4)
                                                "pronounceable" -> generatePronounceable(passwordLength.toInt())
                                                else -> generatePassword(
                                                    length = passwordLength.toInt(),
                                                    uppercase = includeUppercase,
                                                    lowercase = includeLowercase,
                                                    numbers = includeNumbers,
                                                    special = includeSpecial,
                                                    excludeAmbiguous = excludeAmbiguous
                                                )
                                            }
                                        }
                                    }
                                ) {
                                    Text("Generate")
                                }
                            }
                            
                            if (bulkPasswords.isNotEmpty()) {
                                HorizontalDivider()
                                bulkPasswords.forEach { pwd ->
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clickable { copyToClipboard(pwd) }
                                            .padding(vertical = 4.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = pwd,
                                            style = MaterialTheme.typography.bodySmall,
                                            fontFamily = FontFamily.Monospace,
                                            modifier = Modifier.weight(1f),
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis
                                        )
                                        Icon(
                                            Icons.Default.ContentCopy,
                                            null,
                                            modifier = Modifier.size(16.dp),
                                            tint = MaterialTheme.colorScheme.primary
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun OptionCheckbox(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onCheckedChange(!checked) },
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label)
        Checkbox(
            checked = checked,
            onCheckedChange = onCheckedChange
        )
    }
}

@Composable
private fun PasswordHistoryView(
    history: List<PasswordHistoryEntity>,
    onCopy: (String) -> Unit,
    onDelete: (PasswordHistoryEntity) -> Unit,
    onClearAll: () -> Unit,
    modifier: Modifier = Modifier
) {
    val dateFormat = remember { SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault()) }
    
    Column(modifier = modifier) {
        if (history.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "${history.size} saved passwords",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.outline
                )
                TextButton(onClick = onClearAll) {
                    Text("Clear All", color = MaterialTheme.colorScheme.error)
                }
            }
        }
        
        if (history.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        Icons.Default.History,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.outline
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        "No saved passwords",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.outline
                    )
                }
            }
        } else {
            LazyColumn(
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(history, key = { it.id }) { entry ->
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = entry.password,
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontFamily = FontFamily.Monospace,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                                    modifier = Modifier.padding(top = 4.dp)
                                ) {
                                    Text(
                                        text = entry.type.replaceFirstChar { it.uppercase() },
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                    Text(
                                        text = "•",
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                    Text(
                                        text = "${entry.length} chars",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                    Text(
                                        text = "•",
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                    Text(
                                        text = dateFormat.format(Date(entry.createdAt)),
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                }
                            }
                            
                            Row {
                                IconButton(onClick = { onCopy(entry.password) }) {
                                    Icon(
                                        Icons.Default.ContentCopy,
                                        "Copy",
                                        modifier = Modifier.size(20.dp)
                                    )
                                }
                                IconButton(onClick = { onDelete(entry) }) {
                                    Icon(
                                        Icons.Default.Delete,
                                        "Delete",
                                        modifier = Modifier.size(20.dp),
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// Password generation functions
private fun generatePassword(
    length: Int,
    uppercase: Boolean,
    lowercase: Boolean,
    numbers: Boolean,
    special: Boolean,
    excludeAmbiguous: Boolean
): String {
    val uppercaseChars = if (excludeAmbiguous) "ABCDEFGHJKMNPQRSTUVWXYZ" else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    val lowercaseChars = if (excludeAmbiguous) "abcdefghjkmnpqrstuvwxyz" else "abcdefghijklmnopqrstuvwxyz"
    val numberChars = if (excludeAmbiguous) "23456789" else "0123456789"
    val specialChars = "!@#\$%^&*()_+-=[]{}|;:,.<>?"
    
    var charPool = ""
    if (uppercase) charPool += uppercaseChars
    if (lowercase) charPool += lowercaseChars
    if (numbers) charPool += numberChars
    if (special) charPool += specialChars
    
    if (charPool.isEmpty()) charPool = lowercaseChars + numberChars
    
    val random = SecureRandom()
    return (1..length)
        .map { charPool[random.nextInt(charPool.length)] }
        .joinToString("")
}

private val wordList = listOf(
    "apple", "banana", "cherry", "dragon", "eagle", "forest", "garden", "harbor",
    "island", "jungle", "kitchen", "lemon", "mountain", "nature", "ocean", "planet",
    "quantum", "river", "sunset", "thunder", "umbrella", "valley", "window", "yellow",
    "zebra", "anchor", "bridge", "castle", "diamond", "engine", "falcon", "guitar",
    "horizon", "impact", "journey", "kingdom", "lantern", "marble", "needle", "orange",
    "palace", "quartz", "rocket", "silver", "temple", "unique", "violet", "wizard"
)

private fun generatePassphrase(wordCount: Int): String {
    val random = SecureRandom()
    return (1..wordCount)
        .map { wordList[random.nextInt(wordList.size)] }
        .joinToString("-") { it.replaceFirstChar { c -> c.uppercase() } }
}

private fun generatePronounceable(length: Int): String {
    val consonants = "bcdfghjklmnpqrstvwxyz"
    val vowels = "aeiou"
    val random = SecureRandom()
    
    return buildString {
        var useConsonant = random.nextBoolean()
        repeat(length) {
            if (useConsonant) {
                append(consonants[random.nextInt(consonants.length)])
            } else {
                append(vowels[random.nextInt(vowels.length)])
            }
            useConsonant = !useConsonant
        }
    }
}
