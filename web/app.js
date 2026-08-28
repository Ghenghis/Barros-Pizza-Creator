"use strict";

const state = {
  api: localStorage.getItem("barros.api") || "/api",
  token: localStorage.getItem("barros.token") || "",
  pairToken: localStorage.getItem("barros.pairToken") || "",
  bridgeName: localStorage.getItem("barros.bridgeName") || "",
  latest: null,
  latestMessage: "",
  recorder: null,
  chunks: [],
  muted: false,
  installPrompt: null,
};

const $ = selector => document.querySelector(selector);
const $$ = selector => Array.from(document.querySelectorAll(selector));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 3500);
}

function cleanBase(value) {
  const trimmed = String(value || "").trim().replace(/\/+$/, "");
  return trimmed || "/api";
}

async function api(path, options = {}) {
  const headers = {"Content-Type": "application/json", ...(options.headers || {})};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeout || 90000);
  try {
    const response = await fetch(cleanBase(state.api) + path, {...options, headers, signal: controller.signal});
    const result = await response.json().catch(() => ({ok: false, error: `HTTP ${response.status}`}));
    if (!response.ok || !result.ok) throw new Error(result.error || `HTTP ${response.status}`);
    return result;
  } finally {
    clearTimeout(timer);
  }
}

async function health() {
  const badge = $("#statusBadge");
  try {
    const result = await api("/health", {method: "GET", timeout: 6000});
    badge.classList.add("online");
    badge.classList.remove("offline");
    badge.querySelector("span").textContent = "Creator online";
    $("#providerValue").textContent = result.online ? result.provider : "Offline AI";
    $("#voiceValue").textContent = result.tts && result.tts.configured ? "Ready" : "Text only";
  } catch (error) {
    badge.classList.remove("online");
    badge.classList.add("offline");
    badge.querySelector("span").textContent = "Needs connection";
    $("#providerValue").textContent = "Unavailable";
  }
}

function activatePanel(name) {
  $$(".mode-tab").forEach(button => button.classList.toggle("active", button.dataset.panel === name));
  $$(".panel").forEach(panel => panel.classList.toggle("active", panel.id === `${name}Panel`));
  history.replaceState(null, "", name === "design" ? location.pathname : `?mode=${encodeURIComponent(name)}`);
}

function payloadBase(prompt) {
  return api("/catalog", {method: "GET", timeout: 10000}).then(result => ({
    prompt,
    catalog: Array.isArray(result.catalog) ? result.catalog : (result.catalog.catalog || result.catalog.ingredients || []),
    constraints: {
      shape: $("#shapeSelect").value,
      heat: $("#heatSelect").value,
      max_ingredients: 9,
      profit_factor: .6,
    },
    count: 1,
    local_only: false,
  }));
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function scoreBlock(scores = {}) {
  const row = element("div", "score-row");
  [["taste", "Taste"], ["popularity", "Appeal"], ["originality", "Original"]].forEach(([key, label]) => {
    const item = element("div");
    item.append(element("strong", "", Math.round(Number(scores[key] || 0))), element("span", "", label));
    row.append(item);
  });
  return row;
}

function recipeCard(recipe, index) {
  const card = element("article", "recipe-card");
  const art = element("div", "recipe-art", recipe.artwork && recipe.artwork.enabled ? "✦" : "🍕");
  const title = element("h3", "", recipe.name || `Pizza ${index + 1}`);
  const summary = element("p", "muted", recipe.summary || recipe.rationale || "A game-valid pizza design.");
  const ingredients = (recipe.ingredients || []).map(item => item.id).filter(Boolean);
  const ingredientLine = element("div", "ingredient-list", ingredients.length ? ingredients.join(" · ") : "Ingredient placement plan ready");
  const actions = element("div", "recipe-actions");
  const copy = element("button", "secondary-button", "Copy recipe");
  copy.type = "button";
  copy.addEventListener("click", async () => {
    await navigator.clipboard.writeText(JSON.stringify(recipe, null, 2));
    toast("Recipe copied.");
  });
  const send = element("button", "primary-button", "Send to Windows");
  send.type = "button";
  send.addEventListener("click", () => sendToWindows(index));
  actions.append(copy, send);
  card.append(art, title, summary, scoreBlock(recipe.scores), ingredientLine, actions);
  return card;
}

function renderResult(result) {
  state.latest = result;
  state.latestMessage = result.message || "Your pizza design is ready.";
  const section = $("#resultsSection");
  section.classList.remove("hidden");
  $("#resultProvider").textContent = result.provider || "Barro's designer";
  $("#resultMessage").textContent = state.latestMessage;
  const grid = $("#recipeGrid");
  grid.replaceChildren(...(result.recipes || []).map(recipeCard));
  $("#workflowDesign").classList.add("done");
  section.scrollIntoView({behavior: "smooth", block: "start"});
}

function setBusy(button, busy, label) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = label;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
  }
}

