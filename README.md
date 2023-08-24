# orchestration-database
A package for designing and implementing ETL. This repository intends to use the following infrastructure in [`Azure`](https://azure.microsoft.com/en-us), which has a _landing zone_ represented by a [`Storage account`](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview) where the data is located. This storage has 2 stages, the first one containing the _rawdata_ and the second one containing the _processed_ data in `.parquet` format to be uploaded to the [`SQL server database`](https://azure.microsoft.com/en-us/products/azure-sql/database/). The scheme of this solution is hybrid, having processes that run locally and processes that are managed to run using [`Azure ML`](https://azure.microsoft.com/en-us/products/machine-learning/). For a more detailed description, see below.   

<p align="center">
<img src="diagram.png" width=55% height=55%>
</p>