package com.bitflow.finance.ui.screens.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.outlined.AttachMoney
import androidx.compose.material.icons.outlined.Category
import androidx.compose.material.icons.outlined.Fingerprint
import androidx.compose.material.icons.outlined.Palette
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.repository.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository,
    private val backupRepository: com.bitflow.finance.data.repository.BackupRepository
) : ViewModel() {

    val uiState: StateFlow<SettingsUiState> = combine(
        settingsRepository.currencySymbol,
        settingsRepository.isPrivacyModeEnabled,
        settingsRepository.isBiometricEnabled
    ) { currency, isPrivacyMode, isBiometricEnabled ->
        SettingsUiState(
            currencySymbol = currency,
            isPrivacyMode = isPrivacyMode,
            isBiometricEnabled = isBiometricEnabled
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = SettingsUiState()
    )

    fun setCurrency(symbol: String) {
        viewModelScope.launch {
            settingsRepository.setCurrencySymbol(symbol)
        }
    }

    fun setPrivacyMode(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepository.setPrivacyMode(enabled)
        }
    }

    fun setBiometricEnabled(enabled: Boolean) {
        viewModelScope.launch {
            settingsRepository.setBiometricEnabled(enabled)
        }
    }
    
    fun exportData(uri: android.net.Uri, onSuccess: () -> Unit, onError: (String) -> Unit) {
        viewModelScope.launch {
            backupRepository.exportData(uri)
                .onSuccess { onSuccess() }
                .onFailure { onError(it.message ?: "Export failed") }
        }
    }

    fun importData(uri: android.net.Uri, onSuccess: () -> Unit, onError: (String) -> Unit) {
        viewModelScope.launch {
            backupRepository.importData(uri)
                .onSuccess { onSuccess() }
                .onFailure { onError(it.message ?: "Import failed") }
        }
    }
}

data class SettingsUiState(
    val currencySymbol: String = "₹",
    val isPrivacyMode: Boolean = false,
    val isBiometricEnabled: Boolean = false
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel = hiltViewModel(),
    onNavigateToCategories: () -> Unit = {}
) {
    val uiState by viewModel.uiState.collectAsState()
    var showCurrencyDialog by remember { mutableStateOf(false) }

    if (showCurrencyDialog) {
        CurrencySelectionDialog(
            currentCurrency = uiState.currencySymbol,
            onCurrencySelected = {
                viewModel.setCurrency(it)
                showCurrencyDialog = false
            },
            onDismiss = { showCurrencyDialog = false }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        "Settings",
                        fontWeight = FontWeight.Bold
                    ) 
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp)
        ) {
            // Zero Cloud Badge - Privacy Trust Section
            ZeroCloudBadge()
            
            Spacer(modifier = Modifier.height(24.dp))
            
            SettingsSection(title = "General") {
                SettingsItem(
                    icon = Icons.Outlined.Category,
                    title = "Manage Categories",
                    subtitle = "Edit, merge, or hide categories",
                    onClick = onNavigateToCategories
                )
                SettingsItem(
                    icon = Icons.Outlined.AttachMoney,
                    title = "Currency",
                    subtitle = uiState.currencySymbol,
                    onClick = { showCurrencyDialog = true }
                )
                SettingsItem(
                    icon = Icons.Outlined.Security,
                    title = "Privacy Mode",
                    subtitle = "Hide balances by default",
                    trailing = {
                        Switch(
                            checked = uiState.isPrivacyMode,
                            onCheckedChange = { viewModel.setPrivacyMode(it) }
                        )
                    }
                )
                SettingsItem(
                    icon = Icons.Outlined.Fingerprint,
                    title = "Biometric Lock",
                    subtitle = "Require fingerprint on app start",
                    trailing = {
                        Switch(
                            checked = uiState.isBiometricEnabled,
                            onCheckedChange = { viewModel.setBiometricEnabled(it) }
                        )
                    }
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            val context = androidx.compose.ui.platform.LocalContext.current
            val createDocumentLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
                androidx.activity.result.contract.ActivityResultContracts.CreateDocument("application/json")
            ) { uri ->
                uri?.let {
                    viewModel.exportData(it, 
                        onSuccess = { 
                            android.widget.Toast.makeText(context, "Backup successful!", android.widget.Toast.LENGTH_SHORT).show() 
                        },
                        onError = { msg ->
                            android.widget.Toast.makeText(context, "Backup failed: $msg", android.widget.Toast.LENGTH_SHORT).show()
                        }
                    )
                }
            }

            val openDocumentLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
                androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
            ) { uri ->
                uri?.let {
                    viewModel.importData(it,
                        onSuccess = { 
                            android.widget.Toast.makeText(context, "Restore successful!", android.widget.Toast.LENGTH_SHORT).show() 
                        },
                        onError = { msg ->
                            android.widget.Toast.makeText(context, "Restore failed: $msg", android.widget.Toast.LENGTH_SHORT).show()
                        }
                    )
                }
            }

            SettingsSection(title = "Data Management") {
                SettingsItem(
                    icon = Icons.Filled.CloudUpload,
                    title = "Backup Data",
                    subtitle = "Export your data to a JSON file",
                    onClick = { 
                        createDocumentLauncher.launch("finance_app_backup_${System.currentTimeMillis()}.json") 
                    }
                )
                SettingsItem(
                    icon = Icons.Filled.CloudDownload,
                    title = "Restore Data",
                    subtitle = "Import data from a backup file",
                    onClick = { 
                        openDocumentLauncher.launch(arrayOf("application/json"))
                    }
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
            
            SettingsSection(title = "Appearance") {
                SettingsItem(
                    icon = Icons.Outlined.Palette,
                    title = "Theme",
                    subtitle = "System Default",
                    onClick = { /* TODO */ }
                )
            }
        }
    }
}

@Composable
fun ZeroCloudBadge() {
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = androidx.compose.ui.graphics.Color(0xFF10B981).copy(alpha = 0.15f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("🔒", style = MaterialTheme.typography.headlineLarge)
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "Zero Cloud",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = androidx.compose.ui.graphics.Color(0xFF10B981)
                )
                Text(
                    "Your data never leaves this device. We don't have servers.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun SettingsSection(
    title: String,
    content: @Composable () -> Unit
) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 8.dp, start = 4.dp)
        )
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
        ) {
            Column {
                content()
            }
        }
    }
}

@Composable
fun SettingsItem(
    icon: ImageVector,
    title: String,
    subtitle: String? = null,
    trailing: @Composable (() -> Unit)? = null,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = onClick != null, onClick = onClick ?: {})
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title, 
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium
            )
            if (subtitle != null) {
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        if (trailing != null) {
            trailing()
        } else if (onClick != null) {
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}


@Composable
fun CurrencySelectionDialog(
    currentCurrency: String,
    onCurrencySelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val currencies = listOf("₹", "$", "€", "£", "¥")
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Select Currency") },
        text = {
            Column {
                currencies.forEach { currency ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onCurrencySelected(currency) }
                            .padding(vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = (currency == currentCurrency),
                            onClick = { onCurrencySelected(currency) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = currency)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
