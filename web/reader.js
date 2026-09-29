"use strict";
(() => {
  const form = document.getElementById("filters");
  const cards = [...document.querySelectorAll(".card")];
  const status = document.getElementById("status");
  const empty = document.getElementById("empty");
  const ids = ["query", "minutes", "budget", "company", "energy", "chapter"];
  const fields = Object.fromEntries(ids.map(id => [id, document.getElementById(id)]));
  const levels = {low: 0, medium: 1, high: 2};
  const searchable = new Map(cards.map(card => [card, card.textContent.toLowerCase()]));
  const visible = () => cards.filter(card => !card.hidden);
  form.hidden = false;
  const playbooks = [...document.querySelectorAll(".playbook")];
  const guideQuery = document.getElementById("guide-query");
  const guideStatus = document.getElementById("guide-status");
  const guideText = new Map(playbooks.map(item => [item, item.textContent.toLowerCase()]));
  document.getElementById("guide-search-label").hidden = false;
  guideQuery.addEventListener("input", () => {
    const query = guideQuery.value.toLowerCase().trim();
    const words = query.split(/\s+/).filter(Boolean);
    playbooks.forEach(item => {
      item.hidden = /^p\d+$/.test(query) ? item.id !== query : !words.every(word => guideText.get(item).includes(word));
    });
    const count = playbooks.filter(item => !item.hidden).length;
    guideStatus.textContent = count ? `找到 ${count} 篇完整玩法。` : "没找到。可以减少关键词，不必改变自己的条件。";
  });
  const argumentsList = [...document.querySelectorAll(".argument")];
  const essayQuery = document.getElementById("essay-query");
  const argumentText = new Map(argumentsList.map(item => [item, item.textContent.toLowerCase()]));
  document.getElementById("essay-search-label").hidden = false;
  essayQuery.addEventListener("input", () => {
    const query = essayQuery.value.toLowerCase().trim();
    const words = query.split(/\s+/).filter(Boolean);
    argumentsList.forEach(item => {
      item.hidden = /^e\d+$/.test(query) ? item.id !== query : !words.every(word => argumentText.get(item).includes(word));
    });
    const count = argumentsList.filter(item => !item.hidden).length;
    document.getElementById("essay-status").textContent = count ? `找到 ${count} 篇核心论证。` : "没找到。可换一个具体问题，或清空关键词查看目录。";
  });

  function filter() {
    const words = fields.query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    cards.forEach(card => {
      const data = card.dataset;
      card.hidden = !(
        words.every(word => searchable.get(card).includes(word)) &&
        Number(data.minutes) <= Number(fields.minutes.value) &&
        Number(data.budget) <= Number(fields.budget.value) &&
        (fields.company.value === "any" || [fields.company.value, "either"].includes(data.company)) &&
        levels[data.energy] <= levels[fields.energy.value] &&
        (!fields.chapter.value || data.chapter === fields.chapter.value)
      );
    });
    const count = visible().length;
    status.textContent = `当前 ${count} / ${cards.length} 张。筛选只匹配主方案上限；展开查看完整条件。`;
    empty.hidden = count !== 0;
    document.getElementById("random").disabled = count === 0;
  }
  form.addEventListener("input", filter);
  form.addEventListener("change", filter);
  form.addEventListener("submit", event => event.preventDefault());
  form.addEventListener("reset", () => queueMicrotask(filter));

  function openHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    if (target.classList.contains("argument") && target.hidden) {
      essayQuery.value = "";
      essayQuery.dispatchEvent(new Event("input"));
    }
    if (target.classList.contains("playbook") && target.hidden) {
      guideQuery.value = "";
      guideQuery.dispatchEvent(new Event("input"));
    }
    if (target.classList.contains("card") && target.hidden) {
      // The reset button's id also creates a named form property.
      HTMLFormElement.prototype.reset.call(form);
      cards.forEach(card => { card.hidden = false; });
    }
    let ancestor = target;
    while (ancestor) {
      if (ancestor.tagName === "DETAILS") ancestor.open = true;
      ancestor = ancestor.parentElement;
    }
    target.scrollIntoView({block: "start"});
  }
  document.getElementById("random").addEventListener("click", () => {
    const options = visible();
    if (!options.length) return;
    const card = options[Math.floor(Math.random() * options.length)];
    card.open = true;
    location.hash = card.id;
    card.querySelector("summary").focus();
    status.textContent = `这次试试 ${card.dataset.id}？不想做可以换，也可以不做。`;
  });
  window.addEventListener("hashchange", openHash);
  let printOpenState = [];
  window.addEventListener("beforeprint", () => {
    printOpenState = [...document.querySelectorAll("details")].map(item => [item, item.open]);
    printOpenState.forEach(([item]) => { item.open = true; });
  });
  window.addEventListener("afterprint", () => {
    printOpenState.forEach(([item, wasOpen]) => { item.open = wasOpen; });
  });
  document.addEventListener("click", event => {
    const anchor = event.target.closest("a[href^='#']");
    if (anchor && anchor.hash === location.hash) openHash();
  });
  filter();
  openHash();
})();
