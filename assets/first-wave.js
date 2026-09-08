const FIRST_WAVE_PATH = "content/first_wave_v0.1.json";

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function linkEl(label, href, className = "") {
  const link = el("a", className, label);
  link.href = href;
  if (/^https?:/.test(href)) {
    link.target = "_blank";
    link.rel = "noreferrer";
  }
  return link;
}

function list(items, className = "") {
  const ul = el("ul", className);
  items.forEach((item) => ul.append(el("li", "", item)));
  return ul;
}

function badge(text, tone = "neutral") {
  return el("span", `wave-badge wave-badge-${tone}`, text);
}

function isOpenDecision(item) {
  return (item.status || "OPEN") === "OPEN";
}

function sourceLinks(sourceIds, sources) {
  const wrap = el("div", "wave-source-links");
  sourceIds.forEach((sourceId) => {
    const source = sources[sourceId];
    if (!source) return;
    const target = source.url || source.path;
    wrap.append(linkEl(source.title, target));
  });
  return wrap;
}

function renderAssistanceItem(item, owner) {
  const open = isOpenDecision(item);
  const card = el("article", `help-card${open ? "" : " help-card-resolved"}`);
  card.dataset.priority = item.priority;
  card.dataset.status = open ? "open" : "resolved";
  const top = el("div", "help-card-top");
  top.append(
    badge(open ? `${item.id} · ${item.priority}优先级` : `${item.id} · 已确认`, open ? (item.priority === "最高" ? "urgent" : "attention") : "ready"),
    el("span", "help-owner", owner),
  );
  card.append(top, el("h3", "", item.question));

  const facts = el("dl", "help-facts");
  const factItems = open
    ? [["默认方案", item.default], ["影响", item.impact], ["推进边界", item.blocks]]
    : [["确认结果", item.resolution], ["原默认", item.default], ["后续边界", item.blocks]];
  factItems.forEach(([term, value]) => {
    facts.append(el("dt", "", term), el("dd", "", value));
  });
  card.append(facts);
  return card;
}

function renderHelp(data) {
  const root = document.querySelector("#help-grid");
  root.replaceChildren();
  const entries = [...data.joints, ...data.works];
  const decisions = entries.flatMap((entry) => entry.user_assistance.map((item) => ({ item, owner: `${entry.index} ${entry.name_cn}` })));
  const priority = { "最高": 0, "高": 1, "中": 2, "低": 3 };
  decisions.sort((a, b) => Number(!isOpenDecision(a.item)) - Number(!isOpenDecision(b.item)) || (priority[a.item.priority] ?? 9) - (priority[b.item.priority] ?? 9));
  decisions.forEach(({ item, owner }) => root.append(renderAssistanceItem(item, owner)));
  const openCount = decisions.filter(({ item }) => isOpenDecision(item)).length;
  document.querySelector("#decision-count").textContent = String(openCount);
  document.querySelector("#resolved-count").textContent = String(decisions.length - openCount);
}

function renderParts(parts) {
  const grid = el("div", "wave-parts-grid");
  parts.forEach((part) => {
    const card = el("div", "wave-part");
    card.append(el("strong", "", part.name), el("p", "", part.role));
    grid.append(card);
  });
  return grid;
}

function renderSteps(steps) {
  const ol = el("ol", "wave-steps");
  steps.forEach((step) => {
    const item = el("li");
    item.append(el("span", "wave-step-num", step.step));
    const body = el("div");
    body.append(el("h4", "", step.title), el("p", "", step.action), el("small", "", `观察：${step.watch}`));
    item.append(body);
    ol.append(item);
  });
  return ol;
}

function renderParameters(parameters) {
  const wrap = el("div", "table-wrap wave-parameter-table");
  const table = el("table");
  const thead = el("thead");
  const headRow = el("tr");
  ["参数", "名称", "在设计中负责什么", "本轮状态"].forEach((title) => headRow.append(el("th", "", title)));
  thead.append(headRow);
  const tbody = el("tbody");
  parameters.forEach((parameter) => {
    const row = el("tr");
    row.append(
      el("td", "wave-symbol", parameter.symbol),
      el("td", "", parameter.name),
      el("td", "", parameter.role),
      el("td", "", parameter.status),
    );
    tbody.append(row);
  });
  table.append(thead, tbody);
  wrap.append(table);
  return wrap;
}

