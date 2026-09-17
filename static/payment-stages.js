document.addEventListener("DOMContentLoaded", () => {
  const incomeTypes = ["主合同收入", "VO变更款项收入"];
  const statusOptions = ["待处理", "逾期", "进行中", "完成"];

  document.querySelectorAll(".stage-config").forEach((config) => {
    const form = config.closest("form");
    const enabled = config.querySelector('[name="has_stages"]');
    const count = config.querySelector(".stage-count");
    const fields = config.querySelector(".stage-fields");
    const paymentType = form.querySelector('[name="payment_type"]');
    const values = (config.dataset.values || "").split(",").map((value) => value.trim());
    const statuses = (config.dataset.statuses || "").split(",").map((value) => value.trim());
    const kpiIncluded = (config.dataset.kpiIncluded || "").split(",").map((value) => value === "1");
    const kpiYears = (config.dataset.kpiYears || "").split(",").map((value) => value.trim());

    const isIncome = () => incomeTypes.includes(paymentType.value);
    const stageField = (tag, name, value = "") => {
      const field = document.createElement(tag);
      field.name = name;
      field.value = value;
      return field;
    };
    const render = () => {
      const number = Math.max(1, Math.min(10, Number(count.value) || 1));
      count.value = number;
      fields.innerHTML = "";
      for (let index = 1; index <= number; index += 1) {
        const group = document.createElement("div");
        group.className = "stage-field";
        const amountLabel = document.createElement("label");
        amountLabel.textContent = `第 ${index} 阶段金额`;
        const amount = stageField("input", `stage_amount_${index}`, values[index - 1] || "");
        amount.type = "text";
        amount.inputMode = "decimal";
        amount.required = enabled.checked;
        amountLabel.appendChild(amount);

        const statusLabel = document.createElement("label");
        statusLabel.textContent = "阶段状态";
        const status = stageField("select", `stage_status_${index}`);
        statusOptions.forEach((optionValue) => status.add(new Option(optionValue, optionValue, false, (statuses[index - 1] || "待处理") === optionValue)));
        statusLabel.appendChild(status);

        const kpiConfig = document.createElement("div");
        kpiConfig.className = "stage-kpi-config";
        const includedLabel = document.createElement("label");
        includedLabel.className = "checkbox";
        const included = stageField("input", `stage_kpi_included_${index}`);
        included.type = "checkbox";
        included.checked = kpiIncluded[index - 1];
        includedLabel.append(included, " 已计入 KPI");
        const yearLabel = document.createElement("label");
        yearLabel.textContent = "KPI 年份";
        const year = stageField("input", `stage_kpi_year_${index}`, kpiYears[index - 1] || "");
        year.type = "number";
        year.min = "2000";
        year.max = "2100";
        const syncKpi = () => {
          const applicable = isIncome();
          kpiConfig.hidden = !applicable;
          included.disabled = !applicable;
          year.disabled = !applicable || !included.checked;
          year.required = applicable && included.checked;
          if (!applicable) {
            included.checked = false;
            year.value = "";
          }
        };
        included.addEventListener("change", syncKpi);
        paymentType.addEventListener("change", syncKpi);
        syncKpi();
        yearLabel.appendChild(year);
        kpiConfig.append(includedLabel, yearLabel);
        group.append(amountLabel, statusLabel, kpiConfig);
        fields.appendChild(group);
      }
      fields.hidden = !enabled.checked;
      count.closest("label").hidden = !enabled.checked;
    };
    enabled.addEventListener("change", render);
    count.addEventListener("input", render);
    paymentType.addEventListener("change", render);
    render();
  });
});
