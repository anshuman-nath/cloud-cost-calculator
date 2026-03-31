/**
 * BillOfMaterials.js
 *
 * 3-step wizard:
 *   Step 1 — Create BOM  (name + provider + AHB toggle for Azure)
 *   Step 2 — Add Services (provider-aware config forms)
 *   Step 3 — Review & Save (service list preview before generating scenarios)
 *
 * Props:
 *   onBOMCreated(bom)  — called after BOM is saved to backend
 */

import React, { useState, useCallback, useEffect } from "react";
import {
  createBOM,
  updateBOMServices,
  deleteBOM,
  listBOMs,
  SERVICE_TYPES,
  DEFAULT_SERVICE_CONFIGS,
  CONFIG_FIELD_LABELS,
  ApiError,
  getCatalogSKUs,
  getCatalogRegions,
  getCatalogOSOptions,
} from "../services/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PROVIDERS = [
  { value: "aws",   label: "Amazon Web Services", logo: "🟠" },
  { value: "azure", label: "Microsoft Azure",     logo: "🔵" },
  { value: "gcp",   label: "Google Cloud",        logo: "🔴" },
];

const STEPS = ["Create BOM", "Add Services", "Review & Save"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatUSD(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", minimumFractionDigits: 2,
  }).format(value);
}

function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

// ---------------------------------------------------------------------------
// Sub-component: Step indicator
// ---------------------------------------------------------------------------

