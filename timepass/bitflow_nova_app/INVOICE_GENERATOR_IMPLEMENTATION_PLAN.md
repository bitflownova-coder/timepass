# Invoice Generator Implementation Plan

## 1. Overview
We will port the web-based Invoice Generator to the Android app using Jetpack Compose for the input UI and a WebView/PrintManager approach for generating the PDF. This ensures the output PDF looks **exactly** like the web version (including the Tailwind styling) while providing a native Android input experience.

## 2. Architecture
- **Screen**: `InvoiceGeneratorScreen` (Compose) - Form for entering invoice details.
- **ViewModel**: `InvoiceViewModel` - Holds the state (items, client details, totals).
- **Template Engine**: `InvoiceHtmlTemplate` - Kotlin object containing the raw HTML/CSS from `index.html`, with methods to inject dynamic data.
- **PDF Service**: Uses Android's `PrintManager` or `WebView` to render the HTML and save as PDF.

## 3. Step-by-Step Implementation

### Step 1: Create Data Models
- Define `InvoiceItem`, `InvoiceData` data classes.

### Step 2: Create HTML Template
- Port `index.html` into a Kotlin string template.
- Replace static text with `${variable}` placeholders.

### Step 3: Create ViewModel
- Handle adding/removing rows.
- Calculate Subtotal, Tax, Grand Total.

### Step 4: Create Compose UI
- Header inputs (Invoice #, Date).
- Client Info inputs.
- Items List (Dynamic rows).
- "Generate PDF" button.

### Step 5: PDF Generation Logic
- Implement `WebView` loading of the HTML.
- Use `PrintDocumentAdapter` to save to PDF.

### Step 6: Navigation Integration
- Add "invoice" route to `Navigation.kt`.
- Add entry point button in `HomeScreen`.

## 4. Execution
I will now proceed to create these files in the `com.bitflow.finance.ui.screens.invoice` package.
