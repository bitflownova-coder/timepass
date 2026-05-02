package com.bitflow.finance.ui.screens.security

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.bitflow.finance.util.DecoyPinManager

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DecoyPinScreen(
    onBackClick: () -> Unit = {}
) {
    val context = LocalContext.current
    val decoyPinManager = remember { DecoyPinManager(context) }
    var isEnabled by remember { mutableStateOf(decoyPinManager.isDecoyEnabled()) }
    var showSetupDialog by remember { mutableStateOf(false) }
    var newPin by remember { mutableStateOf("") }
    var confirmPin by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Decoy PIN", fontWeight = FontWeight.Bold) },
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
            // Explanation Card
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFFF59E0B).copy(alpha = 0.15f)
                )
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("🕵️", style = MaterialTheme.typography.headlineMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Panic Mode Protection",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Set a secondary PIN that shows an empty app state. If someone forces you to unlock, use this decoy PIN.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Enable/Disable Toggle
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Decoy PIN", fontWeight = FontWeight.Bold)
                        Text(
                            if (isEnabled) "Enabled" else "Disabled",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (isEnabled) Color(0xFF10B981) else Color.Gray
                        )
                    }
                    Switch(
                        checked = isEnabled,
                        onCheckedChange = { enabled ->
                            if (enabled) {
                                showSetupDialog = true
                            } else {
                                decoyPinManager.removeDecoyPin()
                                isEnabled = false
                                Toast.makeText(context, "Decoy PIN disabled", Toast.LENGTH_SHORT).show()
                            }
                        }
                    )
                }
            }

            if (isEnabled) {
                // Change PIN Button
                OutlinedButton(
                    onClick = { showSetupDialog = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Change Decoy PIN")
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Warning
            Text(
                "⚠️ Make sure your decoy PIN is different from your primary PIN/biometric.",
                style = MaterialTheme.typography.bodySmall,
                color = Color.Gray
            )
        }
    }

    // Setup Dialog
    if (showSetupDialog) {
        AlertDialog(
            onDismissRequest = { showSetupDialog = false; newPin = ""; confirmPin = "" },
            title = { Text("Set Decoy PIN") },
            text = {
                Column {
                    Text("This PIN will show an empty app when used.")
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = newPin,
                        onValueChange = { if (it.length <= 6) newPin = it },
                        label = { Text("Enter PIN (4-6 digits)") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = confirmPin,
                        onValueChange = { if (it.length <= 6) confirmPin = it },
                        label = { Text("Confirm PIN") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (newPin.length >= 4 && newPin == confirmPin) {
                            decoyPinManager.setDecoyPin(newPin)
                            isEnabled = true
                            Toast.makeText(context, "Decoy PIN set successfully", Toast.LENGTH_SHORT).show()
                            showSetupDialog = false
                            newPin = ""
                            confirmPin = ""
                        } else if (newPin != confirmPin) {
                            Toast.makeText(context, "PINs don't match", Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(context, "PIN must be at least 4 digits", Toast.LENGTH_SHORT).show()
                        }
                    },
                    enabled = newPin.length >= 4 && newPin == confirmPin
                ) { Text("Save") }
            },
            dismissButton = {
                TextButton(onClick = { showSetupDialog = false; newPin = ""; confirmPin = "" }) {
                    Text("Cancel")
                }
            }
        )
    }
}
