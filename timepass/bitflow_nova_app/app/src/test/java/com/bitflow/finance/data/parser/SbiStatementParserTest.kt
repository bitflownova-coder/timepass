package com.bitflow.finance.data.parser

import com.bitflow.finance.domain.model.TransactionDirection
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.ByteArrayInputStream
import java.nio.charset.StandardCharsets

class SbiStatementParserTest {

    private val parser = UniversalStatementParser()

    @Test
    fun parse_validSbiCsv_returnsTransactions() = runBlocking {
        val csvContent = """
Account Name       :                ,Mr. Pratik Kalidas Chavan,,,,,
Address            :,"FLAT NO A-302, HARI SANKALP APARTMENT, 3",,,,,
                                    ,"A STREET, SERENE MEADOWS, ANANDWALLI",,,,,
                                    ,Nashik-422013,,,,,
                                    ,516:Nashik,,,,,
Date               :                ,10-Jul-24,,,,,
Account Number     :,_00000040206916964,,,,,
Account Description:,REGULAR SB CHQ-INDIVIDUALS,,,,,
Branch             :,"MIDCORPORATE, NASHIK",,,,,
Drawing Power      :,0,,,,,
Interest Rate(% p.a.):,2.7,,,,,
MOD Balance      :,0,,,,,
CIF No.          :,_90764475771,,,,,
IFS (Indian Financial System) Code         :,SBIN0021197,,,,,
MICR (Magnetic Ink Character Recognition)  Code        :,_422002044,,,,,
Nomination Registered    :,Yes ,,,,,
Balance on 1 Apr 2024        :,"1,118.30",,,,,
Start Date          :,01-Apr-24,,,,,
End Date            :,30-Apr-24,,,,,
Txn Date,Value Date,Description,Ref No./Cheque No.,        Debit,Credit,Balance
01-Apr-24,01-Apr-24,   TO TRANSFER-UPI/DR/409297068518/BASAVRAJ/BKID/basavrajra/UPI--,TRANSFER TO 4897690162095,20, ,"1,098.30"
02-Apr-24,02-Apr-24,   TO TRANSFER-UPI/DR/409374856309/SWIGGY/YESB/swiggy@yes/Debit M--,TRANSFER TO 4897691162095,162, ,936.3
02-Apr-24,02-Apr-24,   TO TRANSFER-UPI/DR/409323508043/Mr KANHA/CBIN/q872849215/UPI--,TRANSFER TO 4897691162095,50, ,886.3
02-Apr-24,02-Apr-24,   by debit card-OTHPOS409308815279BLOOMBAY ENTERPRISES PPUNE--,,300, ,586.3
02-Apr-24,02-Apr-24,   BY TRANSFER-UPI/CR/409368416110/AMAN NIH/UTIB/amanshaikh/UPI--,TRANSFER FROM 4897733162090, ,"18,000.00","18,586.30"
        """.trimIndent()

        val inputStream = ByteArrayInputStream(csvContent.toByteArray(StandardCharsets.UTF_8))
        val transactions = parser.parse(inputStream)

        assertEquals(5, transactions.size)
        
        val t1 = transactions[0]
        assertEquals(20.0, t1.amount, 0.01)
        assertEquals(TransactionDirection.DEBIT, t1.direction)
        
        val t5 = transactions[4]
        assertEquals(18000.0, t5.amount, 0.01)
        assertEquals(TransactionDirection.CREDIT, t5.direction)
    }

    @Test
    fun parse_quotedCsv_returnsTransactions() = runBlocking {
        val csvContent = """
"Txn Date","Description","Ref No./Cheque No.","Debit","Credit","Balance"
"10-Jul-24","TO TRANSFER-UPI/DR/419245626209/Mr. SHAIK/SBIN/","","1,098.30","1,098.30",""
        """.trimIndent()

        val inputStream = ByteArrayInputStream(csvContent.toByteArray(StandardCharsets.UTF_8))
        val transactions = parser.parse(inputStream)

        assertEquals(1, transactions.size)
        
        val t1 = transactions[0]
        assertEquals(1098.30, t1.amount, 0.01)
        assertEquals(TransactionDirection.DEBIT, t1.direction)
        assertEquals("TO TRANSFER-UPI/DR/419245626209/Mr. SHAIK/SBIN/", t1.description)
    }
}
