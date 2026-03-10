/**
 * Scenarios.js
 *
 * Features:
 *  - BOM selector dropdown
 *  - "Generate Scenarios" button with loading state
 *  - Pricing model comparison cards (one per applicable model)
 *  - Per-service itemized breakdown table
 *    → Each row shows which models apply (greyed out if N/A)
 *  - Bar chart: monthly cost across all applicable models
 *  - Recommended model badge
 *  - AHB badge when enabled
 *  - Savings badges vs PAYG
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  listBOMs,
  getBOM,
  generateScenarios,
  getScenarios,
  ApiError,
  PRICING_MODEL_META,
} from "../services/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatUSD(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: 2,
  }).format(value);
}

function fmt(value) {
  return typeof value === "number" ? formatUSD(value) : "—";
}

function pct(value) {
  if (!value) return null;
  return `${value.toFixed(1)}%`;
}

function modelMeta(modelVal) {
  return PRICING_MODEL_META[modelVal] || {
    label: modelVal,
    color: "#6b7280",
    badge: "bg-gray-100 text-gray-600",
    order: 99,
  };
}

function sortedModels(models) {
  return [...models].sort(
    (a, b) => (modelMeta(a.model).order || 99) - (modelMeta(b.model).order || 99)
  );
}

// ---------------------------------------------------------------------------
// Sub: Loading spinner
// ---------------------------------------------------------------------------

function Spinner({ label }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent
        rounded-full animate-spin" />
      <p className="text-sm text-gray-500">{label || "Loading…"}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub: Empty state
// ---------------------------------------------------------------------------

function EmptyState({ icon, title, subtitle, action }) {
  return (
    <div className="text-center py-16 px-8 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
      <div className="text-5xl mb-3">{icon}</div>
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-5">{subtitle}</p>
      {action}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub: BOM selector
// ---------------------------------------------------------------------------

function BOMSelector({ boms, selectedId, onChange }) {
  if (!boms.length) return null;
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700 shrink-0">Select BOM:</label>
      <select
        value={selectedId || ""}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-sm
          focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
      >
        <option value="" disabled>— Choose a BOM —</option>
        {boms.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name} ({b.cloud_provider.toUpperCase()}) — {b.service_count} service
            {b.service_count !== 1 ? "s" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub: Pricing model card
// ---------------------------------------------------------------------------

function PricingModelCard({ model, isRecommended, isPayg }) {
  const meta = modelMeta(model.model);

  return (
    <div
      className={`relative rounded-2xl border-2 p-5 transition-all
        ${isRecommended
          ? "border-green-400 bg-green-50 shadow-md"
          : isPayg
          ? "border-gray-200 bg-gray-50"
          : "border-gray-200 bg-white hover:shadow-sm"}`}
    >
      {isRecommended && (
        <div className="absolute -top-3 left-4 bg-green-500 text-white text-xs
          font-bold px-3 py-0.5 rounded-full shadow">
          ⭐ Recommended
        </div>
      )}

      {/* Model label */}
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${meta.badge}`}>
          {meta.label}
        </span>
        {!isPayg && model.savings_pct > 0 && (
          <span className="text-xs font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
            −{pct(model.savings_pct)} vs PAYG
          </span>
        )}
      </div>

      {/* Monthly cost */}
      <div className="text-2xl font-bold text-gray-900">
        {fmt(model.monthly_cost)}
        <span className="text-sm font-normal text-gray-500">/mo</span>
      </div>

      {/* Annual cost */}
      <div className="text-sm text-gray-500 mt-0.5">
        {fmt(model.annual_cost)}/yr
      </div>

      {/* Savings vs PAYG */}
      {!isPayg && model.savings_monthly > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500">Savings vs Pay-As-You-Go</div>
          <div className="font-semibold text-green-700 text-sm mt-0.5">
            {fmt(model.savings_monthly)}/mo · {fmt(model.savings_annual)}/yr
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub: Simple SVG bar chart
// Pure React, no external charting library needed
// ---------------------------------------------------------------------------

function CostBarChart({ models }) {
  const sorted = sortedModels(models);
  const maxCost = Math.max(...sorted.map((m) => m.monthly_cost), 1);
  const BAR_HEIGHT = 32;
  const LABEL_WIDTH = 160;
  const CHART_WIDTH = 320;
  const GAP = 10;
  const svgHeight = sorted.length * (BAR_HEIGHT + GAP) + 30;

  return (
    <div className="overflow-x-auto">
      <svg
        width={LABEL_WIDTH + CHART_WIDTH + 80}
        height={svgHeight}
        className="font-sans"
      >
        {sorted.map((m, i) => {
          const y        = i * (BAR_HEIGHT + GAP) + 15;
          const barWidth = Math.max((m.monthly_cost / maxCost) * CHART_WIDTH, 2);
          const meta     = modelMeta(m.model);
          const isPayg   = m.model === "payg";

          return (
            <g key={m.model}>
              {/* Label */}
              <text
                x={LABEL_WIDTH - 6}
                y={y + BAR_HEIGHT / 2 + 4}
                textAnchor="end"
                fontSize={11}
                fill="#4b5563"
                fontWeight={isPayg ? "600" : "400"}
              >
                {meta.label}
              </text>

              {/* Bar */}
              <rect
                x={LABEL_WIDTH}
                y={y}
                width={barWidth}
                height={BAR_HEIGHT}
                rx={6}
                fill={meta.color}
                opacity={isPayg ? 0.5 : 0.85}
              />

              {/* Value label */}
              <text
                x={LABEL_WIDTH + barWidth + 6}
                y={y + BAR_HEIGHT / 2 + 4}
                fontSize={11}
                fill="#374151"
                fontWeight="500"
              >
                {formatUSD(m.monthly_cost)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub: Itemized service breakdown table
// For each service row, shows cost under each applicable model.
// Models that don't apply to a service are shown in grey with "—".
// ---------------------------------------------------------------------------

function ItemizedTable({ services, allModels }) {
  const sortedModelList = sortedModels(allModels);

  return (
    <div className="overflow-x-auto rounded-2xl border border-gray-200">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-600 whitespace-nowrap">
              Service
            </th>
            <th className="text-left px-3 py-3 text-xs font-semibold text-gray-600">
              Type
            </th>
            {sortedModelList.map((m) => {
              const meta = modelMeta(m.model);
              return (
                <th key={m.model}
                  className="text-right px-3 py-3 text-xs font-semibold whitespace-nowrap"
                  style={{ color: meta.color }}>
                  {meta.label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {services.map((svc, idx) => {
            // Build a model→cost lookup for this service
            const modelCosts = {};
            (svc.scenarios || []).forEach((s) => {
              modelCosts[s.model] = s.monthly_cost;
            });
            const payg = modelCosts["payg"] || svc.payg_monthly_cost || 0;

            return (
              <tr key={idx}
                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors
                  ${idx % 2 === 0 ? "" : "bg-gray-50/30"}`}>
                {/* Service name */}
                <td className="px-4 py-3 font-medium text-gray-800 whitespace-nowrap">
                  {svc.service_name}
                </td>
                {/* Service type */}
                <td className="px-3 py-3 text-gray-500 text-xs whitespace-nowrap">
                  {svc.service_type}
                </td>
                {/* Cost per model */}
                {sortedModelList.map((m) => {
                  const cost = modelCosts[m.model];
                  const isPayg = m.model === "payg";
                  const applicable = cost !== undefined;

                  return (
                    <td key={m.model}
                      className={`px-3 py-3 text-right whitespace-nowrap
                        ${applicable ? "text-gray-800 font-medium" : "text-gray-300"}`}>
                      {applicable ? (
                        <div>
                          <div>{formatUSD(cost)}</div>
                          {!isPayg && applicable && cost < payg && (
                            <div className="text-xs text-green-600 font-normal">
                              −{pct(((payg - cost) / payg) * 100)}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs">N/A</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}

          {/* Totals row */}
          <tr className="bg-gray-100 border-t-2 border-gray-300 font-semibold">
            <td className="px-4 py-3 text-gray-800" colSpan={2}>
              Total (Monthly)
            </td>
            {sortedModelList.map((m) => (
              <td key={m.model} className="px-3 py-3 text-right text-gray-900">
                {formatUSD(m.monthly_cost)}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component: Scenarios
// ---------------------------------------------------------------------------

export default function Scenarios() {
  const [boms,          setBoms]          = useState([]);
  const [selectedBomId, setSelectedBomId] = useState(null);
  const [selectedBom,   setSelectedBom]   = useState(null);
  const [scenarioData,  setScenarioData]  = useState(null);
  const [loadingBoms,   setLoadingBoms]   = useState(true);
  const [generating,    setGenerating]    = useState(false);
  const [loadingExist,  setLoadingExist]  = useState(false);
  const [error,         setError]         = useState(null);

  // -------------------------------------------------------------------------
  // Load BOM list on mount
  // -------------------------------------------------------------------------
  useEffect(() => {
    (async () => {
      try {
        const list = await listBOMs();
        setBoms(list || []);
      } catch (e) {
        setError("Failed to load BOMs: " + (e.detail || e.message));
      } finally {
        setLoadingBoms(false);
      }
    })();
  }, []);

  // -------------------------------------------------------------------------
  // When BOM selection changes: load BOM detail + try to fetch existing scenarios
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedBomId) return;
    setScenarioData(null);
    setError(null);
    setLoadingExist(true);

    (async () => {
      try {
        const bom = await getBOM(selectedBomId);
        setSelectedBom(bom);
        try {
          const data = await getScenarios(selectedBomId);
          setScenarioData(data);
        } catch (e) {
          // 404 = no scenarios yet; anything else is a real error
          if (e instanceof ApiError && e.status === 404) {
            setScenarioData(null);  // show "Generate" CTA
          } else {
            throw e;
          }
        }
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : e.message);
      } finally {
        setLoadingExist(false);
      }
    })();
  }, [selectedBomId]);

  // -------------------------------------------------------------------------
  // Generate scenarios
  // -------------------------------------------------------------------------
  const handleGenerate = useCallback(async () => {
    if (!selectedBomId) return;
    setGenerating(true);
    setError(null);
    try {
      const data = await generateScenarios(selectedBomId);
      setScenarioData(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : e.message);
    } finally {
      setGenerating(false);
    }
  }, [selectedBomId]);

  // =========================================================================
  // Render
  // =========================================================================

  if (loadingBoms) return <Spinner label="Loading BOMs…" />;

  if (!boms.length) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <EmptyState
          icon="📋"
          title="No BOMs yet"
          subtitle="Create a Bill of Materials first, then come back here to generate cost scenarios."
        />
      </div>
    );
  }

  const models = sortedModels(scenarioData?.pricing_models || []);
  const payg   = models.find((m) => m.model === "payg");
  const recommended = scenarioData?.recommended_model;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cost Scenarios</h1>
        <p className="text-sm text-gray-500 mt-1">
          Compare pricing models across your cloud services.
        </p>
      </div>

      {/* BOM selector + Generate button */}
      <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
        <BOMSelector
          boms={boms}
          selectedId={selectedBomId}
          onChange={setSelectedBomId}
        />

        {selectedBom && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                {selectedBom.cloud_provider.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                {selectedBom.service_count} service
                {selectedBom.service_count !== 1 ? "s" : ""}
              </span>
              {selectedBom.azure_hybrid_benefit && (
                <span className="text-xs text-amber-700 bg-amber-100 px-3 py-1 rounded-full font-medium">
                  🏷️ Azure Hybrid Benefit ON
                </span>
              )}
              <span className="text-xs text-gray-400 bg-gray-50 px-3 py-1 rounded-full">
                USD
              </span>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || loadingExist}
              className="ml-4 bg-blue-600 text-white px-5 py-2 rounded-xl text-sm
                font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors
                flex items-center gap-2 shrink-0"
            >
              {generating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent
                    rounded-full animate-spin inline-block" />
                  Fetching live prices…
                </>
              ) : scenarioData ? (
                "🔄 Regenerate"
              ) : (
                "⚡ Generate Scenarios"
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      {/* Loading existing scenarios */}
      {loadingExist && <Spinner label="Loading scenarios…" />}

      {/* No scenarios yet — CTA */}
      {!loadingExist && selectedBomId && !scenarioData && !generating && !error && (
        <EmptyState
          icon="⚡"
          title="No scenarios yet"
          subtitle="Click 'Generate Scenarios' to fetch live prices and calculate costs across all applicable pricing models."
          action={
            <button
              onClick={handleGenerate}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-xl text-sm
                font-medium hover:bg-blue-700 transition-colors"
            >
              ⚡ Generate Scenarios
            </button>
          }
        />
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Results                                                              */}
      {/* ------------------------------------------------------------------ */}
      {scenarioData && !generating && (
        <>
          {/* Meta row */}
          <div className="flex items-center justify-between text-xs text-gray-500 px-1">
            <span>
              Generated: {scenarioData.generated_at
                ? new Date(scenarioData.generated_at).toLocaleString()
                : "just now"}
            </span>
            <span>{models.length} pricing model{models.length !== 1 ? "s" : ""} applicable</span>
          </div>

          {/* Pricing model cards */}
          <div>
            <h2 className="text-base font-semibold text-gray-800 mb-3">
              Pricing Model Comparison
            </h2>
            <div className={`grid gap-4
              ${models.length <= 2 ? "grid-cols-2"
              : models.length === 3 ? "grid-cols-3"
              : models.length === 4 ? "grid-cols-2 md:grid-cols-4"
              : "grid-cols-2 md:grid-cols-3 lg:grid-cols-4"}`}>
              {models.map((m) => (
                <PricingModelCard
                  key={m.model}
                  model={m}
                  isRecommended={m.model === recommended}
                  isPayg={m.model === "payg"}
                />
              ))}
            </div>
          </div>

          {/* Bar chart */}
          <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">
              Monthly Cost by Pricing Model
            </h2>
            <CostBarChart models={models} />
            <p className="text-xs text-gray-400 mt-3">
              * Savings Plan and Committed Use Discounts require upfront commitment.
              Actual savings may vary by region and instance type.
            </p>
          </div>

          {/* Itemized table */}
          {scenarioData.itemized_services?.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-gray-800 mb-3">
                Per-Service Breakdown
              </h2>
              <p className="text-xs text-gray-500 mb-3">
                "N/A" indicates a pricing model is not applicable for that service type.
                The BOM total uses PAYG cost for non-applicable services.
              </p>
              <ItemizedTable
                services={scenarioData.itemized_services}
                allModels={models}
              />
            </div>
          )}

          {/* AHB footnote */}
          {scenarioData.azure_hybrid_benefit && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-700">
              🏷️ <strong>Azure Hybrid Benefit</strong> is enabled for this BOM.
              Applicable services (Windows VMs, SQL Database) show an AHB pricing
              option reflecting your existing licence savings.
            </div>
          )}

          {/* GCP SUD footnote */}
          {scenarioData.cloud_provider === "gcp" && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-xs text-emerald-700">
              🔋 <strong>Sustained Use Discount (SUD)</strong> is calculated at the
              maximum 30% rate, assuming continuous 730-hour/month utilisation.
              SUD and Committed Use Discounts are mutually exclusive — you can only
              apply one per service.
            </div>
          )}
        </>
      )}
    </div>
  );
}