function StepIndicator({ currentStep }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {STEPS.map((label, idx) => {
        const stepNum  = idx + 1;
        const isActive = stepNum === currentStep;
        const isDone   = stepNum < currentStep;
        return (
          <React.Fragment key={stepNum}>
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm
                  ${isDone   ? "bg-green-500 text-white"
                  : isActive ? "bg-blue-600 text-white"
                  :            "bg-gray-200 text-gray-500"}`}
              >
                {isDone ? "✓" : stepNum}
              </div>
              <span
                className={`mt-1 text-xs font-medium
                  ${isActive ? "text-blue-600" : isDone ? "text-green-600" : "text-gray-400"}`}
              >
                {label}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 mb-5
                ${isDone ? "bg-green-400" : "bg-gray-200"}`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Provider card selector
// ---------------------------------------------------------------------------

function ProviderSelector({ value, onChange }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {PROVIDERS.map((p) => (
        <button
          key={p.value}
          type="button"
          onClick={() => onChange(p.value)}
          className={`p-4 rounded-xl border-2 text-left transition-all
            ${value === p.value
              ? "border-blue-500 bg-blue-50 shadow-md"
              : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"}`}
        >
          <div className="text-3xl mb-1">{p.logo}</div>
          <div className="font-semibold text-sm text-gray-800">{p.label}</div>
          <div className="text-xs text-gray-500 mt-0.5">{p.value.toUpperCase()}</div>
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Azure Hybrid Benefit toggle
// ---------------------------------------------------------------------------

function AzureHybridBenefitToggle({ value, onChange }) {
  return (
    <div className="mt-5 p-4 bg-amber-50 border border-amber-200 rounded-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-semibold text-sm text-amber-900 flex items-center gap-1">
            🏷️ Azure Hybrid Benefit
          </div>
          <p className="text-xs text-amber-700 mt-1 leading-relaxed">
            Enable this if your organisation owns existing{" "}
            <strong>Windows Server</strong> or <strong>SQL Server</strong>{" "}
            licences with active Software Assurance. Applicable services will
            show an AHB pricing option with up to 40% additional savings.
          </p>
        </div>
        {/* Toggle switch */}
        <button
          type="button"
          role="switch"
          aria-checked={value}
          onClick={() => onChange(!value)}
          className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent
            transition-colors focus:outline-none
            ${value ? "bg-amber-500" : "bg-gray-300"}`}
        >
          <span
            className={`inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform
              ${value ? "translate-x-5" : "translate-x-0"}`}
          />
        </button>
      </div>
      {value && (
        <div className="mt-2 text-xs text-amber-800 bg-amber-100 rounded-lg px-3 py-2">
          ✅ AHB enabled — Windows VM and SQL Database services will include
          an Azure Hybrid Benefit pricing option.
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Service config form
// Renders the correct fields for a given provider + service_type
// ---------------------------------------------------------------------------

function ServiceConfigForm({ provider, serviceType, config, onChange, dynamicOptions = {} }) {
  if (!config) return null;

  const fields = Object.keys(config);

  return (
    <div className="grid grid-cols-2 gap-3 mt-3">
      {fields.map((field) => {
        const meta    = CONFIG_FIELD_LABELS[field] || { label: field, type: "text" };
        const value   = config[field];

        const options = dynamicOptions[field]?.length
          ? dynamicOptions[field]
          : meta.options || [];

        const isSelect = meta.type === "select" || options.length > 0;

        if (isSelect) {
          return (
            <div key={field}>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                {meta.label}
              </label>
              <select
                value={value}
                onChange={(e) => onChange(field, e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          );
        }

        return (
          <div key={field}>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              {meta.label}
            </label>
            <input
              type={meta.type === "number" ? "number" : "text"}
              value={value}
              min={meta.type === "number" ? 0 : undefined}
              onChange={(e) =>
                onChange(
                  field,
                  meta.type === "number"
                    ? parseFloat(e.target.value) || 0
                    : e.target.value
                )
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Add Service panel
// ---------------------------------------------------------------------------

function AddServicePanel({ provider, onAdd, onCancel }) {
  const serviceTypes = SERVICE_TYPES[provider] || [];

  const [selectedType,  setSelectedType]  = useState(serviceTypes[0]?.value || "");
  const [serviceName,   setServiceName]   = useState("");
  const [config,        setConfig]        = useState(
    deepClone(DEFAULT_SERVICE_CONFIGS[provider]?.[serviceTypes[0]?.value] || {})
  );

  // Dynamic catalog state
  const [skuOptions,    setSkuOptions]    = useState([]);
  const [regionOptions, setRegionOptions] = useState([]);
  const [osOptions,     setOsOptions]     = useState(["linux", "windows"]);

  // Fetch regions + OS once when provider changes
  useEffect(() => {
    getCatalogRegions(provider)
      .then((r) => setRegionOptions(r.regions))
      .catch(() => {});
    getCatalogOSOptions(provider)
      .then((r) => setOsOptions(r.os_options))
      .catch(() => {});
  }, [provider]);

  // Fetch SKUs when provider or service type changes
  useEffect(() => {
    if (selectedType) {
      getCatalogSKUs(provider, selectedType)
        .then((r) => setSkuOptions(r.skus))
        .catch(() => setSkuOptions([]));
    }
  }, [provider, selectedType]);

  // Build dynamic options override map
  const dynamicOptions = {
    instance_type: skuOptions,
    size:          skuOptions,
    machine_type:  skuOptions,
    node_type:     skuOptions,
    node_size:     skuOptions,
    region:        regionOptions,
    os:            osOptions,
  };

  const handleTypeChange = (type) => {
    setSelectedType(type);
    setConfig(deepClone(DEFAULT_SERVICE_CONFIGS[provider]?.[type] || {}));
    setServiceName("");
  };

  const handleConfigChange = (field, value) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const handleAdd = () => {
    if (!serviceName.trim()) {
      alert("Please enter a service name.");
      return;
    }
    onAdd({
      service_name: serviceName.trim(),
      service_type: selectedType,
      config,
    });
  };

  const selectedMeta = serviceTypes.find((s) => s.value === selectedType);

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">➕ Add a Service</h3>

      {/* Service type grid */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        {serviceTypes.map((st) => (
          <button
            key={st.value}
            type="button"
            onClick={() => handleTypeChange(st.value)}
            className={`flex flex-col items-center p-2 rounded-xl border text-center transition-all
              ${selectedType === st.value
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-200 hover:border-blue-300 bg-white text-gray-600"}`}
          >
            <span className="text-xl">{st.icon}</span>
            <span className="text-xs font-medium mt-1 leading-tight">{st.label}</span>
          </button>
        ))}
      </div>

      {/* Service name */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Service Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={serviceName}
          placeholder={`e.g. ${selectedMeta?.icon || ""} Production ${selectedMeta?.label || "Service"}`}
          onChange={(e) => setServiceName(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      {/* Config fields */}
      <ServiceConfigForm
        provider={provider}
        serviceType={selectedType}
        config={config}
        onChange={handleConfigChange}
        dynamicOptions={dynamicOptions}
      />

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button
          type="button"
          onClick={handleAdd}
          className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium
            hover:bg-blue-700 transition-colors"
        >
          Add Service
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 bg-gray-100 text-gray-600 rounded-lg py-2 text-sm font-medium
            hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Service list item
// ---------------------------------------------------------------------------

function ServiceListItem({ service, index, onRemove, onEdit }) {
  const typeMeta = Object.values(SERVICE_TYPES)
    .flat()
    .find((t) => t.value === service.service_type);

  return (
    <div className="flex items-start justify-between p-3 bg-white border border-gray-200
      rounded-xl hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-3">
        <div className="text-2xl mt-0.5">{typeMeta?.icon || "☁️"}</div>
        <div>
          <div className="font-medium text-sm text-gray-800">{service.service_name}</div>
          <div className="text-xs text-gray-500 mt-0.5">
            {typeMeta?.label || service.service_type}
          </div>
          {/* Config summary pills */}
          <div className="flex flex-wrap gap-1 mt-1.5">
            {Object.entries(service.config || {})
              .filter(([k]) => ["instance_type","machine_type","size","region","quantity",
                                "node_count","num_nodes","num_tasks","tier"].includes(k))
              .slice(0, 4)
              .map(([k, v]) => (
                <span key={k}
                  className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                  {k}: {v}
                </span>
              ))}
          </div>
        </div>
      </div>
      <div className="flex gap-1 ml-2">
        <button
          onClick={() => onRemove(index)}
          className="text-red-400 hover:text-red-600 text-xs px-2 py-1 rounded-lg
            hover:bg-red-50 transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component: BillOfMaterials
// ---------------------------------------------------------------------------

export default function BillOfMaterials({ onBOMCreated }) {
  // Step 1 state
  const [step,           setStep]           = useState(1);
  const [bomName,        setBomName]        = useState("");
  const [provider,       setProvider]       = useState("aws");
  const [azureHybrid,    setAzureHybrid]    = useState(false);

  // Step 2 state
  const [services,       setServices]       = useState([]);
  const [showAddPanel,   setShowAddPanel]   = useState(false);

  // Step 3 / global state
  const [savedBOM,       setSavedBOM]       = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [success,        setSuccess]        = useState(false);

  // -------------------------------------------------------------------------
  // Step 1 → Step 2: Create the BOM shell in DB
  // -------------------------------------------------------------------------
  const handleStep1Next = async () => {
    if (!bomName.trim()) {
      setError("Please enter a BOM name.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const bom = await createBOM(bomName.trim(), provider, azureHybrid, [], "USD");
      setSavedBOM(bom);
      setStep(2);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : e.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Step 2: Add / remove services
  // -------------------------------------------------------------------------
  const handleAddService = useCallback((service) => {
    setServices((prev) => [...prev, service]);
    setShowAddPanel(false);
  }, []);

  const handleRemoveService = useCallback((index) => {
    setServices((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleStep2Next = () => {
    if (services.length === 0) {
      setError("Add at least one service before continuing.");
      return;
    }
    setError(null);
    setStep(3);
  };

  // -------------------------------------------------------------------------
  // Step 3: Save services to backend → complete
  // -------------------------------------------------------------------------
  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      const updated = await updateBOMServices(savedBOM.id, services, {
        azureHybridBenefit: azureHybrid,
      });
      setSuccess(true);
      if (onBOMCreated) onBOMCreated(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : e.message);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------------------
  // Reset
  // -------------------------------------------------------------------------
  const handleReset = () => {
    setStep(1);
    setBomName("");
    setProvider("aws");
    setAzureHybrid(false);
    setServices([]);
    setShowAddPanel(false);
    setSavedBOM(null);
    setError(null);
    setSuccess(false);
  };

  // =========================================================================
  // Render
  // =========================================================================

  if (success && savedBOM) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="text-center py-12 bg-green-50 rounded-2xl border border-green-200">
          <div className="text-5xl mb-4">✅</div>
          <h2 className="text-xl font-bold text-green-800 mb-2">BOM Saved!</h2>
          <p className="text-green-700 text-sm mb-1">
            <strong>{savedBOM.name}</strong> ({savedBOM.cloud_provider.toUpperCase()})
          </p>
          <p className="text-green-600 text-sm mb-6">
            {services.length} service{services.length !== 1 ? "s" : ""} added.
            {azureHybrid && provider === "azure" && " Azure Hybrid Benefit enabled."}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleReset}
              className="px-5 py-2 bg-white border border-green-400 text-green-700 rounded-xl
                text-sm font-medium hover:bg-green-50 transition-colors"
            >
              Create Another BOM
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Bill of Materials</h1>
        <p className="text-sm text-gray-500 mt-1">
          Define your cloud services to generate multi-model cost scenarios.
        </p>
      </div>

      <StepIndicator currentStep={step} />

      {/* Error banner */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* STEP 1 — Create BOM                                                  */}
      {/* ------------------------------------------------------------------ */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-800 mb-5">
            1. Name your BOM &amp; choose a cloud provider
          </h2>

          {/* BOM name */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              BOM Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={bomName}
              placeholder="e.g. Production Infrastructure Q2 2026"
              onChange={(e) => setBomName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStep1Next()}
              className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          {/* Provider */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cloud Provider
            </label>
            <ProviderSelector
              value={provider}
              onChange={(p) => {
                setProvider(p);
                if (p !== "azure") setAzureHybrid(false);
              }}
            />
          </div>

          {/* AHB toggle — Azure only */}
          {provider === "azure" && (
            <AzureHybridBenefitToggle
              value={azureHybrid}
              onChange={setAzureHybrid}
            />
          )}

          <button
            type="button"
            onClick={handleStep1Next}
            disabled={loading}
            className="mt-6 w-full bg-blue-600 text-white rounded-xl py-3 font-medium
              hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Creating…" : "Next: Add Services →"}
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* STEP 2 — Add Services                                                */}
      {/* ------------------------------------------------------------------ */}
      {step === 2 && (
        <div className="space-y-4">
          {/* BOM context header */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3
            flex items-center justify-between">
            <div>
              <span className="font-semibold text-blue-800 text-sm">{bomName}</span>
              <span className="ml-2 text-xs text-blue-600 uppercase font-medium">
                {provider}
              </span>
              {azureHybrid && (
                <span className="ml-2 text-xs text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                  AHB On
                </span>
              )}
            </div>
            <span className="text-xs text-blue-500">
              {services.length} service{services.length !== 1 ? "s" : ""}
            </span>
          </div>

          {/* Services list */}
          {services.length > 0 && (
            <div className="space-y-2">
              {services.map((svc, idx) => (
                <ServiceListItem
                  key={idx}
                  service={svc}
                  index={idx}
                  onRemove={handleRemoveService}
                />
              ))}
            </div>
          )}

          {/* Add service panel or trigger */}
          {showAddPanel ? (
            <AddServicePanel
              provider={provider}
              onAdd={handleAddService}
              onCancel={() => setShowAddPanel(false)}
            />
          ) : (
            <button
              type="button"
              onClick={() => setShowAddPanel(true)}
              className="w-full border-2 border-dashed border-gray-300 rounded-2xl py-6
                text-sm text-gray-500 hover:border-blue-400 hover:text-blue-500
                hover:bg-blue-50 transition-all"
            >
              ➕ Add a Service
            </button>
          )}

          {/* Navigation */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-5 py-2.5 border border-gray-300 text-gray-600 rounded-xl
                text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleStep2Next}
              disabled={services.length === 0}
              className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm
                font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
            >
              Next: Review →
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* STEP 3 — Review & Save                                               */}
      {/* ------------------------------------------------------------------ */}
      {step === 3 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-800 mb-4">
            3. Review your BOM before saving
          </h2>

          {/* BOM summary card */}
          <div className="bg-gray-50 rounded-xl p-4 mb-5 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">BOM Name</span>
              <span className="font-medium text-gray-800">{bomName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Cloud Provider</span>
              <span className="font-medium text-gray-800 uppercase">{provider}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Services</span>
              <span className="font-medium text-gray-800">{services.length}</span>
            </div>
            {provider === "azure" && (
              <div className="flex justify-between">
                <span className="text-gray-500">Azure Hybrid Benefit</span>
                <span className={`font-medium ${azureHybrid ? "text-amber-600" : "text-gray-400"}`}>
                  {azureHybrid ? "✅ Enabled" : "Disabled"}
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">Currency</span>
              <span className="font-medium text-gray-800">USD</span>
            </div>
          </div>

          {/* Services detail */}
          <div className="space-y-2 mb-6 max-h-72 overflow-y-auto pr-1">
            {services.map((svc, idx) => {
              const typeMeta = Object.values(SERVICE_TYPES)
                .flat()
                .find((t) => t.value === svc.service_type);
              return (
                <div key={idx}
                  className="flex items-center justify-between p-3 bg-gray-50
                    rounded-xl border border-gray-100 text-sm">
                  <div className="flex items-center gap-2">
                    <span>{typeMeta?.icon || "☁️"}</span>
                    <div>
                      <div className="font-medium text-gray-800">{svc.service_name}</div>
                      <div className="text-xs text-gray-500">{typeMeta?.label || svc.service_type}</div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {svc.config?.region || ""}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Note about pricing */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-xs
            text-blue-700 mb-5">
            💡 After saving, go to <strong>Scenarios</strong> and click{" "}
            <strong>Generate Scenarios</strong> to fetch live prices and see
            cost breakdowns across all applicable pricing models.
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-5 py-2.5 border border-gray-300 text-gray-600 rounded-xl
                text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              ← Back
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={loading}
              className="flex-1 bg-green-600 text-white rounded-xl py-2.5 text-sm
                font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Saving…" : "✅ Save BOM"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
