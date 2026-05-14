let currentData = null;

mermaid.initialize({ startOnLoad: false, theme: "default" });

function useSample(text) {
  document.getElementById("prompt").value = text;
}

function clearAll() {
  document.getElementById("prompt").value = "";
  document.getElementById("results").classList.remove("active");
  document.getElementById("error").classList.remove("active");
  currentData = null;
}

async function generate() {
  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) return showError("请输入工作流描述");

  setLoading(true);
  hideError();
  document.getElementById("results").classList.remove("active");

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `请求失败 (${res.status})`);
    }
    currentData = await res.json();
    renderResults(currentData);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  document.getElementById("spinner").classList.toggle("active", on);
  document.getElementById("submit").disabled = on;
}

function showError(msg) {
  const el = document.getElementById("error");
  el.textContent = "错误：" + msg;
  el.classList.add("active");
}

function hideError() {
  document.getElementById("error").classList.remove("active");
}

function renderResults(data) {
  document.getElementById("results").classList.add("active");
  document.getElementById("workflow-title").textContent = data.workflow.title;
  document.getElementById("workflow-desc").textContent = data.workflow.description;

  renderMermaid(data.mermaid_code);
  renderAPIEndpoints(data.api_spec.endpoints);
  renderDecisions(data.decision_nodes);
  renderRaw(data);

  // reset tabs
  switchTab("diagram");
}

async function renderMermaid(code) {
  const container = document.getElementById("mermaid-render");
  container.innerHTML = "";
  try {
    const { svg } = await mermaid.render("mermaid-svg", code);
    container.innerHTML = svg;
  } catch (e) {
    container.innerHTML =
      '<pre style="color:#f85149">Mermaid 渲染失败:\n' +
      e.message +
      "\n\n原始代码:\n" +
      code +
      "</pre>";
  }
}

function renderAPIEndpoints(endpoints) {
  const container = document.getElementById("api-endpoints");
  if (!endpoints.length) {
    container.innerHTML = '<p style="color:#8b949e">此工作流暂无 API 端点</p>';
    return;
  }
  container.innerHTML = endpoints
    .map(
      (ep) => `
    <div class="card">
      <div class="endpoint">
        <span class="method ${ep.method}">${ep.method}</span>
        <strong>${ep.path}</strong>
      </div>
      <p style="color:#8b949e;margin-top:8px">${ep.description}</p>
      ${renderJSONBlock("请求体", ep.request_body)}
      ${renderJSONBlock("响应体", ep.response_body)}
    </div>`
    )
    .join("");
}

function renderJSONBlock(label, obj) {
  if (!obj || !Object.keys(obj).length) return "";
  return (
    `<p style="color:#8b949e;margin-top:10px;font-size:0.82rem">${label}:</p>` +
    `<div class="json-block">${JSON.stringify(obj, null, 2)}</div>`
  );
}

function renderDecisions(nodes) {
  const countEl = document.getElementById("decision-count");
  const container = document.getElementById("decision-list");

  if (!nodes.length) {
    countEl.textContent = "";
    container.innerHTML =
      '<p style="color:#8b949e">此工作流不需要人类决策 — AI 可独立完成所有步骤</p>';
    return;
  }

  countEl.textContent = "（" + nodes.length + "）";
  container.innerHTML = nodes
    .map(
      (d) => `
    <div class="card decision-card">
      <div class="question">${d.question}</div>
      ${d.tradeoffs.map((t) => `<div class="tradeoff">${t}</div>`).join("")}
      <div class="accountability">${d.human_accountability}</div>
    </div>`
    )
    .join("");
}

function renderRaw(data) {
  document.getElementById("raw-json").textContent = JSON.stringify(data, null, 2);
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
  document
    .querySelector('.tab[onclick="switchTab(\'' + name + "')\"]")
    .classList.add("active");
  document.getElementById("tab-" + name).classList.add("active");
}

// Re-render mermaid on tab switch since it needs visible container
const origSwitchTab = switchTab;
switchTab = function (name) {
  origSwitchTab(name);
  if (name === "diagram" && currentData) {
    renderMermaid(currentData.mermaid_code);
  }
};

function downloadJSON() {
  if (!currentData) return;
  const blob = new Blob([JSON.stringify(currentData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download =
    "flowmind-" + (currentData.workflow.title || "workflow") + ".json";
  a.click();
  URL.revokeObjectURL(url);
}