async function createDesign(endpoint = "/compose") {
  const button = endpoint === "/crew" ? $("#crewButton") : $("#designButton");
  const prompt = $("#designPrompt").value.trim();
  if (!prompt) return toast("Describe the pizza first.");
  setBusy(button, true, endpoint === "/crew" ? "Crew is debating…" : "Designing…");
  try {
    const payload = await payloadBase(prompt);
    if (endpoint === "/compose" && $("#detailSelect").value === "High") {
      payload.prompt = `Create a high-detail ingredient artwork with deliberate color, outline, and shape placement. ${payload.prompt}`;
    }
    const result = await api(endpoint, {method: "POST", body: JSON.stringify(payload)});
    renderResult(result);
    if (endpoint === "/crew") renderCrew(result.agents || []);
  } catch (error) {
    toast(error.message.includes("token") ? "Open Settings and enter the private VPS access token." : error.message);
  } finally {
    setBusy(button, false);
  }
}

function renderCrew(agents) {
  const grid = $("#crewGrid");
  if (!agents.length) return;
  grid.replaceChildren(...agents.map((agent, index) => {
    const card = element("article", `agent-card message ${["flavor", "cost", "scout", "creative"][index % 4]}`);
    const initials = String(agent.agent || "AI").split(/\s+/).map(part => part[0]).join("").slice(0, 2);
    const body = element("div");
    body.append(element("h3", "", agent.agent || "Design agent"), element("p", "", agent.message || agent.role || "Ready."));
    card.append(element("b", "", initials), body);
    return card;
  }));
}

async function pairWindows() {
  const code = $("#pairCode").value.trim();
  if (!/^\d{6}$/.test(code)) return toast("Enter the six-digit code shown on Windows.");
  const button = $("#pairButton");
  setBusy(button, true, "Pairing…");
  try {
    const result = await api("/pairing/connect", {
      method: "POST",
      body: JSON.stringify({pair_code: code, device_name: $("#deviceName").value.trim() || "Android companion"}),
    });
    state.pairToken = result.pair_token;
    state.bridgeName = result.bridge_name;
    localStorage.setItem("barros.pairToken", state.pairToken);
    localStorage.setItem("barros.bridgeName", state.bridgeName);
    updatePairState();
    toast(`Paired with ${state.bridgeName}.`);
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
}

function updatePairState() {
  $("#pairValue").textContent = state.pairToken ? (state.bridgeName || "Paired") : "Not paired";
  $("#unpairButton").classList.toggle("hidden", !state.pairToken);
  $("#workflowPair").classList.toggle("done", Boolean(state.pairToken));
}

async function sendToWindows(index) {
  if (!state.latest || !state.latest.recipes || !state.latest.recipes[index]) return toast("Create a design first.");
  if (!state.pairToken) {
    activatePanel("connect");
    return toast("Pair this device with the Windows bridge first.");
  }
  const payload = {...state.latest, recipes: [state.latest.recipes[index]]};
  try {
    const result = await api("/bridge/jobs", {
      method: "POST",
      body: JSON.stringify({pair_token: state.pairToken, action: "preview", payload}),
    });
    toast(`Sent to Windows · job ${result.job_id.slice(0, 8)}.`);
  } catch (error) {
    if (/not paired/i.test(error.message)) {
      state.pairToken = "";
      localStorage.removeItem("barros.pairToken");
      updatePairState();
    }
    toast(error.message);
  }
}

function toBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function toggleMicrophone() {
  const button = $("#micButton");
  if (state.recorder && state.recorder.state === "recording") {
    state.recorder.stop();
    return;
  }
  if (!navigator.mediaDevices || !window.MediaRecorder) return toast("This browser does not provide microphone recording.");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true}});
    state.chunks = [];
    state.recorder = new MediaRecorder(stream);
    state.recorder.addEventListener("dataavailable", event => event.data.size && state.chunks.push(event.data));
    state.recorder.addEventListener("stop", async () => {
      button.classList.remove("recording");
      button.querySelector("strong").textContent = "Tap to talk";
      stream.getTracks().forEach(track => track.stop());
      $("#micStatus").textContent = "Transcribing…";
      try {
        const blob = new Blob(state.chunks, {type: state.recorder.mimeType || "audio/webm"});
        const result = await api("/transcribe", {method: "POST", body: JSON.stringify({audio_base64: await toBase64(blob), filename: "android-voice.webm"})});
        $("#designPrompt").value = result.text;
        $("#micStatus").textContent = `Heard: “${result.text}”`;
        activatePanel("design");
      } catch (error) {
        $("#micStatus").textContent = error.message;
        toast(error.message);
      }
    });
    state.recorder.start();
    button.classList.add("recording");
    button.querySelector("strong").textContent = "Tap to stop";
    $("#micStatus").textContent = "Listening…";
  } catch (error) {
    toast(`Microphone unavailable: ${error.message}`);
  }
}

