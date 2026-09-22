What is the best way to determine membership in the fortune 500? Additionally, the industry classification for each member? As well as employment, subsidiaries, where they are located, etc.

**Yes—EDGAR is the right foundation under a free-data constraint.** I would use a dated S&P 500 membership list to define the population, EDGAR for company identities and disclosures, and GLEIF for additional parent-company relationships. For actual establishments, NAICS codes, and some location-level employment, I would add OSHA and EPA data.

One correction: **EDGAR’s standard industry classification is SIC, not NAICS.** NAICS requires a separate source or an explicitly documented inference. ([SEC][1])

The result can be a useful, auditable company database. The important boundary is that **disclosed subsidiaries and observed establishments are not necessarily a complete corporate family or workplace census**.

## 1. Define membership: S&P 500 for coverage, Dow for a pilot

I would use the **S&P 500** for the main dataset and the **Dow’s 30 companies** for a smaller proof of concept. Those are different populations, so choose based on the scope of your analysis—not simply which roster is easiest to collect. ([S&P Global][2])

For a free starting roster, the Wikipedia S&P 500 table is convenient because it supplies company names, symbols, CIKs, headquarters locations, and GICS classifications. Treat it as a **seed to validate**, not the authoritative source for historical membership. Its GICS fields are also not NAICS. ([Wikipedia][3])

I would cross-check that seed against official index information and a dated issuer holdings file, such as State Street’s SPY holdings. ETF holdings are a useful corroborating source, but they are fund holdings—not, by definition, an exact index-constituent file. ([S&P Global][2])

My recommended membership key is:

```text
universe_name + membership_as_of_date + issuer_CIK
```

Keep security symbols in a separate table so that multiple securities from the same issuer do not become duplicate companies.

**There is still a licensing distinction:** the S&P 500 and Dow are proprietary indexes, too. Freely viewable constituent information is not equivalent to an openly licensed index product. That distinction matters particularly when redistributing a dataset rather than using it for analysis. ([SSGA][4])

To eliminate dependence on a proprietary index, another option is to define your own population of SEC-reporting operating companies—for example, a reproducible set meeting stated revenue or workforce criteria. I would describe that as a custom company universe, not as a replacement estimate of Fortune or S&P membership.

## 2. The free sources I would combine

| Information needed                                    | Free source                                           | What it provides—and the main limitation                                                                                        |
| ----------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Company identity and filing history**               | **SEC EDGAR submissions API and filings**             | CIK, names, tickers, filing history, and company metadata. This is the backbone for linking disclosures. ([SEC][5])             |
| **Company industry**                                  | **SEC SIC classification**                            | A standardized company-level SIC code. It is not establishment-level NAICS. ([SEC][1])                                          |
| **Disclosed subsidiaries**                            | **10-K Exhibit 21**                                   | Subsidiary names and incorporation/organization jurisdictions; permitted omissions mean the list can be incomplete. ([eCFR][6]) |
| **Additional parent relationships**                   | **GLEIF Level 2**                                     | Direct and ultimate accounting-consolidating parents for covered entities, subject to reporting exceptions. ([GLEIF][7])        |
| **Reported corporate employment**                     | **10-K business/human-capital disclosure**            | Reported workforce figures, with definitions and dates that must be read from the disclosure. ([eCFR][8])                       |
| **Establishment locations, industry, and employment** | **OSHA Injury Tracking Application / Form 300A data** | Establishment information and annual-average employees for the reporting population—not all U.S. businesses. ([OSHA][9])        |
| **Facilities, NAICS, and parent-company links**       | **EPA Toxics Release Inventory**                      | Facility locations, industry codes, and parent information for TRI-reporting facilities. ([US EPA][10])                         |

### Subsidiaries: Exhibit 21 is useful, but preserve what it actually says

You are right that EDGAR contains subsidiaries. Exhibit 21 is a strong starting point, but its required information is primarily **names and jurisdictions**, and the rules permit certain subsidiaries to be omitted. It does not require a workforce count, NAICS code, or operating address for every subsidiary. ([eCFR][6])

For a concrete example, Apple’s 2025 Exhibit 21 lists subsidiaries and their incorporation jurisdictions, then explicitly states that other subsidiaries have been omitted under the applicable disclosure rule. ([SEC][11])

I would therefore represent an Exhibit 21 record as:

