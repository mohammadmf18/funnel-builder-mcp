'use strict';
const form = document.getElementById('lead-form');
if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button');
    const status = document.getElementById('result');
    button.disabled = true;
    status.textContent = 'جارٍ التسجيل…';
    try {
      const response = await fetch(form.dataset.endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({page_id: form.dataset.pageId, email: form.elements.email.value}),
      });
      if (!response.ok) throw new Error('تعذر التسجيل. تحقق من البريد وحاول مجددًا.');
      const result = await response.json();
      status.textContent = 'تم تسجيلك بنجاح.';
      if (result.next_url) window.location.assign(result.next_url);
      else form.reset();
    } catch (error) {
      status.textContent = error.message || 'تعذر الاتصال بالخادم. حاول مجددًا.';
    } finally {
      button.disabled = false;
    }
  });
}
