/**
 * api.js
 * Central API client for the Cloud Cost Calculator frontend.
 *
 * Design principles:
 *  - All prices in USD (currency param stubbed for GBP/EUR readiness)
 *  - Every public function throws a structured ApiError on failure
 *  - Base URL from REACT_APP_API_URL env var (falls back to localhost:8000)
 *  - No axios dependency — uses native fetch with a thin wrapper
 */

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name    = "ApiError";
    this.status  = status;   // HTTP status code
    this.detail  = detail;   // backend detail string
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function request(method, path, body = null, currency = "USD") {
  const url     = `${BASE_URL}${path}`;
  const headers = { "Content-Type": "application/json" };

  // Thread currency as a query param on GET requests for future use
  const finalUrl =
    method === "GET" && currency !== "USD"
      ? `${url}${url.includes("?") ? "&" : "?"}currency=${currency}`
      : url;

  const options = {
    method,
    headers,
    ...(body !== null ? { body: JSON.stringify(body) } : {}),
  };

  let response;
  try {
    response = await fetch(finalUrl, options);
  } catch (networkErr) {
    throw new ApiError(
      "Network error — is the backend running?",
      0,
      networkErr.message
    );
  }

  // 204 No Content — nothing to parse
  if (response.status === 204) return null;

  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      `Unexpected response from server (status ${response.status})`,
      response.status,
      null
    );
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      (typeof data === "string" ? data : JSON.stringify(data));
    throw new ApiError(
      `Request failed: ${detail}`,
      response.status,
      detail
    );
  }

  return data;
}

// Shorthand helpers
const get    = (path, currency)       => request("GET",    path, null,  currency);
const post   = (path, body, currency) => request("POST",   path, body,  currency);
const patch  = (path, body, currency) => request("PATCH",  path, body,  currency);
const del    = (path)                 => request("DELETE", path);


// ===========================================================================
// BOM endpoints
// ===========================================================================

/**
 * Create a new Bill of Materials.
 *
 * @param {string}  name                  - Human-readable BOM name
 * @param {string}  cloudProvider         - "aws" | "azure" | "gcp"
 * @param {boolean} azureHybridBenefit    - Azure only; true = customer owns existing licenses
 * @param {Array}   services              - Optional initial service list (see addServices)
 * @param {string}  currency              - "USD" (GBP/EUR planned)
 * @returns {Promise<BOMResponse>}
 */
export async function createBOM(
  name,
  cloudProvider,
  azureHybridBenefit = false,
  services           = [],
  currency           = "USD"
) {
  return post("/api/v1/bom", {
    name,
    cloud_provider:        cloudProvider,
    azure_hybrid_benefit:  azureHybridBenefit,
    services,
    currency,
  });
}

/**
 * List all BOMs (summary — no deep service configs).
 * @returns {Promise<BOMResponse[]>}
 */
export async function listBOMs() {
  return get("/api/v1/bom");
}

/**
 * Get a single BOM with full service configs.
 * @param {number} bomId
 * @returns {Promise<BOMResponse>}
 */
export async function getBOM(bomId) {
  return get(`/api/v1/bom/${bomId}`);
}

/**
 * Replace the services list on an existing BOM.
 * Also used to update azure_hybrid_benefit or currency.
 *
 * @param {number}  bomId
 * @param {Array}   services
 * @param {object}  opts - { azureHybridBenefit?, currency? }
 * @returns {Promise<BOMResponse>}
 */
export async function updateBOMServices(bomId, services, opts = {}) {
  const body = { services };
  if (opts.azureHybridBenefit !== undefined)
    body.azure_hybrid_benefit = opts.azureHybridBenefit;
  if (opts.currency !== undefined)
    body.currency = opts.currency;
  return patch(`/api/v1/bom/${bomId}/services`, body);
}

/**
 * Delete a BOM and all its associated scenarios.
 * @param {number} bomId
 * @returns {Promise<null>}
 */
export async function deleteBOM(bomId) {
  return del(`/api/v1/bom/${bomId}`);
}


// ===========================================================================
// Scenario endpoints
// ===========================================================================

