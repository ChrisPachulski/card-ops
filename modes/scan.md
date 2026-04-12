# Mode: Parse Statements

## Trigger
User drops statement PDFs into `statements/` or asks to analyze spending.

## Inputs
- PDF statements in `statements/`
- `config/profile.yml` (to update with parsed data)

## Execution Steps

### 1. Detect Statements
- Read `statements/` directory for new PDF files
- Identify issuer from statement format (header, logo, layout)
- Extract statement period (start/end dates)

### 2. Parse Transactions
For each statement, extract:
- Transaction date
- Merchant name
- Amount
- Category (from merchant or statement categorization)

### 3. Categorize Spending
Map transactions to standard categories:
- Groceries (grocery stores, supermarkets)
- Dining (restaurants, fast food, coffee shops)
- Travel (airlines, hotels, car rental, rideshare)
- Gas (gas stations)
- Online shopping (Amazon, online retailers)
- Subscriptions (streaming, software, memberships)
- Utilities (electric, water, internet, phone)
- Other (everything else)

### 4. Calculate Aggregates
- Monthly total by category
- Average across statement periods
- Identify top 5 merchants by spend
- Flag seasonal patterns (e.g., holiday spending spikes)

### 5. Compare to Profile
- Show profile estimates vs actual spend
- Highlight categories where actual differs significantly from estimate
- Suggest profile updates

### 6. Opportunity Analysis
- For each category: what's the best earn rate available?
- Compare to current card earn rates
- Calculate potential annual rewards gap (what you earn now vs what you could earn)
- Flag categories with no optimized card coverage

### 7. Output
- Print spending summary to console
- Offer to update `config/profile.yml` with actual spending data
- Store parsed data for future evaluations
