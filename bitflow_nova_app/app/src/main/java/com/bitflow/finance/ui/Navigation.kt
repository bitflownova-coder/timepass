package com.bitflow.finance.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
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
import androidx.navigation.NavType
import androidx.navigation.navArgument
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.ui.screens.crawler.CrawlerDashboardScreen
import com.bitflow.finance.ui.screens.crawler.CrawlerViewModel
import com.bitflow.finance.ui.screens.simple_finance.SimpleFinanceDashboard
import com.bitflow.finance.ui.screens.simple_finance.ClientsScreen
import com.bitflow.finance.ui.screens.simple_finance.IncomeScreen
import com.bitflow.finance.ui.screens.simple_finance.ExpenseScreen
import com.bitflow.finance.ui.screens.simple_finance.SimpleInvoiceScreen
import com.bitflow.finance.ui.screens.simple_finance.ReportsScreen
import com.bitflow.finance.ui.screens.settings.SettingsScreen
import com.bitflow.finance.ui.screens.dev_tools.DevToolsDashboard
import com.bitflow.finance.ui.screens.dev_tools.TimeTrackerScreen
import com.bitflow.finance.ui.screens.dev_tools.QuickNotesScreen
import com.bitflow.finance.ui.screens.dev_tools.ColorConverterScreen
import com.bitflow.finance.ui.screens.dev_tools.PasswordGeneratorScreen
import com.bitflow.finance.ui.screens.dev_tools.QRCodeGeneratorScreen

@Composable
fun FinanceAppNavigation() {
    val navController = rememberNavController()

    val items = listOf(
        Screen.Home,
        Screen.Clients,
        Screen.Income,
        Screen.Expenses,
        Screen.Crawler,
        Screen.DevTools
    )

    Scaffold(
        bottomBar = {
            val navBackStackEntry by navController.currentBackStackEntryAsState()
            val currentDestination = navBackStackEntry?.destination
            val currentRoute = currentDestination?.route
            
            // Hide bottom bar on detail/form screens
            val hideBottomBar = currentRoute?.startsWith("simple_invoice") == true ||
                currentRoute == "settings" ||
                currentRoute?.startsWith("time_tracker") == true ||
                currentRoute?.startsWith("quick_notes") == true ||
                currentRoute?.startsWith("color_converter") == true ||
                currentRoute?.startsWith("password_generator") == true ||
                currentRoute?.startsWith("qr_generator") == true ||
                currentRoute == "reports"
            
            if (!hideBottomBar) {
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
            // Main Dashboard
            composable(Screen.Home.route) {
                SimpleFinanceDashboard(
                    onNavigateToClients = { navController.navigate(Screen.Clients.route) },
                    onNavigateToIncome = { navController.navigate(Screen.Income.route) },
                    onNavigateToExpenses = { navController.navigate(Screen.Expenses.route) },
                    onNavigateToInvoice = { paymentId ->
                        if (paymentId != null) {
                            navController.navigate("simple_invoice?paymentId=$paymentId")
                        } else {
                            navController.navigate("simple_invoice?paymentId=-1")
                        }
                    },
                    onNavigateToReports = { navController.navigate(Screen.Reports.route) }
                )
            }
            
            // Clients Screen
            composable(Screen.Clients.route) {
                ClientsScreen(
                    onBackClick = { navController.popBackStack() },
                    onClientClick = { /* Client details not needed for simple flow */ }
                )
            }
            
            // Income Screen
            composable(Screen.Income.route) {
                IncomeScreen(
                    onBackClick = { navController.popBackStack() },
                    onGenerateInvoice = { paymentId ->
                        navController.navigate("simple_invoice?paymentId=$paymentId")
                    }
                )
            }
            
            // Expenses Screen
            composable(Screen.Expenses.route) {
                ExpenseScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Reports Screen
            composable(Screen.Reports.route) {
                ReportsScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Invoice Generator
            composable(
                route = "simple_invoice?paymentId={paymentId}",
                arguments = listOf(navArgument("paymentId") { 
                    type = NavType.LongType
                    defaultValue = -1L 
                })
            ) { backStackEntry ->
                val paymentId = backStackEntry.arguments?.getLong("paymentId")?.takeIf { it > 0 }
                SimpleInvoiceScreen(
                    paymentId = paymentId,
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Settings
            composable("settings") {
                SettingsScreen(
                    onNavigateToCategories = { /* Categories removed in simple finance */ }
                )
            }
            
            // Crawler Dashboard
            composable(Screen.Crawler.route) {
                val crawlerViewModel = hiltViewModel<CrawlerViewModel>()
                CrawlerDashboardScreen(
                    viewModel = crawlerViewModel,
                    navController = navController
                )
            }

            // DevTools Dashboard
            composable(Screen.DevTools.route) {
                DevToolsDashboard(
                    onBackClick = { navController.popBackStack() },
                    onToolClick = { route -> navController.navigate(route) }
                )
            }
            
            // Time Tracker
            composable("time_tracker") {
                TimeTrackerScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Quick Notes
            composable("quick_notes") {
                QuickNotesScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Color Converter
            composable("color_converter") {
                ColorConverterScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // Password Generator
            composable("password_generator") {
                PasswordGeneratorScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
            
            // QR Code Generator
            composable("qr_generator") {
                QRCodeGeneratorScreen(
                    onBackClick = { navController.popBackStack() }
                )
            }
        }
    }
}

sealed class Screen(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    object Home : Screen("home", "Home", Icons.Default.Home)
    object Clients : Screen("clients", "Clients", Icons.Default.People)
    object Income : Screen("income", "Income", Icons.Default.AttachMoney)
    object Expenses : Screen("expenses", "Expenses", Icons.Default.ShoppingCart)
    object Reports : Screen("reports", "Reports", Icons.Default.Analytics)
    object Crawler : Screen("crawler_dashboard", "Crawler", Icons.Default.BugReport)
    object DevTools : Screen("dev_tools", "Tools", Icons.Default.Build)
}
