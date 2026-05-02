package com.bitflow.finance.ui.screens.home

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.domain.model.AppMode

@Composable
fun HomeScreen(
    onAddTransactionClick: () -> Unit,
    onTransactionClick: (Long) -> Unit,
    onAnalyticsClick: () -> Unit,
    onSeeAllTransactionsClick: () -> Unit,
    onProfileClick: () -> Unit,
    onImportClick: () -> Unit = {},
    onGenerateInvoice: () -> Unit = {},
    onViewInvoices: () -> Unit = {},
    onToolsClick: () -> Unit = {},
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    if (uiState.appMode == AppMode.BUSINESS) {
        BusinessDashboardScreen(
            currentMode = uiState.appMode,
            onModeChange = { viewModel.setAppMode(it) },
            onGenerateInvoice = onGenerateInvoice,
            onAddExpense = onAddTransactionClick,
            onViewInvoices = onViewInvoices
        )
    } else {
        DailyPulseHomeScreen(
            currentMode = uiState.appMode,
            onModeChange = { viewModel.setAppMode(it) },
            onAddActivityClick = onAddTransactionClick,
            onActivityClick = onTransactionClick,
            onImportClick = onImportClick,
            onAnalyticsClick = onAnalyticsClick,
            onToolsClick = onToolsClick
        )
    }
}
