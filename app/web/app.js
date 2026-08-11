const $ = (selector) => document.querySelector(selector);

const state = { chatController: null };

function setStatus(selector, message, tone = "") {
  const element = $(selector);
  element.textContent = message;
  element.className = `panel-status ${tone}`.trim();
}

function escapeText(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatError(error) {
  return error?.detail?.detail || error?.detail || error?.message || "请求失败，请查看服务日志。";
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json") ? await response.json() : await response.text();
  if (!response.ok) throw new Error(formatError(payload));
  return payload;
}

function documentCard(document) {
  const tags = (document.tags || []).map((tag) => `<span>${escapeText(tag)}</span>`).join("");
  return `<div class="document-item"><strong title="${escapeText(document.filename)}">${escapeText(document.filename)}</strong><div class="item-meta"><span>${escapeText(document.status)}</span><span>${escapeText(document.chunk_count)} chunks</span>${tags}</div></div>`;
}

function renderRetrievalStages(stages) {
  $("#search-stages").innerHTML = (stages || []).map((stage) => {
    const latency = stage.latency_ms == null ? "未启用" : `${Number(stage.latency_ms).toFixed(1)}ms`;
    return `<span class="stage" title="${escapeText(stage.status || "unknown")}">${escapeText(stage.name)} · ${escapeText(latency)}</span>`;
  }).join("");
}

async function loadHealth() {
  const dot = $(".status-dot");
  try {
    const health = await request("/health");
    dot.className = "status-dot ok";
    $("#health-status").textContent = "服务运行正常";
    $("#health-detail").textContent = `${health.dependencies?.vector_store || "local"} · ${health.version || "Insight"}`;
  } catch (error) {
    dot.className = "status-dot error";
    $("#health-status").textContent = "服务不可用";
    $("#health-detail").textContent = formatError(error);
  }
}

async function loadDocuments() {
  const list = $("#document-list");
  list.innerHTML = `<div class="empty-state">正在加载资料库…</div>`;
  try {
    const documents = await request("/documents?limit=100");
    list.innerHTML = documents.length ? documents.map(documentCard).join("") : `<div class="empty-state">还没有资料。选择一份 PDF、Markdown 或 TXT 开始。</div>`;
    setStatus("#document-status", `${documents.length} 份资料已加载`, "success");
  } catch (error) {
    list.innerHTML = `<div class="empty-state">无法加载资料库。</div>`;
    setStatus("#document-status", formatError(error), "error");
  }
}

async function waitForJob(jobId) {
  for (;;) {
    const job = await request(`/jobs/${encodeURIComponent(jobId)}`);
    const progress = job.total_chunks ? Math.round((job.processed_chunks / job.total_chunks) * 100) : 0;
    setStatus("#document-status", `索引任务 ${job.status} · ${progress}%`);
    if (["succeeded", "failed", "cancelled"].includes(job.status)) return job;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

$("#upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("#document-file").files[0];
  if (!file) return;
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  setStatus("#document-status", `正在上传 ${file.name}…`);
  try {
    const form = new FormData();
    form.append("file", file);
    const result = await request("/documents/upload", { method: "POST", body: form });
    if (result.job_id) {
      const job = await waitForJob(result.job_id);
      if (job.status !== "succeeded") throw new Error(job.error || `索引任务 ${job.status}`);
    }
    setStatus("#document-status", "索引完成，资料已加入知识库。", "success");
    event.currentTarget.reset();
    await loadDocuments();
  } catch (error) {
    setStatus("#document-status", formatError(error), "error");
  } finally {
    button.disabled = false;
  }
});

$("#refresh-documents").addEventListener("click", loadDocuments);

$("#search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = $("#search-query").value.trim();
  if (!query) return;
  setStatus("#search-status", "正在混合检索…");
  $("#search-results").innerHTML = `<div class="empty-state">正在召回相关片段…</div>`;
  try {
    const result = await request("/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, top_k: 8 }) });
    const results = result.retrieval_results || [];
    renderRetrievalStages(result.stages);
    $("#search-results").innerHTML = results.length ? results.map((item) => `<div class="result-item"><strong>${escapeText(item.source?.filename || item.chunk?.filename || "未命名片段")}<span class="score">${Number(item.score || 0).toFixed(4)}</span></strong><p>${escapeText(item.chunk?.text || item.text || "")}</p><div class="result-source"><span>${escapeText(item.source?.section || item.chunk?.section || "正文")}</span><span>${escapeText(item.source?.chunk_id || item.chunk?.chunk_id || "")}</span></div></div>`).join("") : `<div class="empty-state">当前知识库中没有匹配片段。</div>`;
    setStatus("#search-status", `${results.length} 条结果 · ${Number(result.latency_ms || 0).toFixed(1)} ms`, results.length ? "success" : "");
  } catch (error) {
    $("#search-results").innerHTML = `<div class="empty-state">检索失败。</div>`;
    setStatus("#search-status", formatError(error), "error");
  }
});

function renderSources(sources) {
  $("#chat-sources").innerHTML = (sources || []).map((source, index) => `<div class="source-item"><strong>[${index + 1}] ${escapeText(source.filename || source.source || "来源")}</strong><div class="source-meta"><span>${escapeText(source.page ? `第 ${source.page} 页` : source.section || "正文")}</span><span>${escapeText(source.chunk_id || "")}</span></div></div>`).join("");
}

function renderStages(stages) {
  $("#chat-stages").innerHTML = (stages || []).map((stage) => `<span class="stage">${escapeText(stage.name)}${stage.latency_ms ? ` · ${Number(stage.latency_ms).toFixed(0)}ms` : ""}</span>`).join("");
}

async function consumeSse(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const eventLine = block.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = block.split("\n").find((line) => line.startsWith("data:"));
      if (eventLine && dataLine) onEvent(eventLine.slice(6).trim(), JSON.parse(dataLine.slice(5).trim()));
    }
    if (done) break;
  }
}

