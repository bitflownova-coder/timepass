package com.bitflow.pdfconverter.feature.converter.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.bitflow.pdfconverter.core.ui.components.PdfTopBar

@Composable
fun ConverterScreen(navController: NavController) {
    Scaffold(
        topBar = { PdfTopBar(title = "Converter", onNavigateBack = { navController.popBackStack() }) }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ConversionOptionCard("Images to PDF", "Convert JPG/PNG images into a PDF document", Icons.Default.Image) {
                navController.navigate("converter/image_to_pdf")
            }
            ConversionOptionCard("Office to PDF", "Convert .docx, .xlsx, .pptx files to PDF", Icons.Default.Description) {
                navController.navigate("converter/office_to_pdf")
            }
            ConversionOptionCard("Merge PDFs", "Combine multiple PDF files into one", Icons.Default.MergeType) {
                navController.navigate("converter/merge")
            }
            ConversionOptionCard("Split PDF", "Extract pages from a PDF into a new file", Icons.Default.CallSplit) {
                navController.navigate("converter/split")
            }
        }
    }
}

@Composable
private fun ConversionOptionCard(title: String, subtitle: String, icon: ImageVector, onClick: () -> Unit) {
    Card(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Row(modifier = Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
            Column {
                Text(title, style = MaterialTheme.typography.titleSmall)
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}
