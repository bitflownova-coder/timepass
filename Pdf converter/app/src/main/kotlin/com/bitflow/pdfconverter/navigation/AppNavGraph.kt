package com.bitflow.pdfconverter.navigation

import androidx.compose.runtime.Composable

import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.bitflow.pdfconverter.ui.HomeScreen
import com.bitflow.pdfconverter.ui.OnboardingScreen
import com.bitflow.pdfconverter.ui.SettingsScreen
import com.bitflow.pdfconverter.feature.scanner.ui.ScannerScreen
import com.bitflow.pdfconverter.feature.scanner.ui.CropScreen
import com.bitflow.pdfconverter.feature.converter.ui.ConverterScreen
import com.bitflow.pdfconverter.feature.converter.ui.ImageToPdfScreen
import com.bitflow.pdfconverter.feature.converter.ui.MergePdfScreen
import com.bitflow.pdfconverter.feature.converter.ui.OfficeToPdfScreen
import com.bitflow.pdfconverter.feature.converter.ui.SplitPdfScreen
import com.bitflow.pdfconverter.feature.editor.ui.EditorScreen
import com.bitflow.pdfconverter.feature.optimization.ui.OptimizationScreen
import com.bitflow.pdfconverter.feature.security.ui.SecurityScreen
import com.bitflow.pdfconverter.feature.smarttools.ui.SmartToolsScreen
import com.bitflow.pdfconverter.feature.storage.ui.StorageScreen
import com.bitflow.pdfconverter.feature.utility.ui.UtilityScreen
import com.bitflow.pdfconverter.feature.utility.ui.PdfDownloaderScreen

