const CATALOG_PATH = "content/design_catalog_v0.1.json";

const stageLabels = {
  IMPLEMENTED: "已有页面",
  DESIGN_BRIEF: "设计简报",
  CATALOG_SLOT: "目录槽位",
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function stageChip(stage) {
  const chip = element("span", `catalog-stage stage-${stage.toLowerCase()}`, stageLabels[stage] || stage);
  chip.dataset.stage = stage;
  return chip;
}

function commaList(values) {
  return Array.isArray(values) ? values.join(" · ") : "待下一轮定义";
}

function renderFirstWave(data) {
  const root = document.querySelector("#first-wave-grid");
  root.replaceChildren();
  const families = new Map(data.families.map((family) => [family.id, family]));
  const works = new Map(data.works.map((work) => [work.index, work]));
  const entries = data.joints.filter((joint) => joint.wave === "FIRST_10");

  entries.forEach((joint) => {
    const article = element("article", "catalog-brief");
    const top = element("div", "catalog-brief-top");
    const index = element("span", "catalog-index", `${joint.index} · ${families.get(joint.family_id).name}`);
    top.append(index, stageChip(joint.design_stage));

    article.append(top, element("h3", "", joint.name_cn));
    article.append(element("p", "catalog-goal", joint.teaching_goal));

    const dl = element("dl", "catalog-facts");
    [
      ["装配动作", joint.assembly_action],
      ["关键参数", commaList(joint.key_parameters)],
      ["未来实验", joint.future_experiment],
      ["作品映射", joint.work_ids.map((id) => works.get(id)?.name_cn || id).join(" · ")],
    ].forEach(([term, description]) => {
      dl.append(element("dt", "", term), element("dd", "", description));
    });
    article.append(dl);

    if (joint.chapter_path) {
      const link = element("a", "catalog-link", "打开现有章节 →");
      link.href = joint.chapter_path;
      article.append(link);
    }
    root.append(article);
  });
}

function renderFamilies(data) {
  const root = document.querySelector("#family-grid");
  root.replaceChildren();
  data.families.forEach((family) => {
    const card = element("article", "catalog-family");
    card.append(
      element("span", "catalog-index", family.id),
      element("h3", "", family.name),
      element("p", "", family.editorial_question),
    );

    const list = element("ol", "catalog-family-list");
    data.joints.filter((joint) => joint.family_id === family.id).forEach((joint) => {
      const item = element("li");
      const label = element("span", "", `${joint.index} ${joint.name_cn}`);
      item.append(label, stageChip(joint.design_stage));
      list.append(item);
    });
    card.append(list);
    root.append(card);
  });
}

function renderWorks(data) {
  const root = document.querySelector("#work-grid");
  root.replaceChildren();
  const jointNames = new Map(data.joints.map((joint) => [joint.id, joint.name_cn]));

  data.works.forEach((work) => {
    const card = element("article", "catalog-work");
    const top = element("div", "catalog-brief-top");
    top.append(
      element("span", "catalog-index", `${work.index} · ${work.position}`),
      stageChip(work.design_stage),
    );
    card.append(top, element("h3", "", work.name_cn), element("p", "catalog-goal", work.teaching_goal));

    const jointList = work.joint_ids.map((id) => jointNames.get(id) || id).join(" · ");
    const dl = element("dl", "catalog-facts");
    dl.append(element("dt", "", "连接映射"), element("dd", "", jointList));
    if (work.design_questions) {
      dl.append(element("dt", "", "设计问题"), element("dd", "", commaList(work.design_questions)));
    }
    if (work.evidence_boundary) {
      dl.append(element("dt", "", "边界"), element("dd", "", work.evidence_boundary));
    }
    card.append(dl);

    if (work.case_path) {
      const link = element("a", "catalog-link", "打开现有案例 →");
      link.href = work.case_path;
      card.append(link);
    }
    root.append(card);
  });
}

function renderLabs(data) {
  const root = document.querySelector("#lab-grid");
  root.replaceChildren();
  data.experiment_chapters.forEach((lab) => {
    const card = element("article", "catalog-lab");
    card.append(element("span", "catalog-index", lab.index), element("h3", "", lab.name_cn), stageChip(lab.status));
    if (lab.path) {
      const link = element("a", "catalog-link", "打开实验章 →");
      link.href = lab.path;
      card.append(link);
    }
    root.append(card);
  });
}

function renderSources(data) {
  const root = document.querySelector("#catalog-sources");
  root.replaceChildren();
  Object.values(data.sources).forEach((source) => {
    const item = element("li");
    if (source.url) {
      const link = element("a", "", source.title);
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      item.append(link);
    } else {
      const link = element("a", "", source.title);
      link.href = source.path;
      item.append(link);
    }
    item.append(document.createTextNode(` · ${source.organization || "仓库内"} · ${source.use}`));
    root.append(item);
  });
}

async function initCatalog() {
  const response = await fetch(CATALOG_PATH);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();

  renderFirstWave(data);
  renderFamilies(data);
  renderWorks(data);
  renderLabs(data);
  renderSources(data);
  document.documentElement.dataset.catalogReady = "true";
}

initCatalog().catch((error) => {
  document.documentElement.dataset.catalogReady = "error";
  document.querySelectorAll("[data-catalog-loading]").forEach((node) => {
    node.textContent = `设计目录载入失败：${error.message}。请通过 npm run dev 访问本页。`;
  });
});