function renderAssistance(items, owner) {
  const wrap = el("section", "wave-assistance");
  wrap.append(el("div", "kicker", items.some(isOpenDecision) ? "需要你协助" : "作者决策记录"));
  items.forEach((item) => wrap.append(renderAssistanceItem(item, owner)));
  return wrap;
}

function renderJoint(joint, sources) {
  const article = el("article", "wave-entry");
  article.id = joint.id;
  article.dataset.kind = "joint";
  article.dataset.needsUser = joint.user_assistance.some(isOpenDecision) ? "true" : "false";

  const header = el("header", "wave-entry-header");
  const titleWrap = el("div");
  titleWrap.append(el("span", "catalog-index", `${joint.index} · ${joint.family}`), el("h3", "", joint.name_cn), el("p", "en-title", joint.name_en));
  const status = el("div", "wave-entry-status");
  status.append(
    badge(joint.review_state === "NEEDS_USER" ? "有作者决策" : joint.review_state === "EXISTING_CHAPTER" ? "已有章节" : "可进 CAD", joint.review_state === "NEEDS_USER" ? "attention" : "ready"),
    badge(joint.evidence_state, "neutral"),
  );
  header.append(titleWrap, status);
  article.append(header, el("p", "big-quote wave-thesis", joint.one_sentence));

  const question = el("div", "wave-question");
  question.append(el("span", "", "教学问题"), el("p", "", joint.teaching_question));
  article.append(question);

  const split = el("div", "wave-two-col");
  const confirmed = el("section", "wave-panel wave-confirmed");
  confirmed.append(el("div", "kicker", "来源已确认"), list(joint.confirmed));
  const proposal = el("section", "wave-panel wave-proposal");
  proposal.append(el("div", "kicker", "本轮设计提案"), el("p", "", joint.design_proposal.model_scope));
  const boundary = el("p", "mini wave-boundary", `本轮不做：${joint.design_proposal.not_in_scope}`);
  proposal.append(boundary);
  split.append(confirmed, proposal);
  article.append(split);

  const partsSection = el("section", "wave-subsection");
  partsSection.append(el("h4", "", "零件与职责"), renderParts(joint.design_proposal.parts));
  article.append(partsSection);

  const stepsSection = el("section", "wave-subsection");
  stepsSection.append(el("h4", "", "装配顺序与观察点"), renderSteps(joint.assembly_steps));
  article.append(stepsSection);

  const parameterSection = el("section", "wave-subsection");
  parameterSection.append(el("h4", "", "参数接口"), renderParameters(joint.parameters));
  article.append(parameterSection);

  const tail = el("div", "wave-two-col wave-tail");
  const deliverables = el("section", "wave-panel");
  deliverables.append(el("div", "kicker", "进入 CAD 后交付"), list(joint.cad_deliverables));
  const debt = el("section", "wave-panel wave-debt");
  debt.append(el("div", "kicker", "实验债务 · 暂缓"), list(joint.experiment_debt));
  tail.append(deliverables, debt);
  article.append(tail);

  if (joint.user_assistance.length) article.append(renderAssistance(joint.user_assistance, `${joint.index} ${joint.name_cn}`));

  const footer = el("footer", "wave-entry-footer");
  footer.append(sourceLinks(joint.source_ids, sources));
  if (joint.chapter_path) footer.append(linkEl("打开现有章节 →", joint.chapter_path, "catalog-link"));
  article.append(footer);
  return article;
}

function renderJointMap(items, jointNames) {
  const grid = el("div", "wave-joint-map");
  items.forEach((item) => {
    const card = el("div");
    card.append(el("strong", "", jointNames.get(item.joint_id) || item.joint_id), el("p", "", item.role));
    grid.append(card);
  });
  return grid;
}

