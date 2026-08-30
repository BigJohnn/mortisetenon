document.querySelectorAll("[data-model-control]").forEach((button) => {
  button.addEventListener("click", () => {
    const panel = document.querySelector("#modelPanel");
    if (!panel) return;

    const mode = button.dataset.modelControl;
    document.querySelectorAll("[data-model-control]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    panel.classList.remove("exploded", "sectioned", "playing");

    if (mode === "explode") panel.classList.add("exploded");
    if (mode === "section") panel.classList.add("sectioned");
    if (mode === "play") panel.classList.add("playing");
  });
});

const slider = document.querySelector("#clearanceRange");
if (slider) {
  const value = document.querySelector("#clearanceValue");
  const peg = document.querySelector("#clearancePeg");
  const verdict = document.querySelector("#clearanceVerdict");

  const update = () => {
    const clearance = Number.parseFloat(slider.value);
    value.textContent = `${clearance.toFixed(2)} mm`;
    peg.style.setProperty("--peg", `${116 - (clearance - 0.1) * 85}px`);
    verdict.textContent =
      clearance < 0.16 ? "非常紧" : clearance < 0.25 ? "顺滑 / 推荐起点" : clearance < 0.34 ? "略松" : "明显松";
  };

  slider.addEventListener("input", update);
  update();
}

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const target = document.querySelector(anchor.getAttribute("href"));
    if (!target) return;

    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

const initPrintLog = (form) => {
  const asset = {
    id: form.dataset.assetId,
    version: form.dataset.assetVersion,
    sha256: form.dataset.assetSha256,
  };
  const storageKey = `printable-joinery:print-log:${asset.id}:${asset.version}`;
  const status = form.querySelector("[data-log-status]");
  const resultRows = [...form.querySelectorAll("[data-clearance]")];
  const dateInput = form.elements.recorded_at;
  let saveTimer;

  const localDate = () => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  };

  const fieldKey = (control) => {
    if (control.name) return `name:${control.name}`;
    const row = control.closest("[data-clearance]");
    return row ? `result:${row.dataset.clearance}:${control.dataset.field}` : "";
  };

  const saveDraft = () => {
    const draft = {};
    form.querySelectorAll("input, select, textarea").forEach((control) => {
      const key = fieldKey(control);
      if (key) draft[key] = control.value;
    });
    localStorage.setItem(storageKey, JSON.stringify(draft));
    status.textContent = "草稿已在本机保存";
  };

  const restoreDraft = () => {
    let draft;
    try {
      draft = JSON.parse(localStorage.getItem(storageKey) || "null");
    } catch {
      localStorage.removeItem(storageKey);
    }

    if (!draft) {
      dateInput.value = localDate();
      return;
    }

    form.querySelectorAll("input, select, textarea").forEach((control) => {
      const key = fieldKey(control);
      if (key && Object.hasOwn(draft, key)) control.value = draft[key];
    });
    if (!dateInput.value) dateInput.value = localDate();
    status.textContent = "已恢复本机草稿";
  };

  const typedValue = (control) => {
    if (!control || control.value === "") return null;
    if (control.type === "number") return Number(control.value);
    if (control.value === "true") return true;
    if (control.value === "false") return false;
    return control.value;
  };

  const readResult = (row) => {
    const result = {
      nominal_clearance_total_mm: Number(row.dataset.clearance),
    };

    row.querySelectorAll("[data-field]").forEach((control) => {
      const key = control.dataset.field;
      const value = typedValue(control);
      const numeric = key === "insertion_force_1_5" || key === "withdrawal_force_1_5";
      result[key] = numeric && value !== null ? Number(value) : value;
    });

    return result;
  };

  const readLog = () => {
    const values = new FormData(form);
    return {
      schema_version: "0.2",
      evidence_state: "PRINT_LOG_DRAFT",
      asset,
      experiment: {
        id: values.get("experiment_id"),
        recorded_at: values.get("recorded_at"),
      },
      print_conditions: {
        printer_model: values.get("printer_model"),
        slicer: values.get("slicer"),
        slicer_version: values.get("slicer_version"),
        material: values.get("material"),
        material_brand: values.get("material_brand"),
        nozzle_mm: Number(values.get("nozzle_mm")),
        layer_height_mm: Number(values.get("layer_height_mm")),
        walls: Number(values.get("walls")),
        infill_percent: Number(values.get("infill_percent")),
        orientation: values.get("orientation"),
        scale_percent: Number(values.get("scale_percent")),
      },
      results: resultRows.map(readResult),
      photo_refs: values.get("photo_refs"),
      run_notes: values.get("run_notes"),
    };
  };

  const validateLog = () => {
    let firstMissing = null;

    resultRows.forEach((row) => {
      row.querySelectorAll("[data-field]").forEach((control) => {
        const missing = control.value === "" && !("optional" in control.dataset);
        control.setCustomValidity(missing ? "请完成此项记录" : "");
        if (missing && !firstMissing) firstMissing = control;
      });
    });

    if (!form.reportValidity()) {
      status.textContent = "请先完成打印条件和四档结果";
      firstMissing?.focus();
      return false;
    }
    return true;
  };

  const csvCell = (value) => {
    if (value === null || value === undefined) return "";
    let text = String(value);
    if (/^[=+@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };

  // Result columns vary by asset — the straight tenon records withdrawal force and
  // shoulder seating, the test kit does not — so the header is read off the rows.
  const toCsv = (log) => {
    const runColumns = [
      ["schema_version", () => log.schema_version],
      ["experiment_id", () => log.experiment.id],
      ["recorded_at", () => log.experiment.recorded_at],
      ["asset_id", () => log.asset.id],
      ["asset_version", () => log.asset.version],
      ["asset_sha256", () => log.asset.sha256],
      ["printer_model", () => log.print_conditions.printer_model],
      ["slicer", () => log.print_conditions.slicer],
      ["slicer_version", () => log.print_conditions.slicer_version],
      ["material", () => log.print_conditions.material],
      ["material_brand", () => log.print_conditions.material_brand],
      ["nozzle_mm", () => log.print_conditions.nozzle_mm],
      ["layer_height_mm", () => log.print_conditions.layer_height_mm],
      ["walls", () => log.print_conditions.walls],
      ["infill_percent", () => log.print_conditions.infill_percent],
      ["orientation", () => log.print_conditions.orientation],
      ["scale_percent", () => log.print_conditions.scale_percent],
    ];
    const resultColumns = [...new Set(log.results.flatMap((result) => Object.keys(result)))];
    const headers = [...runColumns.map(([name]) => name), ...resultColumns, "notes", "photo_refs"];

    const rows = log.results.map((result) => [
      ...runColumns.map(([, read]) => read()),
      ...resultColumns.map((key) => result[key]),
      log.run_notes,
      log.photo_refs,
    ]);

    return [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\n");
  };

  const download = (content, type, filename) => {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  form.addEventListener("input", (event) => {
    event.target.setCustomValidity?.("");
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveDraft, 250);
  });

  form.querySelectorAll("[data-export-log]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!validateLog()) return;

      const log = readLog();
      const runId = String(log.experiment.id || "run-01")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-")
        .replace(/^-|-$/g, "");
      // Matches the print-log path in ASSET_CONTRACT.md so the file can be
      // dropped into content/print-logs/ without renaming.
      const basename = `${log.experiment.recorded_at}_${asset.id}_${asset.version}_${runId || "run-01"}`;

      if (button.dataset.exportLog === "json") {
        download(JSON.stringify(log, null, 2), "application/json", `${basename}.json`);
      } else {
        download(toCsv(log), "text/csv;charset=utf-8", `${basename}.csv`);
      }
      status.textContent = `${button.dataset.exportLog.toUpperCase()} 已导出`;
    });
  });

  form.querySelector("[data-clear-log]").addEventListener("click", () => {
    if (!window.confirm(`清空 ${form.dataset.assetLabel} 在当前浏览器中的实验草稿？已下载的文件不会受影响。`)) return;
    localStorage.removeItem(storageKey);
    form.reset();
    dateInput.value = localDate();
    resultRows.forEach((row) => {
      row.querySelectorAll("[data-field]").forEach((control) => control.setCustomValidity(""));
    });
    status.textContent = "本机草稿已清空";
  });

  restoreDraft();
};

