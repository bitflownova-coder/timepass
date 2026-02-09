package com.bitflow.finance.ui.screens.tools

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Calculate
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.CurrencyExchange
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.MoneyOff
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material.icons.filled.AccountBalanceWallet
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.bitflow.finance.ui.theme.AppColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ToolsScreen(
    onBackClick: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Financial Tools") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = AppColors.Surface
                )
            )
        },
        containerColor = AppColors.Background
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            ToolItem(
                title = "Simple Finance",
                subtitle = "Clients, Income, Expenses & Invoice",
                icon = Icons.Default.AccountBalanceWallet,
                onClick = { onNavigate("simple_finance") }
            )
            ToolItem(
                title = "Debt Snowball",
                subtitle = "Track payoffs & become debt-free",
                icon = Icons.Default.MoneyOff,
                onClick = { onNavigate("debt_tracker") }
            )
            ToolItem(
                title = "Investment Portfolio",
                subtitle = "Track Net Worth & Assets",
                icon = Icons.Default.TrendingUp,
                onClick = { onNavigate("investment_tracker") }
            )
            ToolItem(
                title = "Expense Split",
                subtitle = "Share costs with friends",
                icon = Icons.Default.Group,
                onClick = { onNavigate("expense_split") }
            )
            ToolItem(
                title = "Tax Helper (80C)",
                subtitle = "Maximize tax savings",
                icon = Icons.Default.Calculate,
                onClick = { onNavigate("tax_helper") }
            )
            ToolItem(
                title = "Currency Converter",
                subtitle = "Live exchange rates",
                icon = Icons.Default.CurrencyExchange,
                onClick = { onNavigate("currency_converter") }
            )
            ToolItem(
                title = "Receipt Scanner",
                subtitle = "Auto-log from photos",
                icon = Icons.Default.CameraAlt,
                onClick = { onNavigate("receipt_scanner") }
            )
        }
    }
}

@Composable
fun ToolItem(
    title: String,
    subtitle: String,
    icon: ImageVector,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = AppColors.Surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = AppColors.Primary,
                modifier = Modifier.size(32.dp)
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
            }
        }
    }
}
