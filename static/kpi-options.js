document.addEventListener("DOMContentLoaded", () => {
  const incomeTypes = ["主合同收入", "VO变更款项收入"];

  document.querySelectorAll("form").forEach((form) => {
    const paymentType = form.querySelector('[name="payment_type"]');
    const kpiConfig = form.querySelector(".kpi-config");
    if (!paymentType || !kpiConfig) return;

    const included = kpiConfig.querySelector('[name="kpi_included"]');
    const year = kpiConfig.querySelector('[name="kpi_year"]');
    const hasStages = form.querySelector('[name="has_stages"]');
    const syncKpiOptions = () => {
      const applicable = incomeTypes.includes(paymentType.value) && !(hasStages && hasStages.checked);
      kpiConfig.hidden = !applicable;
      included.disabled = !applicable;
      year.disabled = !applicable || !included.checked;
      year.required = applicable && included.checked;

      if (!applicable) {
        included.checked = false;
        year.value = "";
      }
    };

    paymentType.addEventListener("change", syncKpiOptions);
    included.addEventListener("change", syncKpiOptions);
    if (hasStages) hasStages.addEventListener("change", syncKpiOptions);
    syncKpiOptions();
  });
});
