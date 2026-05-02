# Smart Statement Parser System

## Overview

The Smart Statement Parser automatically detects and parses different bank statement formats without requiring manual configuration. It uses a **Dynamic Header Detection** strategy that scans files for identifying keywords.

## Architecture

### 1. Core Components

#### `BankStatementParser` (Interface)
```kotlin
interface BankStatementParser {
    fun parse(inputStream: InputStream): List<ParsedTransaction>
    fun getParserName(): String
}
```

#### `StatementParserFactory` (Factory)
- **Auto-detects** statement format by scanning first 40 lines
- **Returns** the appropriate parser implementation
- **Throws** `UnknownStatementFormatException` if format not recognized

#### Parser Implementations
- **`SbiStatementParser`**: For SBI and SBI-style statements
- **`BitflowStatementParser`**: For Bitflow and similar formats

### 2. Detection Strategy

The factory scans the first 40 lines looking for keyword combinations:

**SBI Format Detection:**
- Looks for: `"Trans Date"` + `"Debit"` 
- Or: `"Txn Date"` + `"Debit"`
- Or: `"Transaction Date"` + `"Dr."`

**Bitflow Format Detection:**
- Looks for: `"Particulars"` + `"Withdrawal"`
- Or: `"Particulars"` + `"Deposit"`

### 3. Parsing Flow

```
1. Read first 40 lines
2. Detect format → Select parser
3. Find header row (dynamic scanning)
4. Map columns by names (not positions)
5. Parse data rows
6. Handle errors gracefully
```

## Supported Formats

### SBI Statement Format
```csv
[Marketing Header Rows...]
Trans Date,Description/Narration,Chq./Ref.No.,Debit(Dr.) INR,Credit(Cr.) INR,Balance INR
01 Jan 2024,SALARY CREDIT,REF123,-,50000.00,50000.00
02 Jan 2024,ATM WITHDRAWAL,ATM456,2000.00,-,48000.00
```

**Expected Columns:**
- Date: `Trans Date`, `Txn Date`, `Transaction Date`, `Date`
- Description: `Description`, `Narration`, `Description/Narration`
- Debit: `Debit(Dr.)`, `Debit`, `Dr.`, `Withdrawal`
- Credit: `Credit(Cr.)`, `Credit`, `Cr.`, `Deposit`
- Reference: `Chq./Ref.No.`, `Reference`, `Ref No`
- Balance: `Balance`, `Balance INR`

### Bitflow Statement Format
```csv
[Bank Logo/Headers...]
Date,Particulars,Chq./Ref.No.,Withdrawal,Deposit,Balance
01/01/2024,Salary Credit,REF123,,50000.00,50000.00
02/01/2024,ATM Withdrawal,ATM456,2000.00,,48000.00
```

**Expected Columns:**
- Date: `Date`, `Transaction Date`, `Txn Date`
- Particulars: `Particulars`, `Description`, `Narration`
- Withdrawal: `Withdrawal`, `Debit`, `Dr.`
- Deposit: `Deposit`, `Credit`, `Cr.`

## Usage

### In Use Cases
```kotlin
// Automatic format detection and parsing
val transactions = StatementParserFactory.parseStatement(inputStream)
```

### In ViewModels
```kotlin
class ImportStatementViewModel @Inject constructor(
    private val backgroundImport: ImportStatementBackgroundUseCase
) {
    fun importFiles(uris: List<Uri>) {
        // The background import automatically uses smart parser
        backgroundImport(accountId, inputStreams) { progress ->
            // Handle progress
        }
    }
}
```

## Error Handling

### `UnknownStatementFormatException`
Thrown when file format cannot be detected.
- **Reason**: None of the registered parsers match the file
- **Action**: User needs to check if the file is a supported bank statement

### `StatementParsingException`
Thrown when parsing fails after format detection.
- **Reason**: File structure doesn't match expected format
- **Action**: File may be corrupted or have unexpected format variations

## Date Format Support

Both parsers support multiple date formats:
- `dd MMM yyyy` (e.g., "01 Jan 2024")
- `dd/MM/yyyy` (e.g., "01/01/2024")
- `dd-MM-yyyy` (e.g., "01-01-2024")
- `yyyy-MM-dd` (e.g., "2024-01-01")
- `dd MMM yy` (e.g., "01 Jan 24")

## Amount Handling

- **Removes**: Commas, currency symbols (₹, INR), spaces
- **Handles**: Blank fields as 0.0
- **Supports**: Decimal precision
- **Example**: `"1,25,000.50"` → `125000.50`

## Adding New Bank Formats

### Step 1: Create Parser Implementation
```kotlin
class HdfcStatementParser : BankStatementParser {
    override fun getParserName() = "HDFC Statement Parser"
    
    override fun parse(inputStream: InputStream): List<ParsedTransaction> {
        // Implementation
    }
}
```

### Step 2: Register in Factory
```kotlin
// In StatementParserFactory.kt
private val PARSERS = listOf(
    // ... existing parsers ...
    ParserDetector(
        name = "HDFC",
        keywords = listOf(
            listOf("date", "narration", "withdrawal")
        ),
        parserProvider = { HdfcStatementParser() }
    )
)
```

## Testing

### Test with Sample Files
```kotlin
@Test
fun `test SBI format detection`() {
    val inputStream = getResourceAsStream("sample_sbi.csv")
    val parser = StatementParserFactory.detectParser(inputStream)
    
    assertTrue(parser is SbiStatementParser)
}

@Test
fun `test parsing transactions`() {
    val inputStream = getResourceAsStream("sample_sbi.csv")
    val transactions = StatementParserFactory.parseStatement(inputStream)
    
    assertTrue(transactions.isNotEmpty())
    assertEquals(LocalDate.of(2024, 1, 1), transactions.first().txnDate)
}
```

## Advantages Over Old System

### ✅ Old System Issues:
- Fixed row numbers (breaks with marketing headers)
- Single parser for all formats
- Hard to extend
- Poor error messages

### ✅ New System Benefits:
- **Dynamic**: Handles metadata rows automatically
- **Extensible**: Easy to add new bank formats
- **Clear**: Specific parsers for each format
- **Robust**: Better error handling and logging
- **Maintainable**: Clean separation of concerns

## Logging

All parsers log their progress:
```
[Parser Factory] Read 35 lines for format detection
[Parser Factory] Matched SBI format with keywords: [trans date, debit]
[Parser Factory] Detected format: SBI
[SBI Parser] Scanning 100 lines for header...
[SBI Parser] Found header at row 7
[SBI Parser] Column mapping: ColumnMapping(dateIndex=0, descriptionIndex=1, ...)
[SBI Parser] Parsed 45 transactions
```

## Future Enhancements

1. **PDF Support**: Extend parsers to handle PDF statements
2. **Excel Support**: Native XLSX parsing with smart detection
3. **AI Detection**: Use ML to detect unknown formats
4. **Format Learning**: User-guided format registration
5. **Cloud Sync**: Share format definitions across devices

## API Reference

### `StatementParserFactory`
- `detectParser(inputStream): BankStatementParser`
- `parseStatement(inputStream): List<ParsedTransaction>`
- `registerParser(name, keywords, provider)` (Future)

### `ParsedTransaction`
```kotlin
data class ParsedTransaction(
    val txnDate: LocalDate,
    val valueDate: LocalDate?,
    val description: String,
    val reference: String?,
    val amount: Double,
    val direction: ActivityType,
    val balanceAfterTxn: Double
)
```

---

**Last Updated**: November 29, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