/**
 * Generate (or regenerate) cost scenarios for a BOM.
 * Fetches live prices, applies discount matrix, persists results.
 *
 * @param {number} bomId
 * @param {string} currency - "USD" (GBP/EUR planned)
 * @returns {Promise<ScenarioResponse>}
 */
export async function generateScenarios(bomId, currency = "USD") {
  return post(`/api/v1/scenarios/${bomId}/generate`, null, currency);
}

/**
 * Get previously generated scenarios for a BOM.
 * Returns 404-wrapped ApiError if none exist yet.
 *
 * @param {number} bomId
 * @param {string} currency
 * @returns {Promise<ScenarioResponse>}
 */
export async function getScenarios(bomId, currency = "USD") {
  return get(`/api/v1/scenarios/${bomId}`, currency);
}

/**
 * Delete all scenarios for a BOM (BOM itself is kept).
 * @param {number} bomId
 * @returns {Promise<null>}
 */
export async function deleteScenarios(bomId) {
  return del(`/api/v1/scenarios/${bomId}`);
}


// ===========================================================================
// Service config helpers
// Builds correctly-shaped service config objects for each provider + type.
// Used by BillOfMaterials.js form builders.
// ===========================================================================

/**
 * Supported service types per provider.
 * Keys match the service_type field expected by the backend.
 */
export const SERVICE_TYPES = {
  aws: [
    { value: "compute",    label: "EC2 (Compute)",          icon: "💻" },
    { value: "database",   label: "RDS (Database)",         icon: "🗄️" },
    { value: "cache",      label: "ElastiCache",            icon: "⚡" },
    { value: "serverless", label: "Lambda (Serverless)",    icon: "λ"  },
    { value: "storage",    label: "S3 (Object Storage)",    icon: "🪣" },
    { value: "container",  label: "ECS/EKS Fargate",        icon: "🐳" },
    { value: "cdn",        label: "CloudFront (CDN)",       icon: "🌐" },
    { value: "nosql",      label: "DynamoDB (NoSQL)",       icon: "📊" },
  ],
  azure: [
    { value: "compute",    label: "Virtual Machines",       icon: "💻" },
    { value: "database",   label: "SQL Database",           icon: "🗄️" },
    { value: "nosql",      label: "Cosmos DB",              icon: "🌍" },
    { value: "container",  label: "AKS (Kubernetes)",       icon: "🐳" },
    { value: "storage",    label: "Blob Storage",           icon: "🪣" },
    { value: "serverless", label: "Functions",              icon: "λ"  },
    { value: "cache",      label: "Redis Cache",            icon: "⚡" },
  ],
  gcp: [
    { value: "compute",    label: "Compute Engine",         icon: "💻" },
    { value: "database",   label: "Cloud SQL",              icon: "🗄️" },
    { value: "container",  label: "GKE (Kubernetes)",       icon: "🐳" },
    { value: "storage",    label: "Cloud Storage",          icon: "🪣" },
    { value: "serverless", label: "Cloud Functions",        icon: "λ"  },
    { value: "nosql",      label: "Firestore",              icon: "🔥" },
    { value: "cache",      label: "Memorystore (Redis)",    icon: "⚡" },
    { value: "analytics",  label: "BigQuery",               icon: "📊" },
  ],
};

/**
 * Default config values per provider + service type.
 * Pre-populates the "Add Service" form with sensible defaults.
 */
