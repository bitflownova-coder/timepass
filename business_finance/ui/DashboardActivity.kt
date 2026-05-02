package com.bitflow.finance.ui

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Analytics
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.AttachMoney
import androidx.compose.material.icons.filled.BugReport
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Token
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.bitflow.finance.core.theme.FinanceAppTheme

class DashboardActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            FinanceAppTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    DashboardScreen(
                        onFinanceClick = {
                            startActivity(Intent(this, MainActivity::class.java))
                        },
                        onCrawlerClick = {
                             startActivity(Intent(this, CrawlerActivity::class.java))
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun DashboardScreen(onFinanceClick: () -> Unit, onCrawlerClick: () -> Unit) {
    Scaffold(
        topBar = {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Default.Token, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    }
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Bitflow Nova",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                
                Row(verticalAlignment = Alignment.CenterVertically) {
                     IconButton(onClick = {}) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings", tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.surfaceVariant), // Placeholder for Avatar
                         contentAlignment = Alignment.Center   
                    ) {
                         Icon(Icons.Default.Person, contentDescription = "Profile", tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        },
        bottomBar = {
             NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface,
                tonalElevation = 0.dp
             ) {
                 NavigationBarItem(
                     selected = true,
                     onClick = {},
                     icon = { Icon(Icons.Default.GridView, contentDescription = null) },
                     label = { Text("Apps") },
                     colors = NavigationBarItemDefaults.colors(
                         selectedIconColor = MaterialTheme.colorScheme.primary,
                         selectedTextColor = MaterialTheme.colorScheme.primary,
                         indicatorColor = MaterialTheme.colorScheme.surface // No pill background
                     )
                 )
                 NavigationBarItem(
                     selected = false,
                     onClick = {},
                     icon = { Icon(Icons.Default.Notifications, contentDescription = null) },
                     label = { Text("Alerts") }
                 )
                 NavigationBarItem(
                     selected = false,
                     onClick = {},
                     icon = { Icon(Icons.Default.Person, contentDescription = null) },
                     label = { Text("Profile") }
                 )
             }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))
            
            // Headline
            Text(
                buildAnnotatedString {
                    append("Welcome to\n")
                    withStyle(style = SpanStyle(color = MaterialTheme.colorScheme.primary)) {
                        append("Bitflow Nova")
                    }
                },
                style = MaterialTheme.typography.headlineMedium.copy(
                    fontWeight = FontWeight.Bold,
                    lineHeight = 40.sp
                )
            )
            Text(
                text = "Select a tool below to access your workspace.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp, bottom = 32.dp)
            )

            // Cards
            Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                StitchAppCard(
                    title = "Finance Manager",
                    description = "Manage cashflow, audit logs, and track quarterly revenue.",
                    icon = Icons.Default.AttachMoney,
                    themeColor = MaterialTheme.colorScheme.primary,
                    onClick = onFinanceClick
                )

                StitchAppCard(
                    title = "Website Crawler",
                    description = "Real-time SEO analysis, uptime monitoring & bug detection.",
                    icon = Icons.Default.BugReport,
                    themeColor = MaterialTheme.colorScheme.secondary, // Emerald
                    onClick = onCrawlerClick
                )
                
                // Placeholder Analytics Card
                 StitchAppCard(
                    title = "Global Analytics",
                    description = "View suite-wide performance (Coming Soon)",
                    icon = Icons.Default.Analytics,
                    themeColor = Color(0xFFA855F7), // Purple
                    onClick = {},
                    enabled = false
                )
            }
        }
    }
}

@Composable
fun StitchAppCard(
    title: String,
    description: String,
    icon: ImageVector,
    themeColor: Color,
    onClick: () -> Unit,
    enabled: Boolean = true
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.padding(24.dp),
                verticalAlignment = Alignment.Top
            ) {
                // Icon Box
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(RoundedCornerShape(16.dp))
                        .background(themeColor.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = if(enabled) themeColor else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(modifier = Modifier.width(16.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = description,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                         lineHeight = 20.sp
                    )
                }

                if (enabled) {
                    Icon(
                        imageVector = Icons.Default.ArrowForward,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Decorative Bottom Bar
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .background(MaterialTheme.colorScheme.surfaceVariant) // Base grey track
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth(0.3f)
                        .fillMaxHeight()
                        .background(
                            if(enabled) themeColor.copy(alpha = 0.5f) else Color.Transparent, 
                            shape = RoundedCornerShape(topEnd = 4.dp, bottomEnd = 4.dp)
                        )
                )
            }
        }
    }
}
