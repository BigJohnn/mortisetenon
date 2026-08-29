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

const clearanceLogForm = document.querySelector("#clearanceLogForm");
if (clearanceLogForm) {
  const storageKey = "printable-joinery:clearance-log:v0.1";
  const status = document.querySelector("#logStatus");
  const resultRows = [...clearanceLogForm.querySelectorAll("[data-clearance]")];
  const dateInput = clearanceLogForm.elements.recorded_at;
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
    clearanceLogForm.querySelectorAll("input, select, textarea").forEach((control) => {
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

    clearanceLogForm.querySelectorAll("input, select, textarea").forEach((control) => {
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
      result[key] = key === "insertion_force_1_5" && value !== null ? Number(value) : value;
    });

    return result;
  };

  const readLog = () => {
    const values = new FormData(clearanceLogForm);
    return {
      schema_version: "0.1",
      evidence_state: "PRINT_LOG_DRAFT",
      asset: {
        id: "clearance-test-kit",
        version: "v0.1",
        sha256: "954d6ad649288818c5ac5d0ae942dd9d28c60e10cc2959c39f9532008840231d",
      },
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
        const missing = control.value === "";
        control.setCustomValidity(missing ? "请完成此项记录" : "");
        if (missing && !firstMissing) firstMissing = control;
      });
    });

    if (!clearanceLogForm.reportValidity()) {
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

  const toCsv = (log) => {
    const headers = [
      "schema_version",
      "experiment_id",
      "recorded_at",
      "asset_id",
      "asset_version",
      "printer_model",
      "slicer",
      "slicer_version",
      "material",
      "material_brand",
      "nozzle_mm",
      "layer_height_mm",
      "walls",
      "infill_percent",
      "orientation",
      "scale_percent",
      "nominal_clearance_total_mm",
      "peg_measured_x_mm",
      "peg_measured_y_mm",
      "socket_measured_x_mm",
      "socket_measured_y_mm",
      "inserts_without_force",
      "insertion_force_1_5",
      "removable_by_hand",
      "fit_class",
      "defects",
      "notes",
      "photo_refs",
    ];

    const rows = log.results.map((result) => [
      log.schema_version,
      log.experiment.id,
      log.experiment.recorded_at,
      log.asset.id,
      log.asset.version,
      log.print_conditions.printer_model,
      log.print_conditions.slicer,
      log.print_conditions.slicer_version,
      log.print_conditions.material,
      log.print_conditions.material_brand,
      log.print_conditions.nozzle_mm,
      log.print_conditions.layer_height_mm,
      log.print_conditions.walls,
      log.print_conditions.infill_percent,
      log.print_conditions.orientation,
      log.print_conditions.scale_percent,
      result.nominal_clearance_total_mm,
      result.peg_measured_x_mm,
      result.peg_measured_y_mm,
      result.socket_measured_x_mm,
      result.socket_measured_y_mm,
      result.inserts_without_force,
      result.insertion_force_1_5,
      result.removable_by_hand,
      result.fit_class,
      result.defects,
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

  clearanceLogForm.addEventListener("input", (event) => {
    event.target.setCustomValidity?.("");
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveDraft, 250);
  });

  clearanceLogForm.querySelectorAll("[data-export-log]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!validateLog()) return;

      const log = readLog();
      const runId = String(log.experiment.id || "run-01")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]+/g, "-")
        .replace(/^-|-$/g, "");
      const basename = `${log.experiment.recorded_at}_clearance-test-kit_v0.1_${runId || "run-01"}`;

      if (button.dataset.exportLog === "json") {
        download(JSON.stringify(log, null, 2), "application/json", `${basename}.json`);
      } else {
        download(toCsv(log), "text/csv;charset=utf-8", `${basename}.csv`);
      }
      status.textContent = `${button.dataset.exportLog.toUpperCase()} 已导出`;
    });
  });

  clearanceLogForm.querySelector("[data-clear-log]").addEventListener("click", () => {
    if (!window.confirm("清空当前浏览器中的实验草稿？已下载的文件不会受影响。")) return;
    localStorage.removeItem(storageKey);
    clearanceLogForm.reset();
    dateInput.value = localDate();
    resultRows.forEach((row) => {
      row.querySelectorAll("[data-field]").forEach((control) => control.setCustomValidity(""));
    });
    status.textContent = "本机草稿已清空";
  });

  restoreDraft();
}

const explodeViewer = document.querySelector("#explodeViewer");
if (explodeViewer) {
  const range = document.querySelector("#explodeRange");
  const readout = document.querySelector("#explodeReadout");
  const goalButtons = [...document.querySelectorAll("[data-explode-goal]")];
  const cycleButton = document.querySelector("[data-explode-cycle]");
  const controls = [...goalButtons, cycleButton];

  // The GLB carries one clip named "Explode". We never hand playback to the
  // element: keeping it paused and writing currentTime ourselves is what lets the
  // same clip run forwards, backwards and under the reader's finger.
  let duration = 0;
  // The page opens on the exploded frame, which is also what the poster shows, so
  // handing over from poster to live model does not jump.
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
    explodeViewer.currentTime = Math.min(position * duration, duration - 1 / 30);
    range.value = String(Math.round(position * 1000));
    readout.textContent = label(position);
  };

  const stop = () => {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
  };

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

  const run = (target) => {
    goal = target;
    if (position === goal || frame !== null) return;
    lastTick = performance.now();
    frame = requestAnimationFrame(step);
  };

  const setActive = (button) => {
    controls.forEach((item) => item.classList.toggle("active", item === button));
  };

  explodeViewer.addEventListener("load", () => {
    // play() then pause() creates the animation action, so currentTime becomes
    // seekable while nothing is actually running.
    explodeViewer.play();
    explodeViewer.pause();
    duration = explodeViewer.duration || 2.4;
    render();
    [...controls, range].forEach((item) => item.removeAttribute("disabled"));
  });

  goalButtons.forEach((button) => {
    button.addEventListener("click", () => {
      cycling = false;
      setActive(button);
      run(Number(button.dataset.explodeGoal));
    });
  });

  cycleButton.addEventListener("click", () => {
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
}
