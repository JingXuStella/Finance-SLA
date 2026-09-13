document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach((form) => {
    const amount = form.querySelector('[name="receivable_amount"]');
    const invoiced = form.querySelector('[name="invoice_amount"]');
    const status = form.querySelector('[name="invoice_status"]');
    if (!amount || !invoiced || !status) return;
    const sync = () => {
      const total = Number(amount.value || 0), value = Number(invoiced.value || 0);
      if (total > 0) status.value = value >= total ? '已开票' : '未开票';
    };
    amount.addEventListener('input', sync); invoiced.addEventListener('input', sync); sync();
  });
});
