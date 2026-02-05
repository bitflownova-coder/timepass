package com.bitflow.finance.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.Analytics
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.bitflow.finance.ui.screens.split.SplitDashboardScreen
import com.bitflow.finance.ui.screens.split.GroupDetailScreen
import com.bitflow.finance.ui.screens.split.AddExpenseScreen
import com.bitflow.finance.ui.screens.accounts.AccountsScreen
import com.bitflow.finance.ui.screens.add_transaction.AddTransactionScreen
import com.bitflow.finance.ui.screens.analysis.AnalysisScreen
import com.bitflow.finance.ui.screens.categories.CategoryManagementScreen
import com.bitflow.finance.ui.screens.home.HomeScreen
import com.bitflow.finance.ui.screens.import_statement.ImportStatementScreen
import com.bitflow.finance.ui.screens.invoice.InvoiceGeneratorScreen
import com.bitflow.finance.ui.screens.settings.SettingsScreen
import androidx.navigation.NavType
import androidx.navigation.navArgument
import com.bitflow.finance.ui.screens.transaction_detail.TransactionDetailScreen
import com.bitflow.finance.ui.screens.transactions.TransactionsScreen
import com.bitflow.finance.ui.screens.bitflow.BitflowScreen
import com.bitflow.finance.ui.screens.bitflow.InvoiceRecordsScreen
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Receipt

import com.bitflow.finance.ui.screens.invoice.InvoicePreviewScreen
import com.bitflow.finance.ui.screens.profile.ProfileScreen
import com.bitflow.finance.ui.screens.bitflow.BitflowInsightsScreen
import com.bitflow.finance.ui.screens.goals.SavingsGoalsScreen
import com.bitflow.finance.ui.screens.bills.BillRemindersScreen
import com.bitflow.finance.ui.screens.budget.BudgetScreen
import com.bitflow.finance.ui.screens.templates.TemplatesScreen
import com.bitflow.finance.ui.screens.gst.GstSummaryScreen
import com.bitflow.finance.ui.screens.clients.ClientLedgerScreen
import com.bitflow.finance.ui.screens.reports.PnLScreen
import com.bitflow.finance.ui.screens.tds.TdsTrackerScreen
import com.bitflow.finance.ui.screens.backup.BackupScreen
import com.bitflow.finance.ui.screens.security.DecoyPinScreen
import com.bitflow.finance.ui.screens.analytics.CashFlowScreen
import com.bitflow.finance.ui.screens.analytics.LifestyleInflationScreen
import com.bitflow.finance.ui.screens.analytics.SpendingHeatmapScreen
import com.bitflow.finance.ui.screens.debt.DebtScreen
import com.bitflow.finance.ui.screens.investments.InvestmentScreen
import com.bitflow.finance.ui.screens.tax.TaxHelperScreen
import com.bitflow.finance.ui.screens.tools.ToolsScreen

@Composable