const printLogForms = [...document.querySelectorAll("form[data-print-log]")];
printLogForms.forEach(initPrintLog);

document.querySelectorAll("[data-log-tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.logTab;
    document.querySelectorAll("[data-log-tab]").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    printLogForms.forEach((form) => {
      form.classList.toggle("is-hidden", form.dataset.assetId !== target);
    });
  });
});

// Every joint model on this site ships one clip named "Explode", running from the
// assembled pose to the separated pose. Playback is never handed to the element:
// keeping it paused and writing currentTime ourselves is what lets the same clip
// run forwards, backwards and under the reader's finger.
const createExplodeViewer = ({
  viewer,
  panel,
  status,
  range,
  readout,
  goalButtons,
  goalAttribute,
  cycleButton,
  page,
  evidence,
}) => {
  if (!viewer || !range || !readout) return;
  const controls = [...goalButtons, cycleButton].filter(Boolean);

  let duration = 0;
  // The page opens on the separated frame, which is also what the fallback image
  // shows, so handing over from the static evidence to the live model does not jump.
  let position = 1;
  let goal = 1;
  let cycling = false;
  let frame = null;
  let lastTick = 0;

  const label = (fraction) => {
    if (fraction < 0.01) return "装配位置";
    if (fraction > 0.99) return "完全分离";
    return `拆开 ${Math.round(fraction * 100)}%`;
  };

  const render = () => {
    // A looping clip wraps at exactly its duration, which would snap the model back
    // to the assembled pose the moment it finishes separating. Stop one frame short.
    viewer.currentTime = Math.min(position * duration, duration - 1 / 30);
    range.value = String(Math.round(position * 1000));
    readout.textContent = label(position);
  };

  const stop = () => {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
  };

  const setActive = (button) => {
    controls.forEach((item) => item.classList.toggle("active", item === button));
  };

  const run = (target) => {
    goal = target;
    if (position === goal || frame !== null) return;
    lastTick = performance.now();
    const step = (now) => {
      const seconds = Math.min((now - lastTick) / 1000, 0.1);
      lastTick = now;
      const direction = Math.sign(goal - position);
      const next = position + (direction * seconds) / duration;
      position = direction > 0 ? Math.min(next, goal) : Math.max(next, goal);
      render();

      if (position !== goal) {
        frame = requestAnimationFrame(step);
        return;
      }
      frame = null;
      if (cycling) {
        goal = position > 0.5 ? 0 : 1;
        window.setTimeout(() => cycling && run(goal), 700);
      }
    };
    frame = requestAnimationFrame(step);
  };

  const reportLoadFailure = (message) => {
    panel?.classList.add("model-load-failed");
    if (status) status.textContent = message;
  };

  if (window.location.protocol === "file:") {
    reportLoadFailure(`交互 3D 模型需要通过 HTTP 打开；请在项目根目录运行 npm run dev，再访问 http://localhost:8000/${page}。`);
  }

  viewer.addEventListener("error", () => {
    reportLoadFailure(`3D 模型未能载入；请确认页面通过 HTTP 打开，并检查模型资源是否可访问。${evidence}`);
  });

  viewer.addEventListener("load", () => {
    panel?.classList.add("model-ready");
    panel?.classList.remove("model-load-failed");
    // play() then pause() creates the animation action, so currentTime becomes
    // seekable while nothing is actually running.
    viewer.play();
    viewer.pause();
    duration = viewer.duration || 2.4;
    render();
    [...controls, range].forEach((item) => item.removeAttribute("disabled"));
  });

  goalButtons.forEach((button) => {
    button.addEventListener("click", () => {
      cycling = false;
      setActive(button);
      run(Number(button.dataset[goalAttribute]));
    });
  });

  cycleButton?.addEventListener("click", () => {
    if (cycling) {
      cycling = false;
      stop();
      // Stopping mid-cycle leaves the model between the two poses, so no preset is active.
      setActive(null);
      return;
    }
    cycling = true;
    setActive(cycleButton);
    run(position > 0.5 ? 0 : 1);
  });

  range.addEventListener("input", () => {
    cycling = false;
    stop();
    position = Number(range.value) / 1000;
    goal = position;
    setActive(null);
    render();
  });

  [...controls, range].forEach((item) => item.setAttribute("disabled", ""));
};