```text
Subsidiary X was disclosed as belonging to reporting group Y
in filing Z, for fiscal year-end T.
```

I would **not automatically represent it as**:

```text
Y directly owns X.
```

A flat group list does not establish every intermediate ownership link. Likewise, “incorporated in Delaware” is not evidence that the subsidiary’s employees work in Delaware.

**GLEIF is the best complementary open source I would add here.** Its relationship data identifies direct and ultimate *accounting-consolidating* parents—not a universal beneficial-ownership structure. Its coverage is limited to the entities and relationships available through the LEI system, but the data is freely accessible and provided under CC0. ([GLEIF][7])

Use separate relationship types, such as:

```text
disclosed_group_member
direct_accounting_parent
ultimate_accounting_parent
```

That avoids manufacturing a more precise ownership graph than your evidence supports.

## 3. Employment: extract the number, definition, scope, and date

For corporate employment, I would extract the relevant passage from the annual report or 10-K business/human-capital discussion. The SEC disclosure requirement includes the number of persons employed, but the filing still needs to be read for its measurement basis and scope. ([eCFR][8])

For example, Apple’s 2025 10-K reports **approximately 166,000 full-time equivalent employees as of September 27, 2025**. An extraction should preserve “approximately,” “full-time equivalent,” and the reference date—not reduce the passage to an undifferentiated `employees = 166000`. ([SEC][12])

I would store:

```text
entity_id
employment_value
employment_measure        # headcount, FTE, annual-average employees, etc.
organizational_scope      # consolidated group, subsidiary, establishment
geographic_scope          # worldwide, United States, named location, etc.
reference_date_or_period
approximate_flag
source_accession
evidence_text
```

Do not assume the SEC Company Facts API provides a uniform employee-count field for every issuer. Its aggregated XBRL coverage is limited to supported, noncustom taxonomy facts applying to the entire filing entity; narrative disclosures and other facts can require direct filing extraction. ([SEC][5])

For subsidiary employment, my default would be **unknown unless separately disclosed or observed**. I would not allocate the parent’s total across subsidiaries without labeling that as a model-based estimate.

## 4. NAICS and workplace locations: OSHA and EPA are valuable additions

### OSHA: the closest free source to several of your establishment-level requirements

OSHA’s public Injury Tracking Application data includes establishment-level Form 300A summaries. The underlying form contains establishment name and address, industry information, **annual-average employees**, and annual hours worked. It provides for SIC or NAICS industry codes. ([OSHA][9])

That makes it worth testing for records of the form:

```text
establishment → address → industry code → annual-average employment
```

The limitation is coverage: OSHA collects these submissions from establishments meeting specified reporting criteria, not from every establishment. An absent record must therefore remain **unobserved**, not “zero employees” or “not part of the company.” ([OSHA][9])

I would match these establishments against the subsidiary names gathered from EDGAR and GLEIF, using address and other available evidence rather than company-name similarity alone.

### EPA TRI: particularly useful for facilities and parent links

EPA’s downloadable TRI files provide facility names, addresses, and coordinates. Its documentation also identifies primary six-digit NAICS and parent-company fields, including the entity controlling the reporting facility and standardized parent names. ([US EPA][10])

I would use TRI primarily for **facility identification, geographic coverage, NAICS, and parent-link corroboration**, rather than as an employment source. It is an inventory of TRI-reporting facilities, not a general business register. ([US EPA][10])

Also inspect the time meaning of its fields: EPA describes its standardized U.S. parent field as intended to reflect the **current** ultimate U.S. parent. I would not silently treat that field as contemporaneous ownership in every historical reporting year. 

### Do not make SIC-to-NAICS conversion your primary classification method

NAICS classifies **establishments**. A diversified parent company’s single SIC code is therefore not a sufficient basis for assigning one detailed NAICS code to every subsidiary and worksite. ([Census.gov][13])

My preferred order would be:

1. **Reported establishment NAICS**, where available.
2. **Classification from a sufficiently specific business description**, retained as an inference.
3. **SIC-to-NAICS concordance as a fallback**, with ambiguity preserved.

SIC-to-NAICS correspondence is not universally one-to-one. Keep the classification edition and distinguish reported codes from crosswalk-derived or model-inferred codes. ([US EPA][14])