async function speakLatest() {
  if (!state.latestMessage) return toast("Create or ask the crew for a design first.");
  if (state.muted) return toast("Voice playback is muted.");
  const button = $("#speakButton");
  setBusy(button, true, "Preparing voice…");
  try {
    const result = await api("/speak", {method: "POST", body: JSON.stringify({
      agent: "Creative Director",
      message: state.latestMessage,
      voice: $("#voiceSelect").value,
      rate: Number($("#rateRange").value),
    })});
    const audio = new Audio(`data:${result.mime_type || "audio/wav"};base64,${result.audio_base64}`);
    await audio.play();
  } catch (error) {
    toast(error.message);
  } finally {
    setBusy(button, false);
  }
}

function saveSettings() {
  state.api = cleanBase($("#apiInput").value);
  state.token = $("#tokenInput").value.trim();
  localStorage.setItem("barros.api", state.api);
  localStorage.setItem("barros.token", state.token);
  $("#settingsDialog").close();
  health();
  toast("Connection saved. Testing the Creator service…");
}

function wire() {
  $$(".mode-tab").forEach(button => button.addEventListener("click", () => activatePanel(button.dataset.panel)));
  $$("[data-prompt]").forEach(button => button.addEventListener("click", () => { $("#designPrompt").value = button.dataset.prompt; }));
  $("#surpriseButton").addEventListener("click", () => { $("#designPrompt").value = "Surprise me with a distinctive, colorful pizza artwork that is practical in the real ingredient catalog."; });
  $("#designButton").addEventListener("click", () => createDesign("/compose"));
  $("#crewButton").addEventListener("click", () => createDesign("/crew"));
  $("#pairButton").addEventListener("click", pairWindows);
  $("#unpairButton").addEventListener("click", () => {
    state.pairToken = ""; state.bridgeName = "";
    localStorage.removeItem("barros.pairToken"); localStorage.removeItem("barros.bridgeName");
    updatePairState(); toast("Windows pairing forgotten on this device.");
  });
  $("#micButton").addEventListener("click", toggleMicrophone);
  $("#speakButton").addEventListener("click", speakLatest);
  $("#muteButton").addEventListener("click", event => { state.muted = !state.muted; event.currentTarget.textContent = state.muted ? "Muted" : "Sound on"; });
  $("#rateRange").addEventListener("input", event => { $("#rateOutput").textContent = `${Number(event.target.value).toFixed(2)}×`; });
  $("#settingsButton").addEventListener("click", () => {
    $("#apiInput").value = state.api;
    $("#tokenInput").value = state.token;
    $("#settingsDialog").showModal();
  });
  $("#saveSettingsButton").addEventListener("click", event => { event.preventDefault(); saveSettings(); });
  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault(); state.installPrompt = event; $("#installButton").classList.remove("hidden");
  });
  $("#installButton").addEventListener("click", async () => {
    if (!state.installPrompt) return;
    state.installPrompt.prompt(); await state.installPrompt.userChoice;
    state.installPrompt = null; $("#installButton").classList.add("hidden");
  });
}

async function init() {
  wire();
  const width = window.innerWidth;
  $("#deviceLabel").textContent = width >= 900 ? "TABLET STUDIO" : "MOBILE STUDIO";
  $("#deviceName").value = width >= 900 ? "Samsung Tab S9+" : "Samsung S21 Ultra";
  updatePairState();
  const requested = new URLSearchParams(location.search).get("mode");
  if (["design", "crew", "voice", "connect"].includes(requested)) activatePanel(requested);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  await health();
  if (!state.token && state.api !== "http://127.0.0.1:48173") toast("Open Settings to add the private Creator access token.");
  while (document.visibilityState === "visible") {
    await sleep(30000);
    await health();
  }
}

init();