createExplodeViewer({
  viewer: document.querySelector("#explodeViewer"),
  panel: document.querySelector("#modelPanel"),
  status: document.querySelector("[data-model-status]"),
  range: document.querySelector("#explodeRange"),
  readout: document.querySelector("#explodeReadout"),
  goalButtons: [...document.querySelectorAll("[data-explode-goal]")],
  goalAttribute: "explodeGoal",
  cycleButton: document.querySelector("[data-explode-cycle]"),
  page: "joints/straight-tenon.html",
  evidence: "下方保留同源爆炸图作为静态证据。",
});

createExplodeViewer({
  viewer: document.querySelector("#dovetailViewer"),
  panel: document.querySelector("#dovetailModelPanel"),
  status: document.querySelector("[data-dovetail-model-status]"),
  range: document.querySelector("#dovetailRange"),
  readout: document.querySelector("#dovetailReadout"),
  goalButtons: [...document.querySelectorAll("[data-dovetail-goal]")],
  goalAttribute: "dovetailGoal",
  cycleButton: document.querySelector("[data-dovetail-cycle]"),
  page: "joints/dovetail.html",
  evidence: "这里保留首轮打印实物照片作为证据。",
});

createExplodeViewer({
  viewer: document.querySelector("#keyedViewer"),
  panel: document.querySelector("#keyedModelPanel"),
  status: document.querySelector("[data-keyed-model-status]"),
  range: document.querySelector("#keyedRange"),
  readout: document.querySelector("#keyedReadout"),
  goalButtons: [...document.querySelectorAll("[data-keyed-goal]")],
  goalAttribute: "keyedGoal",
  cycleButton: document.querySelector("[data-keyed-cycle]"),
  page: "joints/keyed-tenon.html",
  evidence: "这里保留静态爆炸示意图作为退路。",
});
