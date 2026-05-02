package com.bitflow.finance.ui.screens.import_statement

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.bitflow.finance.domain.usecase.ImportStatementBackgroundUseCase

@Composable
fun ImportProgressDialog(
    progress: ImportStatementBackgroundUseCase.ImportProgress?,
    onDismiss: () -> Unit
) {
    if (progress == null) return
    
    AlertDialog(
        onDismissRequest = { 
            if (progress.status == ImportStatementBackgroundUseCase.ProgressStatus.COMPLETED ||
                progress.status == ImportStatementBackgroundUseCase.ProgressStatus.FAILED) {
                onDismiss()
            }
        },
        title = {
            Text(
                text = "Importing Statements",
                style = MaterialTheme.typography.titleLarge
            )
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Overall progress
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "File ${progress.currentFile} of ${progress.totalFiles}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = "${((progress.currentFile.toFloat() / progress.totalFiles) * 100).toInt()}%",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold
                )
            }
            
            LinearProgressIndicator(
                progress = progress.currentFile.toFloat() / progress.totalFiles,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
            )                // Current file
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Icon(
                                imageVector = when (progress.status) {
                                    ImportStatementBackgroundUseCase.ProgressStatus.PARSING -> Icons.Default.Description
                                    ImportStatementBackgroundUseCase.ProgressStatus.CHECKING_DUPLICATES -> Icons.Default.Search
                                    ImportStatementBackgroundUseCase.ProgressStatus.IMPORTING -> Icons.Default.CloudUpload
                                    ImportStatementBackgroundUseCase.ProgressStatus.COMPLETED -> Icons.Default.CheckCircle
                                    ImportStatementBackgroundUseCase.ProgressStatus.FAILED -> Icons.Default.Error
                                },
                                contentDescription = null,
                                tint = when (progress.status) {
                                    ImportStatementBackgroundUseCase.ProgressStatus.COMPLETED -> Color(0xFF4CAF50)
                                    ImportStatementBackgroundUseCase.ProgressStatus.FAILED -> MaterialTheme.colorScheme.error
                                    else -> MaterialTheme.colorScheme.primary
                                }
                            )
                            
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = progress.fileName,
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.Medium
                                )
                                Text(
                                    text = when (progress.status) {
                                        ImportStatementBackgroundUseCase.ProgressStatus.PARSING -> "Parsing file..."
                                        ImportStatementBackgroundUseCase.ProgressStatus.CHECKING_DUPLICATES -> "Checking for duplicates..."
                                        ImportStatementBackgroundUseCase.ProgressStatus.IMPORTING -> "Importing transactions..."
                                        ImportStatementBackgroundUseCase.ProgressStatus.COMPLETED -> "✓ Completed"
                                        ImportStatementBackgroundUseCase.ProgressStatus.FAILED -> "✗ Failed"
                                    },
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        
                        if (progress.totalTransactions > 0) {
                            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        text = "${progress.processedTransactions} / ${progress.totalTransactions} transactions",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                                
                                if (progress.status == ImportStatementBackgroundUseCase.ProgressStatus.IMPORTING) {
                                    LinearProgressIndicator(
                                        progress = progress.processedTransactions.toFloat() / progress.totalTransactions,
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(4.dp)
                                            .clip(RoundedCornerShape(2.dp)),
                                    )
                                }
                            }
                        }
                        
                        if (progress.errorMessage != null) {
                            Text(
                                text = progress.errorMessage,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (progress.status == ImportStatementBackgroundUseCase.ProgressStatus.COMPLETED ||
                progress.status == ImportStatementBackgroundUseCase.ProgressStatus.FAILED) {
                TextButton(onClick = onDismiss) {
                    Text("Done")
                }
            }
        }
    )
}

@Composable
fun ImportResultsCard(
    results: ImportStatementBackgroundUseCase.BatchImportResult
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = Color(0xFF4CAF50)
                )
                Text(
                    text = "Import Complete",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Divider()
            
            // Summary stats
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatItem(
                    label = "Imported",
                    value = results.totalImported.toString(),
                    icon = Icons.Default.Add,
                    color = Color(0xFF4CAF50)
                )
                StatItem(
                    label = "Duplicates",
                    value = results.totalDuplicates.toString(),
                    icon = Icons.Default.ContentCopy,
                    color = Color(0xFFFF9800)
                )
                StatItem(
                    label = "Skipped",
                    value = results.totalSkipped.toString(),
                    icon = Icons.Default.Block,
                    color = Color(0xFF9E9E9E)
                )
            }
            
            if (results.failedFiles > 0) {
                Divider()
                
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Error,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error
                    )
                    Text(
                        text = "${results.failedFiles} file(s) failed to import",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
    }
}

@Composable
private fun StatItem(
    label: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(24.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
