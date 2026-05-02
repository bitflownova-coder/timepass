package com.bitflow.finance.ui.screens.tax

import com.bitflow.finance.ui.theme.AppColors
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.Activity

import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaxHelperScreen(
    onBackClick: () -> Unit,
    viewModel: TaxHelperViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("80C Tax Helper") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = AppColors.Surface)
            )
        },
        containerColor = AppColors.Background
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            // Summary Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                colors = CardDefaults.cardColors(containerColor = AppColors.Surface),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Section 80C Limit", style = MaterialTheme.typography.titleMedium)
                        Icon(Icons.Default.Info, contentDescription = "Info", tint = AppColors.TextSecondary)
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text("Invested: ₹${String.format("%,.0f", uiState.totalTaxSavingInvestments)}", style = MaterialTheme.typography.headlineMedium, color = AppColors.Primary)
                    Text("Limit: ₹${String.format("%,.0f", uiState.limit)}", style = MaterialTheme.typography.bodyMedium, color = AppColors.TextSecondary)
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    LinearProgressIndicator(
                        progress = uiState.progress,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(8.dp),
                        color = if (uiState.progress >= 1f) AppColors.Income else AppColors.Primary,
                        trackColor = AppColors.Background,
                        strokeCap = StrokeCap.Round
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Text(
                        if (uiState.remainingLimit > 0) 
                            "You can still invest ₹${String.format("%,.0f", uiState.remainingLimit)} to save tax."
                        else 
                            "Limit reached! Great job.",
                        style = MaterialTheme.typography.bodySmall,
                        color = if (uiState.remainingLimit > 0) AppColors.TextSecondary else AppColors.Income
                    )
                }
            }

            // Transactions List
            Text(
                "Tax Saving Transactions",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )

            LazyColumn(
                contentPadding = PaddingValues(bottom = 16.dp)
            ) {
                items(uiState.transactions) { activity ->
                    ActivityItem(activity)
                }
            }
        }
    }
}

@Composable
fun ActivityItem(activity: Activity) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
        colors = CardDefaults.cardColors(containerColor = AppColors.Surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(activity.description.ifEmpty { "Tax Saving Transaction" }, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold)
                Text(activity.activityDate.format(DateTimeFormatter.ofPattern("dd MMM yyyy")), style = MaterialTheme.typography.bodySmall, color = AppColors.TextSecondary)
            }
            Text("₹${String.format("%,.0f", activity.amount)}", style = MaterialTheme.typography.titleMedium, color = AppColors.TextPrimary)
        }
    }
}
