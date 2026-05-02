package com.bitflow.finance.ui.screens.invoice

import android.content.Context
import android.print.PrintAttributes
import android.print.PrintManager
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Print
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import java.text.NumberFormat
import java.util.Locale
import android.widget.Toast

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InvoiceGeneratorScreen(
    onBackClick: () -> Unit,
    viewModel: InvoiceViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Invoice Generator") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = {
                        viewModel.saveInvoice {
                            Toast.makeText(context, "Invoice saved to records", Toast.LENGTH_SHORT).show()
                        }
                    }) {
                        Icon(Icons.Default.Save, contentDescription = "Save Record")
                    }
                    IconButton(onClick = { shareInvoice(context, state) }) {
                        Icon(Icons.Default.Share, contentDescription = "Share")
                    }
                    IconButton(onClick = { printInvoice(context, state) }) {
                        Icon(Icons.Default.Print, contentDescription = "Print")
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { viewModel.addItem() }) {
                Icon(Icons.Default.Add, contentDescription = "Add Item")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header Section
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Invoice Details", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = state.invoiceNumber,
                            onValueChange = { viewModel.updateInvoiceNumber(it) },
                            label = { Text("Invoice Number") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        // Date pickers would go here, simplified as text for now or just display
                        Text("Date: ${state.formattedDate}", modifier = Modifier.padding(top = 8.dp))
                        Text("Due Date: ${state.formattedDueDate}", modifier = Modifier.padding(top = 4.dp))
                    }
                }
            }

            // Client Section
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Bill To", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = state.clientName,
                            onValueChange = { viewModel.updateClientName(it) },
                            label = { Text("Client Name") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = state.clientAddress,
                            onValueChange = { viewModel.updateClientAddress(it) },
                            label = { Text("Client Address") },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 3
                        )
                    }
                }
            }

            // Items Section
            items(state.items) { item ->
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            OutlinedTextField(
                                value = item.description,
                                onValueChange = { viewModel.updateItem(item, it, item.subDescription, item.hsnCode, item.quantity, item.rate) },
                                label = { Text("Description") },
                                modifier = Modifier.weight(1f)
                            )
                            IconButton(onClick = { viewModel.removeItem(item) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Remove")
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        OutlinedTextField(
                            value = item.subDescription,
                            onValueChange = { viewModel.updateItem(item, item.description, it, item.hsnCode, item.quantity, item.rate) },
                            label = { Text("Sub Description") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedTextField(
                                value = item.hsnCode,
                                onValueChange = { viewModel.updateItem(item, item.description, item.subDescription, it, item.quantity, item.rate) },
                                label = { Text("HSN Code") },
                                modifier = Modifier.weight(1f)
                            )
                            OutlinedTextField(
                                value = item.quantity.toString(),
                                onValueChange = { viewModel.updateItem(item, item.description, item.subDescription, item.hsnCode, it.toIntOrNull() ?: 0, item.rate) },
                                label = { Text("Qty") },
                                modifier = Modifier.weight(0.5f),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                            OutlinedTextField(
                                value = item.rate.toString(),
                                onValueChange = { viewModel.updateItem(item, item.description, item.subDescription, item.hsnCode, item.quantity, it.toDoubleOrNull() ?: 0.0) },
                                label = { Text("Rate") },
                                modifier = Modifier.weight(1f),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                        }
                    }
                }
            }

            // Totals Section
            item {
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Tax & Payment Details", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        // GST Type Selection
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("GST Type:", style = MaterialTheme.typography.bodyMedium)
                            Spacer(modifier = Modifier.width(8.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                RadioButton(
                                    selected = state.gstType == GstType.INTRA_STATE,
                                    onClick = { viewModel.updateGstType(GstType.INTRA_STATE) }
                                )
                                Text("Intra-State (CGST+SGST)")
                            }
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                RadioButton(
                                    selected = state.gstType == GstType.INTER_STATE,
                                    onClick = { viewModel.updateGstType(GstType.INTER_STATE) }
                                )
                                Text("Inter-State (IGST)")
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                            Text("GST Rate (%):")
                            OutlinedTextField(
                                value = state.taxRate.toString(),
                                onValueChange = { viewModel.updateTaxRate(it.toDoubleOrNull() ?: 0.0) },
                                modifier = Modifier.width(100.dp),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                            Text("Amount Paid:")
                            OutlinedTextField(
                                value = state.amountPaid.toString(),
                                onValueChange = { viewModel.updateAmountPaid(it.toDoubleOrNull() ?: 0.0) },
                                modifier = Modifier.width(150.dp),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                        }

                        Divider(modifier = Modifier.padding(vertical = 8.dp))
                        
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Subtotal:")
                            Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.subtotal))
                        }
                        if (state.gstType == GstType.INTRA_STATE) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("CGST (${state.taxRate / 2}%):")
                                Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.cgstAmount))
                            }
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("SGST (${state.taxRate / 2}%):")
                                Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.sgstAmount))
                            }
                        } else {
                             Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("IGST (${state.taxRate}%):")
                                Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.igstAmount))
                            }
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Total:", style = MaterialTheme.typography.titleMedium)
                            Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.grandTotal), style = MaterialTheme.typography.titleMedium)
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Balance Due:", color = if (state.balanceDue > 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
                            Text(NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(state.balanceDue), color = if (state.balanceDue > 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
            
            // Spacer for FAB
            item { Spacer(modifier = Modifier.height(80.dp)) }
        }
    }
}

