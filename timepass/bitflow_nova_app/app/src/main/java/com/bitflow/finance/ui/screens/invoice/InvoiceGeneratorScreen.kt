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
                InvoiceItemRow(
                    item = item,
                    onUpdate = { desc, sub, qty, rate ->
                        viewModel.updateItem(item, desc, sub, qty, rate)
                    },
                    onRemove = { viewModel.removeItem(item) }
                )
            }

            // Totals Section
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Subtotal")
                            Text(formatCurrency(state.subtotal))
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("GST (%)")
                                Spacer(modifier = Modifier.width(8.dp))
                                OutlinedTextField(
                                    value = state.taxRate.toString(),
                                    onValueChange = { viewModel.updateTaxRate(it.toDoubleOrNull() ?: 0.0) },
                                    modifier = Modifier.width(80.dp),
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                                )
                            }
                            Text(formatCurrency(state.taxAmount))
                        }
                        Divider(modifier = Modifier.padding(vertical = 8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Total", fontWeight = FontWeight.Bold)
                            Text(formatCurrency(state.grandTotal), fontWeight = FontWeight.Bold)
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