For locations described in 10-K Item 2, apply the same caution: the rule concerns material principal properties and allows collective descriptions, rather than requiring a complete address-level worksite inventory. ([eCFR][15])

## 5. A practical open-source implementation

I would build three linked outputs rather than one oversized company table:

**Company table:** dated membership, CIK, company name, SIC, reported business address, and reported workforce observations.

**Entity and relationship tables:** subsidiary names, jurisdictions, identifiers where available, relationship types, and the filings or GLEIF records supporting each relationship.

**Establishment table:** observed workplaces, addresses, NAICS, establishment employment where available, and evidence linking each workplace to an entity or group.

Every observation should carry both a **reference date** and a **retrieval date**, plus the source and a matching/extraction status. Preserve unmatched and ambiguous records for review.

For EDGAR extraction, **EdgarTools** is an MIT-licensed Python package. Its current documentation includes subsidiary extraction through `tenk.subsidiaries`, based on Exhibit 21. ([GitHub][16])

The documented interface supports a starting point like this:

```python
# Install: uv add edgartools

from edgar import Company, set_identity

# Replace with your actual identifying contact information.
set_identity("Your Name your.email@example.com")

company = Company("AAPL")
filing = company.get_filings(form="10-K").latest()

if filing is None:
    raise RuntimeError("No 10-K found; check the issuer and filing form.")

tenk = filing.obj()

# A parsed disclosure, not proof of a complete subsidiary inventory.
print(tenk.subsidiaries)
```

For a production pipeline, I would pin the package version, save the original exhibits, and validate a sample manually before scaling. A parser returning no subsidiaries should trigger review—not establish that none exist.

Direct EDGAR APIs are free and require no API key. SEC access rules require appropriate identification and limit automated traffic to no more than 10 requests per second in aggregate; caching and conservative request rates are sensible defaults. ([SEC][5])

## Recommendation

**Start with a Dow-sized pilot, then expand to the S&P 500:**

**Dated membership → EDGAR company profiles and Exhibit 21 → GLEIF relationships → OSHA/EPA establishment enrichment.**

That gives you a defensible free-data product comprising **company-level profiles, disclosed subsidiaries, supported ownership relationships, and observed workplaces**. Corporate workforce totals and company-level SIC will generally be a different layer from establishment NAICS and employment; keeping those layers separate is what makes the resulting database useful rather than misleading.

[1]: https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list "SEC.gov | Standard Industrial Classification (SIC) Code List"
[2]: https://www.spglobal.com/spdji/en/indices/equity/sp-500/ "S&P 500® | S&P Dow Jones Indices"
[3]: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies "List of S&P 500 companies - Wikipedia"
[4]: https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-dow-jones-industrial-average-etf-trust-dia "DIA: State Street® SPDR® Dow Jones Industrial Average® ETF Trust"
[5]: https://www.sec.gov/search-filings/edgar-application-programming-interfaces "SEC.gov | EDGAR Application Programming Interfaces (APIs)"
[6]: https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.600/section-229.601 "eCFR :: 17 CFR 229.601 -- (Item 601) Exhibits."
[7]: https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-who-owns-whom "Level 2 Data: Who Owns Whom - LEI Data: Access & Use - LEI Data – GLEIF"
[8]: https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.100/section-229.101 "eCFR :: 17 CFR 229.101 -- (Item 101) Description of business."
[9]: https://www.osha.gov/itadata?utm_source=chatgpt.com "Injury Tracking Application (ITA) Data"
[10]: https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present "TRI Basic Data Files: Calendar Years 1987-Present | US EPA"
[11]: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a10-kexhibit21109272025.htm "www.sec.gov"
[12]: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm "aapl-20250927"
[13]: https://www.census.gov/naics/ "North American Industry Classification System (NAICS) U.S. Census Bureau"
[14]: https://www.epa.gov/system/files/documents/2025-09/basic_data_files_documentation_august_2024.pdf "Microsoft Word - TRI Basic Data File documentation.docx"
[15]: https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.100/section-229.102 "eCFR :: 17 CFR 229.102 -- (Item 102) Description of property."
[16]: https://github.com/dgunning/edgartools "GitHub - dgunning/edgartools: Read and analyze SEC EDGAR filings in Python. 10-K, 8-K, XBRL financials, Form 3/4/5, 13F, ADV — clean API, well-typed, MIT-licensed. · GitHub"
