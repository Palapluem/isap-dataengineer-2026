-- Top ministries or entities by OCSC manpower headcount.
SELECT
    agency_name,
    entity_type,
    sum(headcount) AS headcount
FROM mart.fact_government_manpower
WHERE metric_name = 'civil_servant'
GROUP BY 1, 2
ORDER BY headcount DESC
LIMIT 10;

-- CGD budget execution performance by ministry.
SELECT
    entity_name,
    expense_category,
    budget_after_transfer_million_baht,
    disbursement_million_baht,
    disbursement_pct
FROM mart.fact_budget_execution
WHERE entity_type = 'ministry'
  AND expense_category = 'total'
  AND report_type = 'disbursement'
ORDER BY disbursement_pct ASC
LIMIT 10;

-- Entities with low expenditure against the monthly target.
SELECT
    entity_name,
    expense_category,
    expenditure_pct,
    monthly_target_gap_pct
FROM mart.fact_budget_execution
WHERE report_type = 'expenditure'
  AND expense_category = 'total'
  AND monthly_target_gap_pct IS NOT NULL
ORDER BY monthly_target_gap_pct ASC
LIMIT 10;

-- Exact-name join candidates between OCSC workforce and CGD budget data.
SELECT
    m.agency_name,
    sum(m.headcount) AS civil_servant_headcount,
    max(b.budget_after_transfer_million_baht) AS budget_after_transfer_million_baht,
    max(b.disbursement_pct) AS disbursement_pct
FROM mart.fact_government_manpower m
JOIN mart.fact_budget_execution b
  ON lower(regexp_replace(m.agency_name, '\\s+', '', 'g')) =
     lower(regexp_replace(b.entity_name, '\\s+', '', 'g'))
WHERE m.metric_name = 'civil_servant'
  AND b.expense_category = 'total'
  AND b.report_type = 'disbursement'
GROUP BY 1
ORDER BY civil_servant_headcount DESC
LIMIT 10;
