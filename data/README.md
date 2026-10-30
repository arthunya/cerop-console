# Data

Raw and processed data are not stored in this repo: the raw files are large, and they belong to their publishers. Download them as below.

## Raw datasets

| Dataset | Download | License | Expected file |
|---|---|---|---|
| Taiwanese Bankruptcy Prediction | [UCI ML Repository](https://archive.ics.uci.edu/dataset/572/taiwanese+bankruptcy+prediction) (also on Kaggle as `fedesoriano/company-bankruptcy-prediction`) | CC BY 4.0 | `data.csv` (6,819 rows, 96 columns) |
| DataCo Smart Supply Chain | [Mendeley Data](https://data.mendeley.com/datasets/8gx2fvg2k6/5) (also on Kaggle as `shashwatwork/dataco-smart-supply-chain-for-big-data-analysis`) | CC BY 4.0 | `DataCoSupplyChainDataset.csv` (180,519 rows) |
| Global Supply Chain Pressure Index | [Federal Reserve Bank of New York](https://www.newyorkfed.org/research/policy/gscpi) | NY Fed website terms of use | `gscpi_data.xls` |

Citations:

- Liang, D., Lu, C.-C., Tsai, C.-F., & Shih, G.-A. (2016). Financial ratios and corporate governance indicators in bankruptcy prediction. *European Journal of Operational Research*, 252(2). Dataset: doi:10.24432/C5004D.
- Constante, F., Silva, F., & Pereira, A. (2019). DataCo smart supply chain for big data analysis [Data set]. Mendeley Data. doi:10.17632/8gx2fvg2k6.5.
- Benigno, G., di Giovanni, J., Groen, J., & Noble, A. (2022). The GSCPI: A new barometer of global supply chain pressures. Federal Reserve Bank of New York Staff Report 1017.

## Processed data

Notebook `03` writes the processed train/test CSVs; `05b` reads the corrected 27-feature operations files (`operations_*_processed_v2.csv`). Notebooks `06` and `07` read them from the folder set in `AIT506_DIR`, using the same layout as the course folder:

```
$AIT506_DIR/
  Week 3/Dataset/DataCoSupplyChainDataset.csv
  Week 4/Final/gscpi_data.xls
  Week 4/Final/Outputs/financial_X_{train,test}_clean_unscaled.csv
  Week 5/GROUP/Ankit/data/financial_{X,y}_{train,test}*.csv
  Week 6/Group/data/operations_{X,y}_{train,test}*_v2.csv
```

## `sample/`

The 8 financial and 8 operations cases used by the original live demo (`scripts/score_new_cases.py`, notebook `06`). They are real held-out test rows with the label removed. `counterparty_name` and `order_ref` are placeholder display names, not real companies or orders.
