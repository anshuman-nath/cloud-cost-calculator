-- Cloud Cost Calculator Database Schema

-- Bill of Materials table
CREATE TABLE IF NOT EXISTS bill_of_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cloud_provider VARCHAR(50) NOT NULL,
    services JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'user'
);

-- Cost Scenarios table
CREATE TABLE IF NOT EXISTS cost_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_id INTEGER NOT NULL,
    scenario_name VARCHAR(100) NOT NULL,
    pricing_model VARCHAR(50) NOT NULL,
    total_monthly_cost REAL NOT NULL DEFAULT 0.0,
    total_annual_cost REAL NOT NULL DEFAULT 0.0,
    savings_vs_payg REAL DEFAULT 0.0,
    savings_percentage REAL DEFAULT 0.0,
    itemized_costs JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bom_id) REFERENCES bill_of_materials(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bom_provider ON bill_of_materials(cloud_provider);
CREATE INDEX IF NOT EXISTS idx_bom_created ON bill_of_materials(created_at);
CREATE INDEX IF NOT EXISTS idx_scenario_bom ON cost_scenarios(bom_id);
CREATE INDEX IF NOT EXISTS idx_scenario_model ON cost_scenarios(pricing_model);

-- Pricing cache table (optional - for caching API responses)
CREATE TABLE IF NOT EXISTS pricing_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    pricing_data JSON NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pricing_cache_key ON pricing_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_pricing_expires ON pricing_cache(expires_at);
