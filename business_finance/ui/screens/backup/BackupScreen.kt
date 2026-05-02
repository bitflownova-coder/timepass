package com.bitflow.finance.ui.screens.backup

import android.content.Context
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.bitflow.finance.util.BackupManager
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BackupScreen(
    onBackClick: () -> Unit = {}
) {
    val context = LocalContext.current
    var showBackupDialog by remember { mutableStateOf(false) }
    var showRestoreDialog by remember { mutableStateOf(false) }
    var backupPassword by remember { mutableStateOf("") }
    var restorePassword by remember { mutableStateOf("") }
    var selectedBackupFile by remember { mutableStateOf<File?>(null) }
    var isProcessing by remember { mutableStateOf(false) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let {
            val inputStream = context.contentResolver.openInputStream(it)
            val tempFile = File(context.cacheDir, "restore_temp.bak")
            inputStream?.use { input ->
                tempFile.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            selectedBackupFile = tempFile
            showRestoreDialog = true
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Backup & Restore", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Privacy Notice
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF3B82F6).copy(alpha = 0.15f)
                )
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("🔐", style = MaterialTheme.typography.headlineMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Encrypted Backup",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Your backup is encrypted with AES-256. Only you can decrypt it with your password.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Create Backup Button
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                onClick = { showBackupDialog = true }
            ) {
                Row(
                    modifier = Modifier.padding(20.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.CloudUpload,
                        contentDescription = null,
                        tint = Color(0xFF10B981),
                        modifier = Modifier.size(40.dp)
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Create Backup", fontWeight = FontWeight.Bold)
                        Text(
                            "Export encrypted .bak file",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.Gray
                        )
                    }
                }
            }

            // Restore Backup Button
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                onClick = { filePicker.launch("*/*") }
            ) {
                Row(
                    modifier = Modifier.padding(20.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.CloudDownload,
                        contentDescription = null,
                        tint = Color(0xFF3B82F6),
                        modifier = Modifier.size(40.dp)
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Restore Backup", fontWeight = FontWeight.Bold)
                        Text(
                            "Import from .bak file",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color.Gray
                        )
                    }
                }
            }
        }
    }

    // Create Backup Dialog
    if (showBackupDialog) {
        AlertDialog(
            onDismissRequest = { showBackupDialog = false },
            title = { Text("Create Encrypted Backup") },
            text = {
                Column {
                    Text("Enter a password to encrypt your backup:")
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = backupPassword,
                        onValueChange = { backupPassword = it },
                        label = { Text("Password") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (backupPassword.length >= 6) {
                            isProcessing = true
                            val result = BackupManager.createEncryptedBackup(context, backupPassword)
                            isProcessing = false
                            if (result.success) {
                                Toast.makeText(context, "Backup saved: ${result.filePath}", Toast.LENGTH_LONG).show()
                            } else {
                                Toast.makeText(context, "Error: ${result.error}", Toast.LENGTH_SHORT).show()
                            }
                            showBackupDialog = false
                            backupPassword = ""
                        }
                    },
                    enabled = backupPassword.length >= 6
                ) { Text("Create") }
            },
            dismissButton = {
                TextButton(onClick = { showBackupDialog = false; backupPassword = "" }) {
                    Text("Cancel")
                }
            }
        )
    }

    // Restore Backup Dialog
    if (showRestoreDialog && selectedBackupFile != null) {
        AlertDialog(
            onDismissRequest = { showRestoreDialog = false },
            title = { Text("Restore Backup") },
            text = {
                Column {
                    Text("Enter the password used to encrypt this backup:")
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = restorePassword,
                        onValueChange = { restorePassword = it },
                        label = { Text("Password") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "⚠️ This will replace all current data!",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFFEF4444)
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (restorePassword.isNotEmpty()) {
                            isProcessing = true
                            val result = BackupManager.restoreFromBackup(
                                context,
                                selectedBackupFile!!,
                                restorePassword
                            )
                            isProcessing = false
                            if (result.success) {
                                Toast.makeText(context, "Restore successful! Please restart the app.", Toast.LENGTH_LONG).show()
                            } else {
                                Toast.makeText(context, "Error: ${result.error}", Toast.LENGTH_SHORT).show()
                            }
                            showRestoreDialog = false
                            restorePassword = ""
                        }
                    },
                    enabled = restorePassword.isNotEmpty()
                ) { Text("Restore") }
            },
            dismissButton = {
                TextButton(onClick = { showRestoreDialog = false; restorePassword = "" }) {
                    Text("Cancel")
                }
            }
        )
    }
}