function renderWork(work, sources, jointNames) {
  const article = el("article", "wave-entry wave-work-entry");
  article.id = work.id;
  article.dataset.kind = "work";
  article.dataset.needsUser = work.user_assistance.some(isOpenDecision) ? "true" : "false";

  const header = el("header", "wave-entry-header");
  const titleWrap = el("div");
  titleWrap.append(el("span", "catalog-index", `${work.index} · 综合作品`), el("h3", "", work.name_cn), el("p", "en-title", work.name_en));
  const status = el("div", "wave-entry-status");
  const reviewLabel = work.review_state === "NEEDS_USER"
    ? "有作者决策"
    : work.review_state === "PROVISIONAL_MAPPING" ? "映射待审计" : "可进 CAD";
  status.append(
    badge(reviewLabel, work.review_state === "NEEDS_USER" ? "attention" : "ready"),
    badge(work.evidence_state, "neutral"),
  );
  header.append(titleWrap, status);
  article.append(header, el("p", "big-quote wave-thesis", work.one_sentence));

  const question = el("div", "wave-question");
  question.append(el("span", "", "作品问题"), el("p", "", work.teaching_question));
  article.append(question);

  const split = el("div", "wave-two-col");
  const confirmed = el("section", "wave-panel wave-confirmed");
  confirmed.append(el("div", "kicker", "来源 / 现状已确认"), list(work.confirmed));
  const brief = el("section", "wave-panel wave-proposal");
  brief.append(el("div", "kicker", "功能简报"));
  const dl = el("dl", "catalog-facts wave-brief-facts");
  const briefItems = Object.entries(work.functional_brief).map(([key, value]) => {
    const labels = { use: "用途", default_envelope: "默认尺度", opening: "开口策略", top_strategy: "上部策略", audit_strategy: "审计策略", not_in_scope: "本轮不做" };
    return [labels[key] || key, value];
  });
  briefItems.forEach(([term, value]) => dl.append(el("dt", "", term), el("dd", "", value)));
  brief.append(dl);
  split.append(confirmed, brief);
  article.append(split);

  const partsSection = el("section", "wave-subsection");
  partsSection.append(el("h4", "", "作品 BOM 与职责"), renderParts(work.parts));
  article.append(partsSection);

  const mapSection = el("section", "wave-subsection");
  mapSection.append(el("h4", "", "榫卯映射"), renderJointMap(work.joint_map, jointNames));
  article.append(mapSection);

  const stepsSection = el("section", "wave-subsection");
  stepsSection.append(el("h4", "", "装配 / 审计顺序"), renderSteps(work.assembly_steps));
  article.append(stepsSection);

  const tail = el("div", "wave-two-col wave-tail");
  const deliverables = el("section", "wave-panel");
  deliverables.append(el("div", "kicker", "进入 CAD 后交付"), list(work.cad_deliverables));
  const debt = el("section", "wave-panel wave-debt");
  debt.append(el("div", "kicker", "实验债务 · 暂缓"), list(work.experiment_debt));
  tail.append(deliverables, debt);
  article.append(tail);

  if (work.user_assistance.length) article.append(renderAssistance(work.user_assistance, `${work.index} ${work.name_cn}`));

  const footer = el("footer", "wave-entry-footer");
  footer.append(sourceLinks(work.source_ids, sources));
  if (work.case_path) footer.append(linkEl("打开现有案例 →", work.case_path, "catalog-link"));
  article.append(footer);
  return article;
}

function setupFilters() {
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const entries = [...document.querySelectorAll(".wave-entry")];
  const readout = document.querySelector("#filter-readout");

  function applyFilter(filter) {
    let visible = 0;
    entries.forEach((entry) => {
      const show = filter === "all"
        || (filter === "needs-user" && entry.dataset.needsUser === "true")
        || (filter === "joints" && entry.dataset.kind === "joint")
        || (filter === "works" && entry.dataset.kind === "work");
      entry.hidden = !show;
      if (show) visible += 1;
    });
    buttons.forEach((button) => {
      const active = button.dataset.filter === filter;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    readout.textContent = `显示 ${visible} / ${entries.length} 项`;
  }

  buttons.forEach((button) => button.addEventListener("click", () => applyFilter(button.dataset.filter)));
  applyFilter("all");
}

async function initFirstWave() {
  const response = await fetch(FIRST_WAVE_PATH);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  const jointNames = new Map(data.joints.map((joint) => [joint.id, joint.name_cn]));

  renderHelp(data);
  const jointRoot = document.querySelector("#joint-content");
  jointRoot.replaceChildren(...data.joints.map((joint) => renderJoint(joint, data.sources)));
  const workRoot = document.querySelector("#work-content");
  workRoot.replaceChildren(...data.works.map((work) => renderWork(work, data.sources, jointNames)));
  setupFilters();
  document.documentElement.dataset.waveReady = "true";

  if (window.location.hash) {
    requestAnimationFrame(() => document.querySelector(window.location.hash)?.scrollIntoView());
  }
}

initFirstWave().catch((error) => {
  document.documentElement.dataset.waveReady = "error";
  document.querySelectorAll("[data-wave-loading]").forEach((node) => {
    node.textContent = `首轮内容载入失败：${error.message}。请通过 npm run dev 访问本页。`;
  });
  document.querySelector("#filter-readout").textContent = "内容载入失败";
});
