document.addEventListener("DOMContentLoaded", () => {
  const report = document.querySelector(".weekly-report");
  if (!report) return;
  const reports = JSON.parse(report.dataset.reports || "[]"), input = document.querySelector("#weekly-year"), total = document.querySelector("#weekly-total"), description = document.querySelector("#weekly-description"), chart = document.querySelector("#weekly-chart"), legend = document.querySelector("#weekly-legend"), colors = ["#ef1746", "#ff9f1c", "#247ba0", "#6a994e", "#7b61ff", "#db7093"], currency = (amount) => new Intl.NumberFormat("zh-CN", {style:"currency",currency:"CNY"}).format(amount || 0);
  const render = () => {
    const selected = reports.find((item) => String(item.year) === input.value), items = selected ? selected.breakdown : [];
    total.textContent = selected ? currency(selected.kpi) : "—";
    description.textContent = selected ? `${selected.year} 年项目的 KPI 汇总` : "暂无该年份项目数据";
    legend.innerHTML = "";
    if (!items.length) { chart.style.background = "#f0f2f4"; chart.innerHTML = "<span>暂无 KPI</span>"; return; }
    const amount = items.reduce((sum,item) => sum + item.amount, 0); let progress = 0;
    chart.style.background = `conic-gradient(${items.map((item,index) => { const next = progress + item.amount / amount * 360, segment = `${colors[index % colors.length]} ${progress}deg ${next}deg`; progress = next; return segment; }).join(",")})`;
    chart.innerHTML = `<span>${items.length} 项<br><small>KPI 年份</small></span>`;
    items.forEach((item,index) => { const row = document.createElement("div"); row.innerHTML = `<i style="background:${colors[index % colors.length]}"></i><span>${item.year} 年 KPI</span><b>${currency(item.amount)}</b>`; legend.appendChild(row); });
  };
  input.addEventListener("input", render); render();
});
