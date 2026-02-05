package com.bitflow.finance.data.parser

import org.apache.poi.ss.usermodel.CellType
import org.apache.poi.ss.usermodel.DateUtil
import org.apache.poi.ss.usermodel.Row
import org.apache.poi.ss.usermodel.WorkbookFactory
import java.io.InputStream
import java.time.LocalDate
import java.time.ZoneId

/**
 * Utility for reading Excel files and converting them to text format
 * that can be parsed by the text-based parsers
 */
object ExcelReader {
    
    /**
     * Read an Excel file and convert it to CSV-like text format
     * 
     * @param inputStream Excel file input stream
     * @return List of lines as if reading a CSV file
     */
    fun readExcelAsLines(inputStream: InputStream): List<String> {
        val lines = mutableListOf<String>()
        
        try {
            val workbook = WorkbookFactory.create(inputStream)
            val sheet = workbook.getSheetAt(0) // First sheet
            
            println("[Excel Reader] Reading sheet: ${sheet.sheetName}")
            println("[Excel Reader] Total rows: ${sheet.lastRowNum + 1}")
            
            for (rowIndex in 0..sheet.lastRowNum) {
                val row = sheet.getRow(rowIndex) ?: continue
                val cells = mutableListOf<String>()
                
                // Read all cells in the row
                for (cellIndex in 0 until row.lastCellNum) {
                    val cell = row.getCell(cellIndex)
                    val cellValue = getCellValueAsString(cell)
                    // Quote values that contain commas to prevent CSV parsing issues
                    val quotedValue = if (cellValue.contains(",")) {
                        "\"$cellValue\""
                    } else {
                        cellValue
                    }
                    cells.add(quotedValue)
                }
                
                // Join cells with comma (CSV format)
                val line = cells.joinToString(",")
                lines.add(line)
                
                // Debug first 20 rows
                if (rowIndex < 20) {
                    println("[Excel Reader] Row $rowIndex: $line")
                }
            }
            
            workbook.close()
            println("[Excel Reader] Read ${lines.size} lines from Excel")
            
        } catch (e: Exception) {
            println("[Excel Reader] Error reading Excel: ${e.message}")
            e.printStackTrace()
            throw e
        }
        
        return lines
    }
    
    /**
     * Get cell value as string, handling different cell types
     */
    private fun getCellValueAsString(cell: org.apache.poi.ss.usermodel.Cell?): String {
        if (cell == null) return ""
        
        return try {
            when (cell.cellType) {
                CellType.STRING -> cell.stringCellValue.trim()
                
                CellType.NUMERIC -> {
                    if (DateUtil.isCellDateFormatted(cell)) {
                        // Date cell
                        val date = cell.dateCellValue
                        val localDate = date.toInstant()
                            .atZone(ZoneId.systemDefault())
                            .toLocalDate()
                        localDate.toString()
                    } else {
                        // Numeric cell
                        val numValue = cell.numericCellValue
                        // If it's a whole number, don't show decimals
                        if (numValue == numValue.toLong().toDouble()) {
                            numValue.toLong().toString()
                        } else {
                            numValue.toString()
                        }
                    }
                }
                
                CellType.BOOLEAN -> cell.booleanCellValue.toString()
                
                CellType.FORMULA -> {
                    try {
                        cell.numericCellValue.toString()
                    } catch (e: Exception) {
                        try {
                            cell.stringCellValue
                        } catch (e2: Exception) {
                            ""
                        }
                    }
                }
                
                CellType.BLANK -> ""
                
                else -> ""
            }
        } catch (e: Exception) {
            println("[Excel Reader] Error reading cell: ${e.message}")
            ""
        }
    }
}