export const DEFAULT_SERVICE_CONFIGS = {
  aws: {
    compute: {
      instance_type: "m5.large",
      quantity:       1,
      region:         "us-east-1",
      os:             "linux",
    },
    database: {
      engine:        "mysql",
      instance_type: "db.m5.large",
      storage_gb:    100,
      region:        "us-east-1",
      replicas:       0,
    },
    cache: {
      node_type:  "cache.m5.large",
      num_nodes:   1,
      engine:     "redis",
      region:     "us-east-1",
    },
    serverless: {
      memory_mb:             512,
      avg_duration_ms:       200,
      monthly_invocations:   1000000,
      region:                "us-east-1",
    },
    storage: {
      storage_gb:     100,
      get_requests:   10000,
      put_requests:   1000,
      region:         "us-east-1",
    },
    container: {
      vcpu:             1,
      memory_gb:        2,
      num_tasks:        1,
      hours_per_month:  730,
      region:           "us-east-1",
    },
    cdn: {
      data_transfer_gb: 100,
      https_requests:   1000000,
      region:           "us-east-1",
    },
    nosql: {
      storage_gb:           10,
      read_request_units:   1000000,
      write_request_units:  500000,
      region:               "us-east-1",
    },
  },

  azure: {
    compute: {
      size:     "Standard_D2s_v3",
      quantity:  1,
      region:   "eastus",
      os:       "linux",
    },
    database: {
      tier:       "GeneralPurpose",
      vcores:      4,
      storage_gb:  100,
      region:     "eastus",
    },
    nosql: {
      request_units:  400,
      storage_gb:      10,
      region:         "eastus",
    },
    container: {
      node_size:   "Standard_D2s_v3",
      node_count:   3,
      os:          "linux",
      region:      "eastus",
    },
    storage: {
      storage_gb:       100,
      read_operations:  10000,
      write_operations: 1000,
      region:           "eastus",
    },
    serverless: {
      monthly_executions: 1000000,
      avg_duration_ms:    200,
      memory_mb:          512,
      region:             "eastus",
    },
    cache: {
      tier:      "Standard",
      capacity:   1,
      region:    "eastus",
    },
  },

  gcp: {
    compute: {
      machine_type: "n2-standard-2",
      quantity:      1,
      region:       "us-central1",
      os:           "linux",
    },
    database: {
      tier:       "db-n1-standard-2",
      engine:     "mysql",
      storage_gb:  100,
      replicas:    0,
      region:      "us-central1",
    },
    container: {
      machine_type: "n2-standard-2",
      node_count:    3,
      os:           "linux",
      region:       "us-central1",
    },
    storage: {
      storage_gb:   100,
      class_a_ops:  10000,
      class_b_ops:  100000,
      region:       "us-central1",
    },
    serverless: {
      monthly_invocations: 1000000,
      avg_duration_ms:     200,
      memory_mb:           256,
      region:              "us-central1",
    },
    nosql: {
      storage_gb:         10,
      reads_per_month:    1000000,
      writes_per_month:   500000,
      deletes_per_month:  100000,
      region:             "us-central1",
    },
    cache: {
      tier:        "standard",
      capacity_gb:  1,
      region:      "us-central1",
    },
    analytics: {
      storage_gb:            100,
      tb_queried_per_month:   1,
      region:                "us-central1",
    },
  },
};

/**
 * Human-readable field labels for the service config forms.
 * Used by BillOfMaterials.js to render labeled inputs.
 */