@Composable
fun InvoiceItemRow(
    item: InvoiceItem,
    onUpdate: (String, String, Int, Double) -> Unit,
    onRemove: () -> Unit
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Item", style = MaterialTheme.typography.labelMedium)
                IconButton(onClick = onRemove, modifier = Modifier.size(24.dp)) {
                    Icon(Icons.Default.Delete, contentDescription = "Remove", tint = MaterialTheme.colorScheme.error)
                }
            }
            
            OutlinedTextField(
                value = item.description,
                onValueChange = { onUpdate(it, item.subDescription, item.quantity, item.rate) },
                label = { Text("Description") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(4.dp))
            OutlinedTextField(
                value = item.subDescription,
                onValueChange = { onUpdate(item.description, it, item.quantity, item.rate) },
                label = { Text("Sub Description") },
                modifier = Modifier.fillMaxWidth()
            )
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = item.quantity.toString(),
                    onValueChange = { onUpdate(item.description, item.subDescription, it.toIntOrNull() ?: 0, item.rate) },
                    label = { Text("Qty") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                OutlinedTextField(
                    value = item.rate.toString(),
                    onValueChange = { onUpdate(item.description, item.subDescription, item.quantity, it.toDoubleOrNull() ?: 0.0) },
                    label = { Text("Rate") },
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
            }
            
            Text(
                text = "Amount: ${formatCurrency(item.amount)}",
                modifier = Modifier.align(Alignment.End).padding(top = 8.dp),
                fontWeight = FontWeight.Bold
            )
        }
    }
}

fun formatCurrency(amount: Double): String {
    return NumberFormat.getCurrencyInstance(Locale("en", "IN")).format(amount)
}

fun printInvoice(context: Context, state: InvoiceState) {
    val webView = WebView(context)
    webView.settings.javaScriptEnabled = true
    webView.webViewClient = object : WebViewClient() {
        override fun onPageFinished(view: WebView?, url: String?) {
            // Give Tailwind a moment to process styles
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                createWebPrintJob(context, view!!)
            }, 1000)
        }
    }
    
    val htmlContent = InvoiceHtmlTemplate.generateHtml(state)
    webView.loadDataWithBaseURL(null, htmlContent, "text/HTML", "UTF-8", null)
}

fun createWebPrintJob(context: Context, webView: WebView) {
    val printManager = context.getSystemService(Context.PRINT_SERVICE) as? PrintManager
    printManager?.let {
        val printAdapter = webView.createPrintDocumentAdapter("Invoice_Bitflow")
        it.print(
            "Invoice_Bitflow_Job",
            printAdapter,
            PrintAttributes.Builder().build()
        )
    }
}

private fun shareInvoice(context: Context, state: InvoiceState) {
    try {
        val htmlContent = InvoiceHtmlTemplate.generateHtml(state)
        // Save HTML to cache
        val file = java.io.File(context.cacheDir, "Invoice_${state.invoiceNumber}.html")
        java.io.FileOutputStream(file).use { it.write(htmlContent.toByteArray()) }
        
        // Share using FileProvider
        val uri = androidx.core.content.FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        
        val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
            type = "text/html"
            putExtra(android.content.Intent.EXTRA_STREAM, uri)
            putExtra(android.content.Intent.EXTRA_SUBJECT, "Invoice ${state.invoiceNumber}")
            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        
        context.startActivity(android.content.Intent.createChooser(intent, "Share Invoice"))
    } catch (e: Exception) {
        e.printStackTrace()
        Toast.makeText(context, "Error sharing invoice: ${e.message}", Toast.LENGTH_LONG).show()
    }
}