$("#chat-stop").addEventListener("click", () => {
  state.chatController?.abort();
  state.chatController = null;
  $("#chat-stop").classList.add("hidden");
  $("#chat-submit").classList.remove("hidden");
  setStatus("#chat-status", "已停止，已保留收到的回答内容。");
});

$("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = $("#chat-query").value.trim();
  if (!query) return;
  state.chatController = new AbortController();
  $("#chat-submit").classList.add("hidden");
  $("#chat-stop").classList.remove("hidden");
  $("#answer-card").innerHTML = `<p></p>`;
  $("#chat-sources").innerHTML = "";
  $("#chat-stages").innerHTML = "";
  let answer = "";
  let sources = [];
  let refused = false;
  setStatus("#chat-status", "正在检索并生成回答…");
  try {
    const response = await fetch("/chat/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }), signal: state.chatController.signal });
    if (!response.ok) throw new Error(await response.text());
    await consumeSse(response, (eventName, data) => {
      if (eventName === "token") answer += data.text || "";
      if (eventName === "complete") {
        answer = data.answer || answer;
        refused = data.status === "refused";
        renderStages(data.stages || []);
      }
      if (eventName === "source") {
        sources = [...sources, data];
        renderSources(sources);
      }
      if (eventName === "retrieval") renderStages(data.stages || []);
      if (eventName === "fallback") {
        refused = true;
        setStatus("#chat-status", data.answer || "当前知识库中没有足够信息。", "error");
      }
      $("#answer-card p").textContent = answer || data.answer || "";
    });
    setStatus("#chat-status", refused ? "当前知识库中没有足够信息。" : answer ? "回答完成，内容来自当前检索上下文。" : "当前知识库中没有足够信息。", refused || !answer ? "error" : "success");
  } catch (error) {
    if (error.name !== "AbortError") setStatus("#chat-status", formatError(error), "error");
  } finally {
    state.chatController = null;
    $("#chat-stop").classList.add("hidden");
    $("#chat-submit").classList.remove("hidden");
  }
});

loadHealth();
loadDocuments();
