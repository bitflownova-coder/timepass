package com.bitflow.finance.ui.screens.simple_finance

import android.content.Context
import android.content.Intent
import android.graphics.pdf.PdfDocument
import android.os.Environment
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.hilt.navigation.compose.hiltViewModel
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import java.io.File
import java.io.FileOutputStream
import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SimpleInvoiceScreen(
    viewModel: SimpleFinanceViewModel = hiltViewModel(),
    paymentId: Long? = null,
    onBackClick: () -> Unit
) {
    val context = LocalContext.current
    val clients by viewModel.clients.collectAsState()
    val paymentsWithoutInvoice by viewModel.paymentsWithoutInvoice.collectAsState()
    
    var selectedPayment by remember { mutableStateOf<IncomePaymentEntity?>(null) }
    var selectedClient by remember { mutableStateOf<ClientEntity?>(null) }
    
    // Form fields
    var invoiceNumber by remember { 
        mutableStateOf("INV-${SimpleDateFormat("yyyyMMdd", Locale.getDefault()).format(Date())}-${(100..999).random()}")
    }
    var description by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var taxRate by remember { mutableStateOf("18") }
    var notes by remember { mutableStateOf("") }
    
    // Load payment if ID provided
    LaunchedEffect(paymentId) {
        paymentId?.let { id ->
            val payment = viewModel.getPaymentForInvoice(id)
            payment?.let {
                selectedPayment = it
                description = it.description
                amount = it.amount.toString()
                it.clientId?.let { clientId ->
                    selectedClient = viewModel.getClientForPayment(clientId)
                }
            }
        }
    }
    
    var showSelectPaymentDialog by remember { mutableStateOf(false) }
    var isGenerating by remember { mutableStateOf(false) }
    
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    val subtotal = amount.toDoubleOrNull() ?: 0.0
    val tax = subtotal * ((taxRate.toDoubleOrNull() ?: 18.0) / 100)
    val total = subtotal + tax
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Generate Invoice", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Link to Payment (Optional)
            item {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = if (selectedPayment != null) 
                            Color(0xFF10B981).copy(alpha = 0.1f) 
                        else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    ),
                    shape = RoundedCornerShape(12.dp),
                    onClick = { showSelectPaymentDialog = true }
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                if (selectedPayment != null) "Linked to Payment" else "Link to Payment (Optional)",
                                fontWeight = FontWeight.Medium
                            )
                            if (selectedPayment != null) {
                                Text(
                                    "${selectedPayment!!.description} - ${currencyFormat.format(selectedPayment!!.amount)}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Color(0xFF10B981)
                                )
                            } else {
                                Text(
                                    "${paymentsWithoutInvoice.size} payments without invoice",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        Icon(Icons.Default.ChevronRight, null)
                    }
                }
            }
            
            // Invoice Details Section
            item {
                Text("Invoice Details", fontWeight = FontWeight.Bold)
            }
            
            item {
                OutlinedTextField(
                    value = invoiceNumber,
                    onValueChange = { invoiceNumber = it },
                    label = { Text("Invoice Number") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }
            
            // Client Section
            item {
                Text("Client Details", fontWeight = FontWeight.Bold)
            }
            
            item {
                var clientExpanded by remember { mutableStateOf(false) }
                
                ExposedDropdownMenuBox(
                    expanded = clientExpanded,
                    onExpandedChange = { clientExpanded = it }
                ) {
                    OutlinedTextField(
                        value = selectedClient?.name ?: "Select Client",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Client") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = clientExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = clientExpanded,
                        onDismissRequest = { clientExpanded = false }
                    ) {
                        clients.forEach { client ->
                            DropdownMenuItem(
                                text = { 
                                    Column {
                                        Text(client.name)
                                        if (client.email.isNotEmpty()) {
                                            Text(client.email, style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                },
                                onClick = {
                                    selectedClient = client
                                    clientExpanded = false
                                }
                            )
                        }
                    }
                }
            }
            
            // Items Section
            item {
                Text("Line Items", fontWeight = FontWeight.Bold)
            }
            
            item {
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Description") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3
                )
            }
            
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(
                        value = amount,
                        onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                        label = { Text("Amount") },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        leadingIcon = { Text("₹") }
                    )
                    OutlinedTextField(
                        value = taxRate,
                        onValueChange = { taxRate = it.filter { c -> c.isDigit() || c == '.' } },
                        label = { Text("GST %") },
                        modifier = Modifier.weight(0.5f),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                    )
                }
            }
            
            // Totals Section
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF3B82F6).copy(alpha = 0.1f)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Subtotal")
                            Text(currencyFormat.format(subtotal))
                        }
                        Spacer(Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("GST (${taxRate}%)")
                            Text(currencyFormat.format(tax))
                        }
                        Divider(Modifier.padding(vertical = 8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Total", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                            Text(
                                currencyFormat.format(total),
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = Color(0xFF3B82F6)
                            )
                        }
                    }
                }
            }
            
            item {
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Notes (Optional)") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3
                )
            }
            
            // Generate Button
            item {
                Button(
                    onClick = {
                        isGenerating = true
                        // Generate and share invoice
                        val invoiceHtml = generateInvoiceHtml(
                            invoiceNumber = invoiceNumber,
                            clientName = selectedClient?.name ?: "",
                            clientEmail = selectedClient?.email ?: "",
                            clientPhone = selectedClient?.phone ?: "",
                            clientAddress = selectedClient?.address ?: "",
                            clientGstin = selectedClient?.gstin ?: "",
                            description = description,
                            amount = subtotal,
                            taxRate = taxRate.toDoubleOrNull() ?: 18.0,
                            notes = notes
                        )
                        
                        // Mark payment as invoiced if linked
                        selectedPayment?.let { payment ->
                            viewModel.markInvoiceGenerated(payment.id, invoiceNumber, 0L)
                        }
                        
                        // Share as HTML (can be printed to PDF)
                        shareInvoice(context, invoiceHtml, invoiceNumber)
                        isGenerating = false
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    enabled = description.isNotBlank() && amount.isNotBlank() && !isGenerating,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3B82F6))
                ) {
                    if (isGenerating) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            color = Color.White
                        )
                    } else {
                        Icon(Icons.Default.Receipt, null)
                        Spacer(Modifier.width(8.dp))
                        Text("Generate Invoice", fontWeight = FontWeight.Bold)
                    }
                }
            }
            
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
    
    // Select Payment Dialog
    if (showSelectPaymentDialog) {
        AlertDialog(
            onDismissRequest = { showSelectPaymentDialog = false },
            title = { Text("Select Payment", fontWeight = FontWeight.Bold) },
            text = {
                LazyColumn {
                    if (paymentsWithoutInvoice.isEmpty()) {
                        item {
                            Text(
                                "No payments without invoice",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        items(paymentsWithoutInvoice) { payment ->
                            val client = payment.clientId?.let { id -> clients.find { it.id == id } }
                            
                            Card(
                                onClick = {
                                    selectedPayment = payment
                                    description = payment.description
                                    amount = payment.amount.toString()
                                    client?.let { selectedClient = it }
                                    showSelectPaymentDialog = false
                                },
                                modifier = Modifier.padding(vertical = 4.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                                )
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(12.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Column {
                                        Text(payment.description, fontWeight = FontWeight.Medium)
                                        client?.let {
                                            Text(it.name, style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                    Text(
                                        currencyFormat.format(payment.amount),
                                        color = Color(0xFF10B981),
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showSelectPaymentDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

private fun generateInvoiceHtml(
    invoiceNumber: String,
    clientName: String,
    clientEmail: String,
    clientPhone: String,
    clientAddress: String,
    clientGstin: String,
    description: String,
    amount: Double,
    taxRate: Double,
    notes: String
): String {
    val tax = amount * (taxRate / 100)
    val total = amount + tax
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())
    val date = dateFormat.format(Date())
    val currencyFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
    
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice $invoiceNumber</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 20px; background: #fff; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { margin: 0; color: #1e293b; }
        .header .subtitle { color: #64748b; margin: 5px 0 0 0; }
        .invoice-title { color: #2563eb; font-size: 24px; margin: 0; float: right; }
        .section { margin-bottom: 20px; }
        .section h3 { color: #64748b; font-size: 12px; text-transform: uppercase; margin: 0 0 10px 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .dates { background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th { background: #f1f5f9; padding: 12px; text-align: left; font-size: 12px; color: #475569; }
        td { padding: 16px 12px; border-bottom: 1px solid #e2e8f0; }
        .totals { margin-left: auto; max-width: 300px; }
        .totals .row { display: flex; justify-content: space-between; padding: 8px 0; }
        .totals .total { background: #f8fafc; padding: 12px; border-radius: 8px; margin-top: 8px; }
        .totals .total span:last-child { color: #2563eb; font-weight: bold; font-size: 20px; }
        .notes { background: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 30px; }
        .footer { margin-top: 40px; text-align: center; color: #64748b; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BitFlow Nova</h1>
            <p class="subtitle">Professional Invoice</p>
            <p class="invoice-title">INVOICE #$invoiceNumber</p>
            <div style="clear: both;"></div>
        </div>
        
        <div class="grid">
            <div class="section">
                <h3>From</h3>
                <p><strong>BitFlow Nova</strong><br>
                Software Solutions<br>
                contact@bitflownova.com</p>
            </div>
            <div class="section">
                <h3>Bill To</h3>
                <p><strong>$clientName</strong><br>
                ${if (clientAddress.isNotEmpty()) "$clientAddress<br>" else ""}
                ${if (clientEmail.isNotEmpty()) "$clientEmail<br>" else ""}
                ${if (clientPhone.isNotEmpty()) "$clientPhone<br>" else ""}
                ${if (clientGstin.isNotEmpty()) "GSTIN: $clientGstin" else ""}</p>
            </div>
        </div>
        
        <div class="dates">
            <strong>Date:</strong> $date
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th style="text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>$description</td>
                    <td style="text-align: right;">${currencyFormat.format(amount)}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="totals">
            <div class="row">
                <span>Subtotal</span>
                <span>${currencyFormat.format(amount)}</span>
            </div>
            <div class="row">
                <span>GST ($taxRate%)</span>
                <span>${currencyFormat.format(tax)}</span>
            </div>
            <div class="total row">
                <span><strong>Total</strong></span>
                <span>${currencyFormat.format(total)}</span>
            </div>
        </div>
        
        ${if (notes.isNotEmpty()) """
        <div class="notes">
            <strong>Notes:</strong><br>
            $notes
        </div>
        """ else ""}
        
        <div class="footer">
            <p>Thank you for your business!</p>
            <p>Generated by BitFlow Nova Finance</p>
        </div>
    </div>
</body>
</html>
    """.trimIndent()
}

private fun shareInvoice(context: Context, html: String, invoiceNumber: String) {
    try {
        // Save HTML to cache
        val file = File(context.cacheDir, "Invoice_$invoiceNumber.html")
        FileOutputStream(file).use { it.write(html.toByteArray()) }
        
        // Share using FileProvider
        val uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.provider",
            file
        )
        
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/html"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, "Invoice $invoiceNumber")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        
        context.startActivity(Intent.createChooser(intent, "Share Invoice"))
    } catch (e: Exception) {
        e.printStackTrace()
    }
}