export const CONFIG_FIELD_LABELS = {
  // Common
  region: {
    label:   "Region",
    type:    "select",
    options: [
        // AWS regions
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1",
        // Azure regions
        "eastus", "eastus2", "westus", "westus2", "westus3",
        "northeurope", "westeurope", "uksouth", "ukwest",
        "southeastasia", "eastasia", "australiaeast",
        "centralindia", "brazilsouth", "canadacentral",
        // GCP regions
        "us-central1", "us-east1", "us-east4", "us-west1", "us-west2",
        "europe-west1", "europe-west2", "europe-west3", "europe-west4",
        "asia-south1", "asia-southeast1", "asia-east1", "asia-northeast1",
        "australia-southeast1", "southamerica-east1",
    ],
  },
  quantity:             { label: "Number of Instances",      type: "number" },
  os:                   { label: "Operating System",         type: "select",
                          options: ["linux", "windows"]                      },
  storage_gb:           { label: "Storage (GB)",             type: "number" },
  replicas:             { label: "Read Replicas",            type: "number" },

  // AWS EC2
  instance_type:        { label: "Instance Type",            type: "text"   },

  // AWS RDS
  engine:               { label: "Database Engine",          type: "select",
                          options: ["mysql","postgres","oracle","sqlserver","aurora"] },

  // AWS ElastiCache
  node_type:            { label: "Node Type",                type: "text"   },
  num_nodes:            { label: "Number of Nodes",          type: "number" },

  // Serverless (Lambda / Azure Functions / GCP Functions)
  memory_mb:            { label: "Memory (MB)",              type: "number" },
  avg_duration_ms:      { label: "Avg Duration (ms)",        type: "number" },
  monthly_invocations:  { label: "Monthly Invocations",      type: "number" },
  monthly_executions:   { label: "Monthly Executions",       type: "number" },

  // S3 / Blob / GCS
  get_requests:         { label: "Monthly GET Requests",     type: "number" },
  put_requests:         { label: "Monthly PUT Requests",     type: "number" },
  read_operations:      { label: "Monthly Read Operations",  type: "number" },
  write_operations:     { label: "Monthly Write Operations", type: "number" },
  class_a_ops:          { label: "Class A Operations (writes)", type: "number" },
  class_b_ops:          { label: "Class B Operations (reads)",  type: "number" },

  // Fargate / Container
  vcpu:                 { label: "vCPU",                     type: "number" },
  memory_gb:            { label: "Memory (GB)",              type: "number" },
  num_tasks:            { label: "Number of Tasks",          type: "number" },
  hours_per_month:      { label: "Hours per Month",          type: "number" },

  // CloudFront
  data_transfer_gb:     { label: "Data Transfer Out (GB)",   type: "number" },
  https_requests:       { label: "Monthly HTTPS Requests",   type: "number" },

  // DynamoDB / Firestore / Cosmos
  read_request_units:   { label: "Read Request Units/mo",    type: "number" },
  write_request_units:  { label: "Write Request Units/mo",   type: "number" },
  request_units:        { label: "Provisioned RU/s",         type: "number" },
  reads_per_month:      { label: "Reads per Month",          type: "number" },
  writes_per_month:     { label: "Writes per Month",         type: "number" },
  deletes_per_month:    { label: "Deletes per Month",        type: "number" },

  // Azure VM / AKS
  size:                 { label: "VM Size",                  type: "text"   },
  node_size:            { label: "Node VM Size",             type: "text"   },
  node_count:           { label: "Number of Nodes",          type: "number" },

  // Azure SQL
  tier:                 { label: "Service Tier",             type: "select",
                          options: ["GeneralPurpose", "BusinessCritical", "basic", "standard", "premium"] },
  vcores:               { label: "vCores",                   type: "number" },

  // Azure Redis
  capacity:             { label: "Cache Size (index 0–6)",   type: "number" },

  // GCP Compute
  machine_type:         { label: "Machine Type",             type: "text"   },

  // GCP Cloud SQL
  // (tier already defined above)

  // GCP Memorystore
  capacity_gb:          { label: "Capacity (GB)",            type: "number" },

  // BigQuery
  tb_queried_per_month: { label: "TB Queried per Month",     type: "number" },
};

/**
 * Pricing model display metadata for the Scenarios UI.
 * Controls badge colour and sort order.
 */
export const PRICING_MODEL_META = {
  payg:    { label: "Pay-As-You-Go", color: "#6b7280", badge: "bg-gray-100 text-gray-700",  order: 0 },
  ri_1yr:  { label: "1-Year Reserved", color: "#2563eb", badge: "bg-blue-100 text-blue-700", order: 1 },
  ri_3yr:  { label: "3-Year Reserved", color: "#1d4ed8", badge: "bg-blue-200 text-blue-800", order: 2 },
  sp_1yr:  { label: "1-Year Savings Plan", color: "#7c3aed", badge: "bg-purple-100 text-purple-700", order: 3 },
  sp_3yr:  { label: "3-Year Savings Plan", color: "#6d28d9", badge: "bg-purple-200 text-purple-800", order: 4 },
  cud_1yr: { label: "1-Year Committed Use", color: "#0891b2", badge: "bg-cyan-100 text-cyan-700", order: 5 },
  cud_3yr: { label: "3-Year Committed Use", color: "#0e7490", badge: "bg-cyan-200 text-cyan-800", order: 6 },
  sud:     { label: "Sustained Use Discount", color: "#059669", badge: "bg-emerald-100 text-emerald-700", order: 7 },
  ahb:     { label: "Azure Hybrid Benefit", color: "#d97706", badge: "bg-amber-100 text-amber-700", order: 8 },
};