@Composable
fun AppNavGraph(
    navController: NavHostController = rememberNavController(),
    startDestination: String = Screen.Home.route,
    onProfileSaved: (name: String, role: String) -> Unit = { _, _ -> }
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Home.route) {
            HomeScreen(navController = navController)
        }

        // ── Onboarding ───────────────────────────────────────────────────────
        composable(Screen.Onboarding.route) {
            OnboardingScreen(
                onFinished = { name, role ->
                    onProfileSaved(name, role)
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Onboarding.route) { inclusive = true }
                    }
                }
            )
        }

        // ── Settings ─────────────────────────────────────────────────────────
        composable(Screen.Settings.route) {
            SettingsScreen(onNavigateBack = { navController.popBackStack() })
        }

        // ── Scanner ──────────────────────────────────────────────────────────
        composable(Screen.Scanner.route) {
            ScannerScreen(
                onNavigateToCrop = { navController.navigate(Screen.ScannerCrop.route) },
                onNavigateBack = { navController.popBackStack() },
                onPdfExported = { path ->
                    navController.navigate(Screen.Editor.withFile(path))
                }
            )
        }
        composable(Screen.ScannerCrop.route) {
            CropScreen(
                onNavigateBack = { navController.popBackStack() },
                onScanComplete = { navController.navigate(Screen.Home.route) { popUpTo(Screen.Home.route) } }
            )
        }

        // ── Converter ────────────────────────────────────────────────────────
        composable(Screen.Converter.route) {
            ConverterScreen(navController = navController)
        }
        composable(Screen.ImageToPdf.route) {
            ImageToPdfScreen(
                onNavigateBack = { navController.popBackStack() },
                onConversionComplete = { fileUri ->
                    navController.navigate(Screen.Editor.withFile(fileUri))
                }
            )
        }
        composable(Screen.MergePdf.route) {
            MergePdfScreen(
                onNavigateBack = { navController.popBackStack() },
                onMergeComplete = { fileUri ->
                    navController.navigate(Screen.Editor.withFile(fileUri))
                }
            )
        }
        composable(Screen.SplitPdf.route) {
            SplitPdfScreen(
                onNavigateBack = { navController.popBackStack() },
                onSplitComplete = { fileUri ->
                    navController.navigate(Screen.Editor.withFile(fileUri))
                }
            )
        }
        composable(Screen.OfficeToPdf.route) {
            OfficeToPdfScreen(onNavigateBack = { navController.popBackStack() })
        }

        // ── Editor ───────────────────────────────────────────────────────────
        composable(
            route = Screen.Editor.route,
            arguments = listOf(navArgument(Screen.Editor.ARG_FILE_URI) {
                type = NavType.StringType; defaultValue = ""
            })
        ) { backStack ->
            EditorScreen(
                fileUri = backStack.arguments?.getString(Screen.Editor.ARG_FILE_URI) ?: "",
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // ── Optimization ─────────────────────────────────────────────────────
        composable(
            route = Screen.Optimization.route,
            arguments = listOf(navArgument(Screen.Optimization.ARG_FILE_URI) {
                type = NavType.StringType; defaultValue = ""
            })
        ) { backStack ->
            val fileUri = backStack.arguments?.getString(Screen.Optimization.ARG_FILE_URI) ?: ""
            OptimizationScreen(
                fileUri = fileUri,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // ── Security ─────────────────────────────────────────────────────────
        composable(
            route = Screen.Security.route,
            arguments = listOf(
                navArgument(Screen.Security.ARG_FILE_URI) {
                    type = NavType.StringType; defaultValue = ""
                },
                navArgument(Screen.Security.ARG_SECTION) {
                    type = NavType.StringType; defaultValue = ""
                }
            )
        ) { backStack ->
            val fileUri = backStack.arguments?.getString(Screen.Security.ARG_FILE_URI) ?: ""
            val section = backStack.arguments?.getString(Screen.Security.ARG_SECTION) ?: ""
            SecurityScreen(
                fileUri = fileUri,
                initialSection = section,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // ── Smart Tools ──────────────────────────────────────────────────────
        composable(
            route = Screen.SmartTools.route,
            arguments = listOf(
                navArgument(Screen.SmartTools.ARG_SECTION) {
                    type = NavType.StringType; defaultValue = ""
                }
            )
        ) { backStack ->
            val section = backStack.arguments?.getString(Screen.SmartTools.ARG_SECTION) ?: ""
            SmartToolsScreen(
                initialSection = section,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable(
            route = Screen.Ocr.route,
            arguments = listOf(navArgument(Screen.Ocr.ARG_FILE_URI) {
                type = NavType.StringType; defaultValue = ""
            })
        ) { _ ->
            SmartToolsScreen(initialSection = "OCR", onNavigateBack = { navController.popBackStack() })
        }
        composable(Screen.QrScanner.route) {
            SmartToolsScreen(initialSection = "QR_SCAN", onNavigateBack = { navController.popBackStack() })
        }

        // ── Storage ──────────────────────────────────────────────────────────
        composable(Screen.Storage.route) {
            StorageScreen(
                onOpenPdf = { fileUri ->
                    navController.navigate(Screen.Editor.withFile(fileUri))
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        // ── Utility ──────────────────────────────────────────────────────────
        composable(
            route = Screen.Utility.route,
            arguments = listOf(
                navArgument(Screen.Utility.ARG_SECTION) {
                    type = NavType.StringType; defaultValue = ""
                }
            )
        ) { backStack ->
            val section = backStack.arguments?.getString(Screen.Utility.ARG_SECTION) ?: ""
            UtilityScreen(
                initialSection = section,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        // ── PDF Downloader ───────────────────────────────────────────────────────
        composable(Screen.PdfDownloader.route) {
            PdfDownloaderScreen(
                onNavigateBack = { navController.popBackStack() },
                onDownloadComplete = { filePath ->
                    navController.navigate(Screen.Editor.withFile(filePath))
                }
            )
        }

        // ── Settings ─────────────────────────────────────────────────────────
        composable(Screen.Settings.route) {
            SettingsScreen(onNavigateBack = { navController.popBackStack() })
        }
    }
}
