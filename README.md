# Customer Segmentation & Retention Alerts (RFM Analysis)

Segmented 5,878 online-retail customers with RFM analysis in Python, built a 3-page Power BI dashboard, and automated win-back alerts for high-value customers using Make.com.

![Segments dashboard](screenshots/dashboard_segments.png)

## Business problem
A retailer treats every customer the same. Which customers drive revenue, which are slipping away, and who should the marketing team contact first?

## Dataset
[Online Retail II (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii): transactions from a UK-based online gift retailer, Dec 2009 to Dec 2011 (two CSV files combined).
- 1,067,371 raw rows, 779,425 after cleaning
- 5,878 unique customers

## Approach
1. **Cleaning (pandas):** removed rows with no Customer ID, cancelled invoices (start with "C"), non-positive quantities and prices, and duplicates (including the overlap between the two files).
2. **RFM metrics:** Recency (days since last purchase, measured from one day after the last transaction), Frequency (unique invoices), Monetary (total spend).
3. **Scoring:** each metric scored 1-5 with quintiles (`pd.qcut`); frequency was ranked first because many customers share the same value.
4. **Segmentation:** rule-based segments from R and F scores: Champions, Loyal Customers, Potential Loyalists, New Customers, Need Attention, Cant Lose Them, At Risk, Hibernating, Lost.
5. **Dashboard (Power BI):** Overview, Segments, and an Action List of at-risk customers.
6. **Automation (Make.com):** a scenario reads the top at-risk customers from Google Sheets and emails an alert for high-spend customers.

## Key findings
| Finding | Detail |
|---|---|
| Revenue is concentrated | Champions are 25.2% of customers but generate 69.2% of revenue |
| Biggest win-back target | Cant Lose Them: 353 customers who last bought about 344 days ago but spent about £3,090 each on average |
| Low priority | Lost customers (816) average a single order |

## Recommendations
| Segment | Action |
|---|---|
| Champions | Early access, loyalty rewards, referral program |
| Loyal Customers | Bundles and upsell offers |
| Cant Lose Them / At Risk | Personalised win-back offer, highest priority |
| New Customers | Onboarding email and a second-purchase incentive |
| Hibernating / Lost | Low-cost reactivation campaign only |

## Dashboard
| Overview | Segments | Action List |
|---|---|---|
| ![](screenshots/dashboard_overview.png) | ![](screenshots/dashboard_segments.png) | ![](screenshots/dashboard_actions.png) |

Power BI file: `rfm_dashboard.pbix`

## Automation
![Make.com scenario](screenshots/make_scenario.png)

The scenario watches a Google Sheet of the top 50 at-risk customers by spend and sends an email alert for each customer who has spent over £1,000.

## Limitations and next steps
- Segments use fixed rules on R and F scores; K-means clustering could find data-driven groups.
- Add customer lifetime value (CLV) to prioritise win-back spend.
- The dataset ends in 2011, so recency reflects that snapshot date.

## How to run
```bash
pip install pandas numpy openpyxl matplotlib
# download the two CSV files from the dataset link and set their paths in DATA_FILES
python rfm_segmentation.py
```
Outputs are written to `output/` (segments, summary, monthly and country revenue, alert list). Open them in Power BI.

## Tools
Python (pandas, matplotlib), Power BI, Make.com, Google Sheets
