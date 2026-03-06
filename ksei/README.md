# KSEI Ownership Data Documentation

## Overview

This directory contains Indonesian stock ownership data from **KSEI (Kustodian Sentral Efek Indonesia)** - the Central Securities Depository of Indonesia.

## Data Sources

### 1. KSEI Aggregate Ownership Data

**Files:**
- `data/BalanceposYYYYMMDD.txt` - Balance position data showing shareholdings by investor type
- `data/StatisEfekYYYYMMDD.txt` - Securities master data with ownership percentages

**Download Sources:**
- **Balancepos (Holding Composition):** https://web.ksei.co.id/archive_download/holding_composition
  - Lists dated PDF files
  - Downloads as ZIP archive containing TXT files
  - Pipe-separated format (`|` delimiter)
  
- **StatisEfek (Master Securities):** https://web.ksei.co.id/archive_download/master_securities
  - Lists dated PDF files
  - Downloads as ZIP archive containing TXT files
  - Pipe-separated format (`|` delimiter)

**Data Structure:**

#### Balancepos File
Shows aggregated shareholdings by investor category for each listed stock:

| Field | Description |
|-------|-------------|
| Date | Reporting date |
| Code | Stock ticker symbol |
| Type | Security type (EQUITY, etc.) |
| Sec. Num | Number of securities |
| Price | Closing price |
| Local IS/CP/PF/IB/ID/MF/SC/FD/OT | Shares held by local investor types |
| Foreign IS/CP/PF/IB/ID/MF/SC/FD/OT | Shares held by foreign investor types |
| Total | Total shares outstanding |

#### StatisEfek File
Contains security details and ownership percentages:

| Field | Description |
|-------|-------------|
| Code, Description, ISIN Code | Security identification |
| Issuer | Company name |
| Sector | Industry classification |
| Local (%) | Percentage owned by local investors |
| Foreign (%) | Percentage owned by foreign investors |
| Closing Price | Latest price |

### 2. Investor Type Classification

Based on `Panduan_Klasifikasi_Investor_Institusi.pdf` and `Panduan_Acuan_Informasi_Berdasarkan_Tipe_Investor_guna_Pembentukan_SID_v....pdf`:

| Code | Type | Description | Examples |
|------|------|-------------|----------|
| **ID** | Individual | Personal investors | Individual persons |
| **CP** | Corporate | Companies/Corporations | PT, CV, Firma, non-financial businesses |
| **IB** | Financial Institution | Banks & financial institutions | Banks, financing companies |
| **IS** | Insurance | Insurance companies | Life insurance, general insurance, reinsurance |
| **SC** | Securities Company | Securities firms | Broker-dealers, underwriters, investment managers |
| **MF** | Mutual Fund | Investment funds | Reksa Dana, ETFs, hedge funds |
| **PF** | Pension Fund | Pension fund managers | Dana Pensiun |
| **FD** | Foundation | Non-profit foundations | Yayasan (social, religious, humanitarian) |
| **OT** | Others | Other entities | Government, associations, cooperatives, etc. |

**Detailed Sub-Classifications:**
Each investor type has specific sub-classifications with codes (001-049). See the PDF guides for complete mapping.

## Limitations

### What KSEI Data Shows
✅ Aggregated ownership by investor type (e.g., "Local Corporate owns 5.03B shares of AADI")  
✅ Market-level ownership patterns  
✅ Local vs. foreign ownership distribution  
✅ Institutional vs. retail investor composition  

### What KSEI Data Does NOT Show
❌ Individual investor names/identities  
❌ Specific entity ownership (e.g., "PT ABC owns X shares")  
❌ Beneficial ownership (ultimate owners behind shell companies)  
❌ Corporate structure relationships  
❌ Cross-ownership between companies  

## Obtaining Detailed Shareholder Information

### IDX Shareholder Registry (>5% Ownership)

For entity-level ownership data showing shareholders owning more than 5% of a company:

**Source:** Indonesia Stock Exchange (IDX) Company Announcements

**How to Access:**
1. Go to: https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/
2. In the search form:
   - **Keyword field** (`Kata kunci`): Enter `Laporan Bulanan Registrasi Pemegang Efek`
   - **Code field** (`Cari Kode`): Enter stock ticker (e.g., `BBCA`)
3. Results will show PDF files for monthly shareholder registration reports
4. Download the latest report

**Information Available:**
- Names of shareholders owning >5% of shares
- Number of shares owned
- Percentage ownership
- Monthly updates

**Example Workflow:**
```
Stock: BBCA (Bank Central Asia)
Search: "Laporan Bulanan Registrasi Pemegang Efek" + "BBCA"
Result: PDF list of major shareholders with >5% ownership
```

## Data Requirements for Ownership Network Analysis

To build complete ownership relationship networks, you need:

1. **KSEI Data** (this directory) - Market-level ownership patterns
2. **IDX Shareholder Registry** - Major shareholders (>5%) for each company
3. **Corporate Structure Data** - Parent-subsidiary relationships
4. **Beneficial Ownership Registry** - Ultimate owners behind corporate entities
5. **Annual Reports** - Top shareholders listed in company disclosures

## Recommended Approach

1. **Use KSEI data** for market analysis and ownership trends by investor type
2. **Use IDX shareholder registry** for specific entity ownership relationships
3. **Cross-reference** both sources for comprehensive ownership mapping
4. **Automate** PDF parsing for IDX reports (requires browser automation due to IDX website restrictions)

## Files in This Directory

```
ksei/
├── README.md (this file)
├── data/
│   ├── Balancepos20260227.txt (3,681 records)
│   └── StatisEfek20260227.txt (3,624 records)
├── Panduan_Klasifikasi_Investor_Institusi.pdf
└── Panduan_Acuan_Informasi_Berdasarkan_Tipe_Investor_guna_Pembentukan_SID_v....pdf
```

## Related Resources

- **KSEI Official Website:** https://www.ksei.co.id/
- **IDX Company Announcements:** https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/
- **OJK (Financial Services Authority):** https://www.ojk.go.id/

## Notes

- KSEI data is updated regularly (check file dates)
- IDX shareholder reports are published monthly
- Both sources should be used together for complete picture
- PDF extraction from IDX requires browser automation (403 error on direct access)
