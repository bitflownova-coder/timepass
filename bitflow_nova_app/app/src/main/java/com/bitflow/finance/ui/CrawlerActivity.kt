package com.bitflow.finance.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bitflow.finance.core.theme.FinanceAppTheme
import com.bitflow.finance.ui.screens.crawler.CrawlerDashboardScreen
import com.bitflow.finance.ui.screens.crawler.CrawlerDetailScreen
import com.bitflow.finance.ui.screens.crawler.CrawlerViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class CrawlerActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            FinanceAppTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()
                    val viewModel: CrawlerViewModel = hiltViewModel()

                    NavHost(navController = navController, startDestination = "dashboard") {
                        composable("dashboard") {
                            CrawlerDashboardScreen(viewModel, navController)
                        }
                        composable("helper_crawl_detail/{sessionId}") { backStackEntry ->
                            val sessionId = backStackEntry.arguments?.getString("sessionId")?.toLongOrNull() ?: 0L
                            CrawlerDetailScreen(viewModel, navController, sessionId)
                        }
                    }
                }
            }
        }
    }
}
