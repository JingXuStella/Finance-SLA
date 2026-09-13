document.addEventListener('DOMContentLoaded', () => {
  const incomeTypes = ['主合同收入', 'VO变更款项收入'];
  document.querySelectorAll('form').forEach((form) => {
    const type = form.querySelector('[name="payment_type"]');
    const status = form.querySelector('[name="receipt_status"]');
    if (!type || !status) return;
    const sync = () => {
      const income = incomeTypes.includes(type.value);
      const allowed = income ? ['未收款', '部分收款', '已收款'] : ['未支付', '部分支付', '已支付'];
      [...status.options].forEach((option) => { option.hidden = !allowed.includes(option.value); option.disabled = !allowed.includes(option.value); });
      if (!allowed.includes(status.value)) status.value = allowed[0];
    };
    type.addEventListener('change', sync); sync();
  });
});
