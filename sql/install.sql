CREATE TABLE IF NOT EXISTS `{target_table}` (
    sales_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    sales_date DATE NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    month TINYINT UNSIGNED NOT NULL,
    month_name CHAR(3) NOT NULL,
    naics_code VARCHAR(30) NULL,
    kind_of_business VARCHAR(255) NOT NULL,
    sales DECIMAL(18,2) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sales_id),
    UNIQUE KEY uk_mrts_business_month (sales_date, naics_code, kind_of_business),
    KEY idx_mrts_date (sales_date),
    KEY idx_mrts_year_month (year, month),
    KEY idx_mrts_business (kind_of_business),
    CONSTRAINT chk_mrts_month CHECK (month BETWEEN 1 AND 12)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `{staging_table}` (
    sales_date DATE NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    month TINYINT UNSIGNED NOT NULL,
    month_name CHAR(3) NOT NULL,
    naics_code VARCHAR(30) NULL,
    kind_of_business VARCHAR(255) NOT NULL,
    sales DECIMAL(18,2) NULL,
    KEY idx_stg_mrts_date (sales_date)
) ENGINE=InnoDB;
