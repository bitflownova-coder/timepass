package com.bitflow.finance.ui.screens.dev_tools

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

data class DevTool(
    val name: String,
    val description: String,
    val icon: ImageVector,
    val color: Color,
    val route: String
)

val devTools = listOf(
    DevTool(
        name = "Time Tracker",
        description = "Track time on projects & tasks",
        icon = Icons.Default.Timer,
        color = Color(0xFF10B981),
        route = "time_tracker"
    ),
    DevTool(
        name = "Quick Notes",
        description = "Jot down ideas & snippets",
        icon = Icons.Default.Note,
        color = Color(0xFF8B5CF6),
        route = "quick_notes"
    ),
    DevTool(
        name = "Color Converter",
        description = "Convert HEX, RGB, HSL colors",
        icon = Icons.Default.Palette,
        color = Color(0xFFF59E0B),
        route = "color_converter"
    ),
    DevTool(
        name = "Password Generator",
        description = "Create secure passwords",
        icon = Icons.Default.Key,
        color = Color(0xFFEF4444),
        route = "password_generator"
    ),
    DevTool(
        name = "QR Generator",
        description = "Create QR codes for URLs & more",
        icon = Icons.Default.QrCode,
        color = Color(0xFF3B82F6),
        route = "qr_generator"
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DevToolsDashboard(
    onBackClick: () -> Unit,
    onToolClick: (String) -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Column {
                        Text("Developer Tools", fontWeight = FontWeight.Bold)
                        Text(
                            "Utilities for everyday coding",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(devTools) { tool ->
                DevToolCard(
                    tool = tool,
                    onClick = { onToolClick(tool.route) }
                )
            }
        }
    }
}

@Composable
private fun DevToolCard(
    tool: DevTool,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1f)
            .clickable { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = tool.color.copy(alpha = 0.1f)
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Surface(
                modifier = Modifier.size(56.dp),
                shape = RoundedCornerShape(12.dp),
                color = tool.color.copy(alpha = 0.2f)
            ) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = tool.icon,
                        contentDescription = tool.name,
                        modifier = Modifier.size(32.dp),
                        tint = tool.color
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Text(
                text = tool.name,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                color = tool.color
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = tool.description,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                maxLines = 2
            )
        }
    }
}