fun FinanceAppNavigation() {
    val navController = rememberNavController()

    val items = listOf(
        Screen.Home,
        Screen.Transactions,
        Screen.Insights,
        Screen.Profile
    )

    Scaffold(
        bottomBar = {
            val navBackStackEntry by navController.currentBackStackEntryAsState()
            val currentDestination = navBackStackEntry?.destination
            val currentRoute = currentDestination?.route
            
            // Hide bottom bar on specific screens
            if (currentRoute != "import" && 
                currentRoute != "categories" &&
                currentRoute != "add_transaction" &&
                currentRoute != "invoice" &&
                currentRoute != "invoice_records" &&
                currentRoute?.startsWith("transaction_detail") != true) {
                NavigationBar(
                    tonalElevation = 0.dp,
                    containerColor = MaterialTheme.colorScheme.surface
                ) {
                    items.forEach { screen ->
                        NavigationBarItem(
                            icon = { 
                                Icon(
                                    imageVector = screen.icon,
                                    contentDescription = screen.label,
                                    modifier = Modifier.size(24.dp)
                                )
                            },
                            label = { 
                                Text(
                                    text = screen.label,
                                    style = MaterialTheme.typography.labelSmall,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                            },
                            selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            alwaysShowLabel = true
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Home.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Home.route) {
                HomeScreen(
                    onAddTransactionClick = { navController.navigate("add_transaction") },
                    onTransactionClick = { activityId ->
                        navController.navigate("transaction_detail/$activityId")
                    },
                    onAnalyticsClick = { navController.navigate(Screen.Insights.route) },
                    onSeeAllTransactionsClick = { navController.navigate(Screen.Transactions.route) },
                    onProfileClick = { navController.navigate(Screen.Profile.route) },
                    onImportClick = { navController.navigate("import") },
                    onGenerateInvoice = { navController.navigate("invoice") },
                    onViewInvoices = { navController.navigate("invoice_records") },
                    onToolsClick = { navController.navigate("tools") }
                )
            }
            composable(Screen.Profile.route) {
                ProfileScreen(
                    onBackClick = { navController.popBackStack() },
                    onSettingsClick = { navController.navigate(Screen.Settings.route) },
                    onAccountsClick = { navController.navigate(Screen.Accounts.route) },
                    onInsightsClick = { navController.navigate(Screen.Insights.route) },
                    onImportClick = { navController.navigate("import") }
                )
            }
            composable("savings_goals") {
                SavingsGoalsScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("bill_reminders") {
                BillRemindersScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("budget") {
                BudgetScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("templates") {
                TemplatesScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("gst_summary") {
                GstSummaryScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("client_ledger") {
                ClientLedgerScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("pnl_report") {
                PnLScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("tds_tracker") {
                TdsTrackerScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("backup") {
                BackupScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("decoy_pin") {
                DecoyPinScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("cash_forecast") {
                com.bitflow.finance.ui.screens.analytics.CashForecastScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("cash_flow") {
                CashFlowScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("lifestyle_inflation") {
                LifestyleInflationScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("spending_heatmap") {
                SpendingHeatmapScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("debt_tracker") {
                DebtScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("investment_tracker") {
                InvestmentScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("tax_helper") {
                TaxHelperScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("tools") {
                ToolsScreen(
                    onBackClick = { navController.popBackStack() },
                    onNavigate = { route -> navController.navigate(route) }
                )
            }
            composable("currency_converter") {
                // Placeholder for Currency Converter
                androidx.compose.material3.Text("Currency Converter Coming Soon")
            }
            composable("receipt_scanner") {
                // Placeholder for Receipt Scanner
                androidx.compose.material3.Text("Receipt Scanner Coming Soon")
            }
            composable(Screen.Accounts.route) {
                AccountsScreen()
            }
            
            // Expense Split Feature
            composable("expense_split") {
                SplitDashboardScreen(
                    onGroupClick = { groupId -> navController.navigate("group_detail/$groupId") },
                    onCreateGroupClick = { /* TODO: Implement Add Group Dialog or Screen */ }
                )
            }
            composable(
                route = "group_detail/{groupId}",
                arguments = listOf(navArgument("groupId") { type = NavType.StringType })
            ) {
                GroupDetailScreen(
                    onBackClick = { navController.popBackStack() },
                    onAddExpenseClick = { groupId -> navController.navigate("add_expense/$groupId") }
                )
            }
            composable(
                route = "add_expense/{groupId}",
                arguments = listOf(navArgument("groupId") { type = NavType.StringType })
            ) {
                AddExpenseScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Bitflow Admin Screen removed/replaced by Business Mode
            // Invoice & Insight routes exposed below

            composable(Screen.Insights.route) {
                AnalysisScreen(
                    onCashForecastClick = { navController.navigate("cash_forecast") }
                )
            }
            composable(Screen.Settings.route) {
                SettingsScreen(
                    onNavigateToCategories = { navController.navigate("categories") }
                )
            }
            composable("import") {
                ImportStatementScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Invoice Routes (Accessible in Business Mode via Home Screen)
            composable("invoice") {
                InvoiceGeneratorScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable("invoice_records") {
                InvoiceRecordsScreen(
                    onBackClick = { navController.popBackStack() },
                    onInvoiceClick = { invoiceId ->
                        navController.navigate("invoice_preview/$invoiceId")
                    }
                )
            }
            composable(
                route = "invoice_preview/{invoiceId}",
                arguments = listOf(navArgument("invoiceId") { type = NavType.LongType })
            ) { backStackEntry ->
                val invoiceId = backStackEntry.arguments?.getLong("invoiceId") ?: 0L
                InvoicePreviewScreen(
                    invoiceId = invoiceId,
                    onBackClick = { navController.popBackStack() }
                )
            }

            composable(Screen.Transactions.route) {
                TransactionsScreen(
                    onBackClick = { navController.popBackStack() },
                    onTransactionClick = { id -> navController.navigate("transaction_detail/$id") }
                )
            }
            composable("add_transaction") {
                AddTransactionScreen(
                    onBackClick = { navController.popBackStack() },
                    onSuccess = { navController.popBackStack() }
                )
            }
            composable("categories") {
                CategoryManagementScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            composable(
                route = "transaction_detail/{transactionId}",
                arguments = listOf(navArgument("transactionId") { type = NavType.LongType })
            ) {
                TransactionDetailScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
        }
    }
}

sealed class Screen(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    object Home : Screen("home", "Home", Icons.Default.Home)
    object Transactions : Screen("transactions", "Transactions", Icons.Default.Receipt)
    object Bitflow : Screen("bitflow", "Bitflow", Icons.Default.Star)
    object Insights : Screen("insights", "Insights", Icons.Default.Analytics)
    object Profile : Screen("profile", "Profile", Icons.Default.Person)
    object Accounts : Screen("accounts", "Accounts", Icons.Default.AccountBalance)
    object Settings : Screen("settings", "Settings", Icons.Default.Settings)
}
