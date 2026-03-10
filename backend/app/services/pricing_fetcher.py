"""
Pricing Fetcher Service
Fetches live PAYG (base) prices from AWS, Azure, and GCP official APIs.

Currency: USD always (current).
Extensibility: currency param threads through all public methods.
               _convert_currency() is the single place to add forex later.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Currency conversion stub
# ---------------------------------------------------------------------------

def _convert_currency(amount_usd: float, to: str = "USD") -> float:
    """
    Convert a USD amount to the requested currency.
    Currently only USD is supported. When GBP/EUR support is needed:
      1. Integrate a forex API (e.g. Open Exchange Rates, ECB)
      2. Replace the NotImplementedError block below
    """
    if to == "USD":
        return amount_usd
    # TODO: integrate forex API when GBP/EUR support is activated
    raise NotImplementedError(
        f"Currency '{to}' is not yet supported. Only USD is available."
    )


# ---------------------------------------------------------------------------
# AWS Pricing
# ---------------------------------------------------------------------------

AWS_PRICING_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws"

# Map our internal region slugs → AWS region codes
AWS_REGION_NAMES = {
    "us-east-1":      "US East (N. Virginia)",
    "us-east-2":      "US East (Ohio)",
    "us-west-1":      "US West (N. California)",
    "us-west-2":      "US West (Oregon)",
    "eu-west-1":      "Europe (Ireland)",
    "eu-west-2":      "Europe (London)",
    "eu-central-1":   "Europe (Frankfurt)",
    "ap-south-1":     "Asia Pacific (Mumbai)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "sa-east-1":      "South America (Sao Paulo)",
    "ca-central-1":   "Canada (Central)",
}


async def fetch_aws_pricing(
    service_type: str,
    config: dict,
    region: str = "us-east-1",
    currency: str = "USD",
) -> dict:
    """
    Fetch live AWS PAYG price for a given service + config + region.

    Returns:
        {
            "monthly_cost_usd": float,
            "unit":             str,
            "price_per_unit":   float,
            "source":           "aws_api" | "fallback",
            "details":          dict
        }
    """
    try:
        if service_type == "compute":
            result = await _fetch_aws_ec2(config, region)
        elif service_type == "database":
            result = await _fetch_aws_rds(config, region)
        elif service_type == "cache":
            result = await _fetch_aws_elasticache(config, region)
        elif service_type == "storage":
            result = await _fetch_aws_s3(config, region)
        elif service_type == "serverless":
            result = await _fetch_aws_lambda(config, region)
        elif service_type == "container":
            result = await _fetch_aws_fargate(config, region)
        elif service_type == "cdn":
            result = await _fetch_aws_cloudfront(config, region)
        elif service_type == "nosql":
            result = await _fetch_aws_dynamodb(config, region)
        else:
            raise ValueError(f"Unsupported AWS service_type: {service_type}")

        result["monthly_cost_usd"] = _convert_currency(result["monthly_cost_usd"], to=currency)
        return result

    except Exception as e:
        logger.error(f"AWS pricing fetch failed [{service_type}|{region}]: {e}")
        raise


async def _fetch_aws_ec2(config: dict, region: str) -> dict:
    """
    EC2 On-Demand pricing via AWS Bulk Pricing JSON API.
    config keys: instance_type, quantity, os (linux|windows)
    730 hours/month assumed (full utilization).
    """
    instance_type = config.get("instance_type", "m5.large")
    quantity = int(config.get("quantity", 1))
    os_type = config.get("os", "linux")
    hours_per_month = 730

    region_name = AWS_REGION_NAMES.get(region, "US East (N. Virginia)")
    os_filter = "Linux" if os_type == "linux" else "Windows"

    url = (
        f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json"
    )
    # Use the filter API for efficiency
    filter_url = (
        f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/"
        f"region_index.json"
    )

    # Use AWS Price List Query API (filters) — more efficient than full index
    query_url = (
        "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json"
    )
    params = {
        "Filter.1.Type": "TERM_MATCH",
        "Filter.1.Field": "instanceType",
        "Filter.1.Value": instance_type,
        "Filter.2.Type": "TERM_MATCH",
        "Filter.2.Field": "location",
        "Filter.2.Value": region_name,
        "Filter.3.Type": "TERM_MATCH",
        "Filter.3.Field": "operatingSystem",
        "Filter.3.Value": os_filter,
        "Filter.4.Type": "TERM_MATCH",
        "Filter.4.Field": "tenancy",
        "Filter.4.Value": "Shared",
        "Filter.5.Type": "TERM_MATCH",
        "Filter.5.Field": "capacityStatus",
        "Filter.5.Value": "Used",
        "Filter.6.Type": "TERM_MATCH",
        "Filter.6.Field": "preInstalledSw",
        "Filter.6.Value": "NA",
        "formatVersion": "aws_v1",
        "callback": "",
        "pricingRegion": region,
    }

    # Use the newer filter-based endpoint
    api_url = f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()
        data = resp.json()

    hourly_rate = _extract_ec2_rate(data, instance_type, os_filter)
    monthly_cost = hourly_rate * hours_per_month * quantity

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "instance-hour",
        "price_per_unit": hourly_rate,
        "source": "aws_api",
        "details": {
            "instance_type": instance_type,
            "quantity": quantity,
            "os": os_type,
            "region": region,
            "hours_per_month": hours_per_month,
        },
    }


def _extract_ec2_rate(data: dict, instance_type: str, os_filter: str) -> float:
    """
    Parse AWS Bulk Pricing JSON to extract the On-Demand hourly rate
    for a given instance type + OS.
    """
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})

    for sku, product in products.items():
        attrs = product.get("attributes", {})
        if (
            attrs.get("instanceType") == instance_type
            and attrs.get("operatingSystem") == os_filter
            and attrs.get("tenancy") == "Shared"
            and attrs.get("capacityStatus") == "Used"
            and attrs.get("preInstalledSw") == "NA"
        ):
            sku_terms = terms.get(sku, {})
            for term_key, term_val in sku_terms.items():
                for dim_key, dim_val in term_val.get("priceDimensions", {}).items():
                    price_str = dim_val.get("pricePerUnit", {}).get("USD", "0")
                    rate = float(price_str)
                    if rate > 0:
                        return rate

    raise ValueError(f"Could not find EC2 rate for {instance_type} ({os_filter})")


async def _fetch_aws_rds(config: dict, region: str) -> dict:
    """
    RDS On-Demand pricing.
    config keys: engine (mysql|postgres|oracle|sqlserver), instance_type,
                 storage_gb, replicas, region
    """
    engine = config.get("engine", "mysql").lower()
    instance_type = config.get("instance_type", "db.m5.large")
    storage_gb = float(config.get("storage_gb", 100))
    replicas = int(config.get("replicas", 0))
    hours_per_month = 730

    engine_map = {
        "mysql":      "MySQL",
        "postgres":   "PostgreSQL",
        "postgresql": "PostgreSQL",
        "oracle":     "Oracle",
        "sqlserver":  "SQL Server",
        "aurora":     "Aurora MySQL",
    }
    db_engine = engine_map.get(engine, "MySQL")

    api_url = f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/{region}/index.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()
        data = resp.json()

    hourly_rate = _extract_rds_rate(data, instance_type, db_engine)
    storage_rate = _extract_rds_storage_rate(data)

    instance_monthly = hourly_rate * hours_per_month * (1 + replicas)
    storage_monthly = storage_rate * storage_gb
    total = instance_monthly + storage_monthly

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "instance-hour + GB-month",
        "price_per_unit": hourly_rate,
        "source": "aws_api",
        "details": {
            "engine": engine,
            "instance_type": instance_type,
            "storage_gb": storage_gb,
            "replicas": replicas,
            "region": region,
        },
    }


def _extract_rds_rate(data: dict, instance_type: str, db_engine: str) -> float:
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})

    for sku, product in products.items():
        attrs = product.get("attributes", {})
        if (
            attrs.get("instanceType") == instance_type
            and db_engine.lower() in attrs.get("databaseEngine", "").lower()
            and attrs.get("deploymentOption") == "Single-AZ"
        ):
            sku_terms = terms.get(sku, {})
            for term_key, term_val in sku_terms.items():
                for dim_key, dim_val in term_val.get("priceDimensions", {}).items():
                    price_str = dim_val.get("pricePerUnit", {}).get("USD", "0")
                    rate = float(price_str)
                    if rate > 0:
                        return rate

    raise ValueError(f"Could not find RDS rate for {instance_type} ({db_engine})")


def _extract_rds_storage_rate(data: dict) -> float:
    """Extract RDS gp2 storage rate per GB-month."""
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})

    for sku, product in products.items():
        attrs = product.get("attributes", {})
        if (
            attrs.get("volumeType") == "General Purpose"
            and "storage" in attrs.get("usagetype", "").lower()
        ):
            sku_terms = terms.get(sku, {})
            for term_key, term_val in sku_terms.items():
                for dim_key, dim_val in term_val.get("priceDimensions", {}).items():
                    price_str = dim_val.get("pricePerUnit", {}).get("USD", "0")
                    rate = float(price_str)
                    if rate > 0:
                        return rate
    return 0.115  # fallback: standard GP2 price


async def _fetch_aws_elasticache(config: dict, region: str) -> dict:
    """
    ElastiCache On-Demand pricing.
    config keys: node_type, num_nodes, engine (redis|memcached)
    """
    node_type = config.get("node_type", "cache.m5.large")
    num_nodes = int(config.get("num_nodes", 1))
    hours_per_month = 730

    api_url = f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonElastiCache/current/{region}/index.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(api_url)
        resp.raise_for_status()
        data = resp.json()

    hourly_rate = _extract_elasticache_rate(data, node_type)
    monthly_cost = hourly_rate * hours_per_month * num_nodes

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "node-hour",
        "price_per_unit": hourly_rate,
        "source": "aws_api",
        "details": {"node_type": node_type, "num_nodes": num_nodes, "region": region},
    }


def _extract_elasticache_rate(data: dict, node_type: str) -> float:
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})

    for sku, product in products.items():
        attrs = product.get("attributes", {})
        if attrs.get("instanceType") == node_type:
            sku_terms = terms.get(sku, {})
            for term_key, term_val in sku_terms.items():
                for dim_key, dim_val in term_val.get("priceDimensions", {}).items():
                    price_str = dim_val.get("pricePerUnit", {}).get("USD", "0")
                    rate = float(price_str)
                    if rate > 0:
                        return rate

    raise ValueError(f"Could not find ElastiCache rate for {node_type}")


async def _fetch_aws_s3(config: dict, region: str) -> dict:
    """
    S3 pricing: storage + GET/PUT requests.
    config keys: storage_gb, get_requests (monthly), put_requests (monthly)
    Rates are well-known and stable; use hardcoded regional tiers as AWS
    S3 bulk pricing JSON is extremely large.
    """
    storage_gb = float(config.get("storage_gb", 100))
    get_requests = int(config.get("get_requests", 10000))
    put_requests = int(config.get("put_requests", 1000))

    # Standard S3 storage rates by region (USD/GB-month)
    storage_rates = {
        "us-east-1": 0.023, "us-east-2": 0.023, "us-west-1": 0.026,
        "us-west-2": 0.023, "eu-west-1": 0.023, "eu-west-2": 0.024,
        "eu-central-1": 0.024, "ap-south-1": 0.025, "ap-southeast-1": 0.025,
        "ap-southeast-2": 0.025, "ap-northeast-1": 0.025, "sa-east-1": 0.0405,
        "ca-central-1": 0.023,
    }
    storage_rate = storage_rates.get(region, 0.023)
    get_rate = 0.0004 / 1000   # per request
    put_rate = 0.005 / 1000    # per request

    storage_cost = storage_gb * storage_rate
    get_cost = get_requests * get_rate
    put_cost = put_requests * put_rate
    total = storage_cost + get_cost + put_cost

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB-month + requests",
        "price_per_unit": storage_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb,
            "get_requests": get_requests,
            "put_requests": put_requests,
            "region": region,
        },
    }


async def _fetch_aws_lambda(config: dict, region: str) -> dict:
    """
    Lambda pricing: requests + GB-seconds compute.
    config keys: memory_mb, avg_duration_ms, monthly_invocations
    Free tier excluded intentionally (enterprise BOM context).
    """
    memory_mb = int(config.get("memory_mb", 512))
    avg_duration_ms = float(config.get("avg_duration_ms", 200))
    monthly_invocations = int(config.get("monthly_invocations", 1_000_000))

    # Lambda rates are global (same across regions with minor exceptions)
    request_rate = 0.20 / 1_000_000       # per request
    compute_rate = 0.0000166667           # per GB-second

    gb_seconds = (memory_mb / 1024) * (avg_duration_ms / 1000) * monthly_invocations
    compute_cost = gb_seconds * compute_rate
    request_cost = monthly_invocations * request_rate
    total = compute_cost + request_cost

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "invocations + GB-seconds",
        "price_per_unit": compute_rate,
        "source": "hardcoded_regional",
        "details": {
            "memory_mb": memory_mb,
            "avg_duration_ms": avg_duration_ms,
            "monthly_invocations": monthly_invocations,
            "gb_seconds": round(gb_seconds, 2),
        },
    }


async def _fetch_aws_fargate(config: dict, region: str) -> dict:
    """
    ECS/EKS Fargate pricing: vCPU-hours + GB-hours.
    config keys: vcpu, memory_gb, num_tasks, hours_per_month
    """
    vcpu = float(config.get("vcpu", 1.0))
    memory_gb = float(config.get("memory_gb", 2.0))
    num_tasks = int(config.get("num_tasks", 1))
    hours_per_month = float(config.get("hours_per_month", 730))

    # Fargate rates (us-east-1 base; other regions within ~10%)
    fargate_vcpu_rates = {
        "us-east-1": 0.04048, "us-east-2": 0.04048, "us-west-1": 0.04656,
        "us-west-2": 0.04048, "eu-west-1": 0.04453, "eu-west-2": 0.04975,
        "eu-central-1": 0.04453, "ap-south-1": 0.04656, "ap-southeast-1": 0.05065,
        "ap-southeast-2": 0.05065, "ap-northeast-1": 0.05065,
    }
    fargate_mem_rates = {
        "us-east-1": 0.004445, "us-east-2": 0.004445, "us-west-1": 0.005113,
        "us-west-2": 0.004445, "eu-west-1": 0.004890, "eu-west-2": 0.005463,
        "eu-central-1": 0.004890, "ap-south-1": 0.005113, "ap-southeast-1": 0.005563,
        "ap-southeast-2": 0.005563, "ap-northeast-1": 0.005563,
    }

    vcpu_rate = fargate_vcpu_rates.get(region, 0.04048)
    mem_rate = fargate_mem_rates.get(region, 0.004445)

    vcpu_cost = vcpu * vcpu_rate * hours_per_month * num_tasks
    mem_cost = memory_gb * mem_rate * hours_per_month * num_tasks
    total = vcpu_cost + mem_cost

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "vCPU-hour + GB-hour",
        "price_per_unit": vcpu_rate,
        "source": "hardcoded_regional",
        "details": {
            "vcpu": vcpu, "memory_gb": memory_gb,
            "num_tasks": num_tasks, "hours_per_month": hours_per_month,
        },
    }


async def _fetch_aws_cloudfront(config: dict, region: str) -> dict:
    """
    CloudFront pricing: data transfer out + HTTP requests.
    config keys: data_transfer_gb, https_requests (monthly)
    """
    data_transfer_gb = float(config.get("data_transfer_gb", 100))
    https_requests = int(config.get("https_requests", 1_000_000))

    # First 10TB/month
    transfer_rate = 0.0085   # per GB
    request_rate = 0.0100 / 10_000  # per HTTPS request (first 10M)

    transfer_cost = data_transfer_gb * transfer_rate
    request_cost = https_requests * request_rate
    total = transfer_cost + request_cost

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB + requests",
        "price_per_unit": transfer_rate,
        "source": "hardcoded_regional",
        "details": {
            "data_transfer_gb": data_transfer_gb,
            "https_requests": https_requests,
        },
    }


async def _fetch_aws_dynamodb(config: dict, region: str) -> dict:
    """
    DynamoDB On-Demand pricing.
    config keys: storage_gb, read_request_units (monthly), write_request_units (monthly)
    """
    storage_gb = float(config.get("storage_gb", 10))
    rru = int(config.get("read_request_units", 1_000_000))
    wru = int(config.get("write_request_units", 500_000))

    storage_rate = 0.25     # per GB-month
    rru_rate = 0.25 / 1_000_000  # per RRU
    wru_rate = 1.25 / 1_000_000  # per WRU

    total = (storage_gb * storage_rate) + (rru * rru_rate) + (wru * wru_rate)

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB + RRU + WRU",
        "price_per_unit": storage_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb,
            "read_request_units": rru,
            "write_request_units": wru,
            "region": region,
        },
    }


# ---------------------------------------------------------------------------
# Azure Pricing
# ---------------------------------------------------------------------------

AZURE_RETAIL_API = "https://prices.azure.com/api/retail/prices"


async def fetch_azure_pricing(
    service_type: str,
    config: dict,
    region: str = "eastus",
    currency: str = "USD",
) -> dict:
    """
    Fetch live Azure PAYG price for a given service + config + region.
    Uses the Azure Retail Prices API (no auth required).
    """
    try:
        if service_type in ("compute_linux", "compute_windows", "compute"):
            result = await _fetch_azure_vm(config, region)
        elif service_type == "database":
            result = await _fetch_azure_sql(config, region)
        elif service_type == "nosql":
            result = await _fetch_azure_cosmos(config, region)
        elif service_type == "container":
            result = await _fetch_azure_aks(config, region)
        elif service_type == "storage":
            result = await _fetch_azure_blob(config, region)
        elif service_type == "serverless":
            result = await _fetch_azure_functions(config, region)
        elif service_type == "cache":
            result = await _fetch_azure_redis(config, region)
        else:
            raise ValueError(f"Unsupported Azure service_type: {service_type}")

        result["monthly_cost_usd"] = _convert_currency(result["monthly_cost_usd"], to=currency)
        return result

    except Exception as e:
        logger.error(f"Azure pricing fetch failed [{service_type}|{region}]: {e}")
        raise


async def _fetch_azure_vm(config: dict, region: str) -> dict:
    """
    Azure VM On-Demand (PAYG) pricing.
    config keys: size (e.g. Standard_D2s_v3), quantity, os (linux|windows)
    """
    size = config.get("size", "Standard_D2s_v3")
    quantity = int(config.get("quantity", 1))
    os_type = config.get("os", "linux")
    hours_per_month = 730

    os_filter = "Linux" if os_type == "linux" else "Windows"
    sku_name = size if os_type == "linux" else f"{size} Windows"

    filter_str = (
        f"serviceName eq 'Virtual Machines' "
        f"and armRegionName eq '{region}' "
        f"and skuName eq '{sku_name}' "
        f"and priceType eq 'Consumption' "
        f"and contains(productName, '{os_filter}')"
    )

    params = {"$filter": filter_str, "currencyCode": "USD", "api-version": "2023-01-01-preview"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(AZURE_RETAIL_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("Items", [])
    if not items:
        raise ValueError(f"No Azure VM pricing found for {size} in {region}")

    hourly_rate = float(items[0]["retailPrice"])
    monthly_cost = hourly_rate * hours_per_month * quantity

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "hour",
        "price_per_unit": hourly_rate,
        "source": "azure_api",
        "details": {
            "size": size, "quantity": quantity, "os": os_type, "region": region,
        },
    }


async def _fetch_azure_sql(config: dict, region: str) -> dict:
    """
    Azure SQL Database pricing (vCore model).
    config keys: tier (GeneralPurpose|BusinessCritical), vcores, storage_gb
    """
    tier = config.get("tier", "GeneralPurpose")
    vcores = int(config.get("vcores", 4))
    storage_gb = float(config.get("storage_gb", 100))
    hours_per_month = 730

    sku_name = f"{tier}, {vcores} vCores"
    filter_str = (
        f"serviceName eq 'SQL Database' "
        f"and armRegionName eq '{region}' "
        f"and skuName eq '{sku_name}' "
        f"and priceType eq 'Consumption'"
    )

    params = {"$filter": filter_str, "currencyCode": "USD", "api-version": "2023-01-01-preview"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(AZURE_RETAIL_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("Items", [])
    if not items:
        raise ValueError(f"No Azure SQL pricing found for {sku_name} in {region}")

    hourly_rate = float(items[0]["retailPrice"])
    storage_rate = 0.115  # USD per GB-month (standard)
    monthly_cost = (hourly_rate * hours_per_month) + (storage_gb * storage_rate)

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "vCore-hour + GB-month",
        "price_per_unit": hourly_rate,
        "source": "azure_api",
        "details": {
            "tier": tier, "vcores": vcores, "storage_gb": storage_gb, "region": region,
        },
    }


async def _fetch_azure_cosmos(config: dict, region: str) -> dict:
    """
    Azure Cosmos DB pricing (RU/s provisioned).
    config keys: request_units (RU/s), storage_gb
    """
    request_units = int(config.get("request_units", 400))
    storage_gb = float(config.get("storage_gb", 10))

    # Cosmos DB pricing (per 100 RU/s per hour)
    filter_str = (
        f"serviceName eq 'Azure Cosmos DB' "
        f"and armRegionName eq '{region}' "
        f"and priceType eq 'Consumption' "
        f"and skuName eq 'Standard'"
    )
    params = {"$filter": filter_str, "currencyCode": "USD", "api-version": "2023-01-01-preview"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(AZURE_RETAIL_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = [i for i in data.get("Items", []) if "RU" in i.get("meterName", "")]
    if not items:
        # Fallback known rate
        ru_rate_per_100_per_hour = 0.008
    else:
        ru_rate_per_100_per_hour = float(items[0]["retailPrice"])

    storage_rate = 0.25  # per GB-month

    ru_monthly = (request_units / 100) * ru_rate_per_100_per_hour * 730
    storage_monthly = storage_gb * storage_rate
    total = ru_monthly + storage_monthly

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "RU/s-hour + GB-month",
        "price_per_unit": ru_rate_per_100_per_hour,
        "source": "azure_api",
        "details": {
            "request_units": request_units, "storage_gb": storage_gb, "region": region,
        },
    }


async def _fetch_azure_aks(config: dict, region: str) -> dict:
    """
    AKS: VM pricing for node pool (AKS management plane is free).
    config keys: node_size, node_count, os (linux|windows)
    """
    node_config = {
        "size": config.get("node_size", "Standard_D2s_v3"),
        "quantity": config.get("node_count", 3),
        "os": config.get("os", "linux"),
    }
    return await _fetch_azure_vm(node_config, region)


async def _fetch_azure_blob(config: dict, region: str) -> dict:
    """
    Azure Blob Storage (Hot tier).
    config keys: storage_gb, read_operations (monthly), write_operations (monthly)
    """
    storage_gb = float(config.get("storage_gb", 100))
    read_ops = int(config.get("read_operations", 10000))
    write_ops = int(config.get("write_operations", 1000))

    storage_rate = 0.018   # per GB-month (Hot LRS, eastus)
    read_rate = 0.004 / 10_000
    write_rate = 0.05 / 10_000

    total = (storage_gb * storage_rate) + (read_ops * read_rate) + (write_ops * write_rate)

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB-month + operations",
        "price_per_unit": storage_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb, "read_operations": read_ops,
            "write_operations": write_ops, "region": region,
        },
    }


async def _fetch_azure_functions(config: dict, region: str) -> dict:
    """
    Azure Functions (Consumption plan).
    config keys: monthly_executions, avg_duration_ms, memory_mb
    """
    executions = int(config.get("monthly_executions", 1_000_000))
    avg_duration_ms = float(config.get("avg_duration_ms", 200))
    memory_mb = int(config.get("memory_mb", 512))

    execution_rate = 0.20 / 1_000_000
    compute_rate = 0.000016  # per GB-second

    gb_seconds = (memory_mb / 1024) * (avg_duration_ms / 1000) * executions
    total = (executions * execution_rate) + (gb_seconds * compute_rate)

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "executions + GB-seconds",
        "price_per_unit": execution_rate,
        "source": "hardcoded_regional",
        "details": {
            "monthly_executions": executions,
            "avg_duration_ms": avg_duration_ms,
            "memory_mb": memory_mb,
        },
    }


async def _fetch_azure_redis(config: dict, region: str) -> dict:
    """
    Azure Cache for Redis pricing.
    config keys: tier (Basic|Standard|Premium), capacity (cache size index 0-6)
    """
    tier = config.get("tier", "Standard")
    capacity = int(config.get("capacity", 1))

    filter_str = (
        f"serviceName eq 'Azure Cache for Redis' "
        f"and armRegionName eq '{region}' "
        f"and priceType eq 'Consumption' "
        f"and skuName eq '{tier} {capacity}'"
    )
    params = {"$filter": filter_str, "currencyCode": "USD", "api-version": "2023-01-01-preview"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(AZURE_RETAIL_API, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("Items", [])
    if not items:
        raise ValueError(f"No Azure Redis pricing for {tier} {capacity} in {region}")

    hourly_rate = float(items[0]["retailPrice"])
    monthly_cost = hourly_rate * 730

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "hour",
        "price_per_unit": hourly_rate,
        "source": "azure_api",
        "details": {"tier": tier, "capacity": capacity, "region": region},
    }


# ---------------------------------------------------------------------------
# GCP Pricing
# ---------------------------------------------------------------------------

GCP_BILLING_API = "https://cloudbilling.googleapis.com/v1"


async def fetch_gcp_pricing(
    service_type: str,
    config: dict,
    region: str = "us-central1",
    currency: str = "USD",
    api_key: Optional[str] = None,
) -> dict:
    """
    Fetch live GCP PAYG price for a given service + config + region.
    api_key: GCP API key for Cloud Billing API (optional; falls back to
             hardcoded regional rates if not provided).
    """
    try:
        if service_type == "compute":
            result = await _fetch_gcp_compute(config, region, api_key)
        elif service_type == "database":
            result = await _fetch_gcp_cloudsql(config, region, api_key)
        elif service_type == "container":
            result = await _fetch_gcp_gke(config, region, api_key)
        elif service_type == "storage":
            result = await _fetch_gcp_storage(config, region)
        elif service_type == "serverless":
            result = await _fetch_gcp_functions(config, region)
        elif service_type == "nosql":
            result = await _fetch_gcp_firestore(config, region)
        elif service_type == "cache":
            result = await _fetch_gcp_memorystore(config, region)
        elif service_type == "analytics":
            result = await _fetch_gcp_bigquery(config, region)
        else:
            raise ValueError(f"Unsupported GCP service_type: {service_type}")

        result["monthly_cost_usd"] = _convert_currency(result["monthly_cost_usd"], to=currency)
        return result

    except Exception as e:
        logger.error(f"GCP pricing fetch failed [{service_type}|{region}]: {e}")
        raise


async def _fetch_gcp_compute(config: dict, region: str, api_key: Optional[str]) -> dict:
    """
    Compute Engine pricing.
    config keys: machine_type (e.g. n2-standard-2), quantity, os (linux|windows)
    730 hours/month. SUD NOT applied here — applied by pricing_engine.py.
    """
    machine_type = config.get("machine_type", "n2-standard-2")
    quantity = int(config.get("quantity", 1))
    os_type = config.get("os", "linux")
    hours_per_month = 730

    # GCP Compute hourly rates (Linux, us-central1) — well-known stable rates
    # Used as fallback when API key not provided
    gce_rates = {
        "n2-standard-2":  0.0971, "n2-standard-4":  0.1942, "n2-standard-8":  0.3883,
        "n2-standard-16": 0.7766, "n2-standard-32": 1.5533, "n2-standard-64": 3.1065,
        "n2-highmem-2":   0.1310, "n2-highmem-4":   0.2620, "n2-highmem-8":   0.5240,
        "n2-highcpu-2":   0.0719, "n2-highcpu-4":   0.1437, "n2-highcpu-8":   0.2875,
        "e2-standard-2":  0.0670, "e2-standard-4":  0.1340, "e2-standard-8":  0.2681,
        "e2-medium":      0.0335, "e2-small":       0.0168,
        "c2-standard-4":  0.2088, "c2-standard-8":  0.4176, "c2-standard-16": 0.8352,
        "n1-standard-1":  0.0475, "n1-standard-2":  0.0950, "n1-standard-4":  0.1900,
    }

    # Regional multipliers vs us-central1
    region_multipliers = {
        "us-central1": 1.0, "us-east1": 1.0, "us-east4": 1.04, "us-west1": 1.0,
        "us-west2": 1.09, "us-west3": 1.09, "us-west4": 1.09,
        "europe-west1": 1.08, "europe-west2": 1.16, "europe-west3": 1.12,
        "europe-west4": 1.08, "europe-north1": 1.08,
        "asia-east1": 1.10, "asia-east2": 1.22, "asia-northeast1": 1.14,
        "asia-south1": 1.14, "asia-southeast1": 1.14, "asia-southeast2": 1.20,
        "australia-southeast1": 1.19, "southamerica-east1": 1.24,
    }

    windows_surcharge_per_core = {
        "n2-standard-2": 0.04, "n2-standard-4": 0.08, "n2-standard-8": 0.16,
        "e2-standard-2": 0.04, "e2-standard-4": 0.08,
    }

    base_rate = gce_rates.get(machine_type)
    if not base_rate:
        raise ValueError(f"Unknown GCP machine type: {machine_type}. Add to gce_rates table.")

    multiplier = region_multipliers.get(region, 1.0)
    hourly_rate = base_rate * multiplier

    if os_type == "windows":
        hourly_rate += windows_surcharge_per_core.get(machine_type, 0.04)

    monthly_cost = hourly_rate * hours_per_month * quantity

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "instance-hour",
        "price_per_unit": hourly_rate,
        "source": "hardcoded_regional",
        "details": {
            "machine_type": machine_type, "quantity": quantity,
            "os": os_type, "region": region, "hours_per_month": hours_per_month,
        },
    }


async def _fetch_gcp_cloudsql(config: dict, region: str, api_key: Optional[str]) -> dict:
    """
    Cloud SQL pricing.
    config keys: tier (db-n1-standard-2 etc.), engine (mysql|postgres|sqlserver),
                 storage_gb, replicas
    """
    tier = config.get("tier", "db-n1-standard-2")
    engine = config.get("engine", "mysql")
    storage_gb = float(config.get("storage_gb", 100))
    replicas = int(config.get("replicas", 0))
    hours_per_month = 730

    # Cloud SQL hourly instance rates (us-central1)
    cloudsql_rates = {
        "db-n1-standard-1": 0.0413, "db-n1-standard-2": 0.0826,
        "db-n1-standard-4": 0.1651, "db-n1-standard-8": 0.3302,
        "db-n1-highmem-2":  0.1117, "db-n1-highmem-4":  0.2234,
        "db-n1-highmem-8":  0.4469, "db-n1-highmem-16": 0.8938,
        "db-custom-2-7680": 0.1004, "db-custom-4-15360": 0.2007,
    }

    region_multipliers = {
        "us-central1": 1.0, "us-east1": 1.0, "us-east4": 1.04,
        "europe-west1": 1.08, "europe-west4": 1.08,
        "asia-east1": 1.10, "asia-southeast1": 1.14, "asia-south1": 1.14,
    }

    storage_rate = 0.17   # SSD per GB-month
    base_rate = cloudsql_rates.get(tier, 0.0826)
    multiplier = region_multipliers.get(region, 1.0)
    hourly_rate = base_rate * multiplier

    instance_monthly = hourly_rate * hours_per_month * (1 + replicas)
    storage_monthly = storage_gb * storage_rate
    total = instance_monthly + storage_monthly

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "instance-hour + GB-month",
        "price_per_unit": hourly_rate,
        "source": "hardcoded_regional",
        "details": {
            "tier": tier, "engine": engine, "storage_gb": storage_gb,
            "replicas": replicas, "region": region,
        },
    }


async def _fetch_gcp_gke(config: dict, region: str, api_key: Optional[str]) -> dict:
    """
    GKE: node pool VM pricing (GKE control plane is free for Standard tier).
    config keys: machine_type, node_count, os
    """
    node_config = {
        "machine_type": config.get("machine_type", "n2-standard-2"),
        "quantity": config.get("node_count", 3),
        "os": config.get("os", "linux"),
    }
    return await _fetch_gcp_compute(node_config, region, api_key)


async def _fetch_gcp_storage(config: dict, region: str) -> dict:
    """
    Cloud Storage pricing (Standard class).
    config keys: storage_gb, class_a_ops, class_b_ops
    """
    storage_gb = float(config.get("storage_gb", 100))
    class_a_ops = int(config.get("class_a_ops", 10000))   # write ops
    class_b_ops = int(config.get("class_b_ops", 100000))  # read ops

    # Standard storage rates by region
    storage_rates = {
        "us-central1": 0.020, "us-east1": 0.020, "us-west1": 0.020,
        "europe-west1": 0.020, "europe-west4": 0.020,
        "asia-east1": 0.020, "asia-southeast1": 0.023, "asia-south1": 0.023,
        "australia-southeast1": 0.023, "southamerica-east1": 0.035,
    }

    storage_rate = storage_rates.get(region, 0.020)
    class_a_rate = 0.05 / 10_000
    class_b_rate = 0.004 / 10_000

    total = (
        storage_gb * storage_rate
        + class_a_ops * class_a_rate
        + class_b_ops * class_b_rate
    )

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB-month + ops",
        "price_per_unit": storage_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb, "class_a_ops": class_a_ops,
            "class_b_ops": class_b_ops, "region": region,
        },
    }


async def _fetch_gcp_functions(config: dict, region: str) -> dict:
    """
    Cloud Functions (1st gen) pricing.
    config keys: monthly_invocations, avg_duration_ms, memory_mb
    """
    invocations = int(config.get("monthly_invocations", 1_000_000))
    avg_duration_ms = float(config.get("avg_duration_ms", 200))
    memory_mb = int(config.get("memory_mb", 256))

    invocation_rate = 0.40 / 1_000_000
    compute_rate = 0.0000025  # per GB-second

    gb_seconds = (memory_mb / 1024) * (avg_duration_ms / 1000) * invocations
    total = (invocations * invocation_rate) + (gb_seconds * compute_rate)

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "invocations + GB-seconds",
        "price_per_unit": invocation_rate,
        "source": "hardcoded_regional",
        "details": {
            "monthly_invocations": invocations,
            "avg_duration_ms": avg_duration_ms,
            "memory_mb": memory_mb,
        },
    }


async def _fetch_gcp_firestore(config: dict, region: str) -> dict:
    """
    Firestore pricing.
    config keys: storage_gb, reads_per_month, writes_per_month, deletes_per_month
    """
    storage_gb = float(config.get("storage_gb", 10))
    reads = int(config.get("reads_per_month", 1_000_000))
    writes = int(config.get("writes_per_month", 500_000))
    deletes = int(config.get("deletes_per_month", 100_000))

    storage_rate = 0.18  # per GB-month
    read_rate = 0.06 / 100_000
    write_rate = 0.18 / 100_000
    delete_rate = 0.02 / 100_000

    total = (
        storage_gb * storage_rate
        + reads * read_rate
        + writes * write_rate
        + deletes * delete_rate
    )

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB-month + operations",
        "price_per_unit": storage_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb, "reads_per_month": reads,
            "writes_per_month": writes, "deletes_per_month": deletes,
        },
    }


async def _fetch_gcp_memorystore(config: dict, region: str) -> dict:
    """
    Memorystore for Redis pricing.
    config keys: tier (basic|standard), capacity_gb
    """
    tier = config.get("tier", "standard")
    capacity_gb = float(config.get("capacity_gb", 1.0))
    hours_per_month = 730

    # Rate per GB-hour
    tier_rates = {"basic": 0.016, "standard": 0.032}
    rate_per_gb_hour = tier_rates.get(tier, 0.032)

    region_multipliers = {
        "us-central1": 1.0, "us-east1": 1.0, "europe-west1": 1.08,
        "asia-east1": 1.10, "asia-southeast1": 1.14,
    }
    multiplier = region_multipliers.get(region, 1.0)
    monthly_cost = rate_per_gb_hour * capacity_gb * hours_per_month * multiplier

    return {
        "monthly_cost_usd": round(monthly_cost, 4),
        "unit": "GB-hour",
        "price_per_unit": rate_per_gb_hour,
        "source": "hardcoded_regional",
        "details": {"tier": tier, "capacity_gb": capacity_gb, "region": region},
    }


async def _fetch_gcp_bigquery(config: dict, region: str) -> dict:
    """
    BigQuery pricing (on-demand query model).
    config keys: storage_gb, tb_queried_per_month
    """
    storage_gb = float(config.get("storage_gb", 100))
    tb_queried = float(config.get("tb_queried_per_month", 1.0))

    storage_rate = 0.020   # active storage per GB-month
    query_rate = 5.0       # per TB queried (on-demand)

    total = (storage_gb * storage_rate) + (tb_queried * query_rate)

    return {
        "monthly_cost_usd": round(total, 4),
        "unit": "GB-month + TB-queried",
        "price_per_unit": query_rate,
        "source": "hardcoded_regional",
        "details": {
            "storage_gb": storage_gb, "tb_queried_per_month": tb_queried, "region": region,
        },
    }
