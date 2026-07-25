(function () {
  'use strict';
  var DICT = __ZHTW_DICT__;
  var RULES = [
    [/^Showing (\d+)\s*(?:to|-|–)\s*(\d+) of (\d+)(?: results?)?$/, '顯示第 $1 至 $2 筆,共 $3 筆'],
    [/^Total (\d+) items?$/, '共 $1 筆'],
    [/^Page (\d+) of (\d+)$/, '第 $1 頁,共 $2 頁'],
    [/^(\d+) \/ page$/, '$1 筆/頁'],
    [/^Showing (\d+) of (\d+) results?$/, '顯示 $1 筆,共 $2 筆'],
    [/^(\d+) selected$/, '已選 $1 筆'],
    [/^Copied!?$/, '已複製'],
    [/^(\d+) models?$/, '$1 個模型'],
    [/^(\d+) members?$/, '$1 位成員'],
    [/^(\d+) keys?$/, '$1 把金鑰'],
    [/^(\d+) rows?$/, '$1 列'],
    [/^(\d+) results?$/, '$1 筆結果'],
    [/^(\d+) teams?$/, '$1 個團隊'],
    [/^(\d+) users?$/, '$1 位使用者'],
    [/^(\d+) organizations?$/, '$1 個組織'],
    [/^(\d+) items?$/, '$1 筆']
  ];
  var ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1, PRE: 1, KBD: 1, SAMP: 1 };

  function tr(raw) {
    if (!raw) return null;
    var key = raw.replace(/\s+/g, ' ').trim();
    if (!key || key.length > 300) return null;
    var hit = DICT[key];
    if (hit !== undefined) return hit;
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i][0].test(key)) return key.replace(RULES[i][0], RULES[i][1]);
    }
    return null;
  }

  function processText(node) {
    var p = node.parentElement;
    if (p && (SKIP_TAGS[p.tagName] || p.isContentEditable)) return;
    var v = tr(node.nodeValue);
    if (v != null && v !== node.nodeValue) node.nodeValue = v;
  }

  function processElement(el) {
    if (SKIP_TAGS[el.tagName]) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i];
      if (el.hasAttribute && el.hasAttribute(a)) {
        var val = el.getAttribute(a);
        var v = tr(val);
        if (v != null && v !== val) el.setAttribute(a, v);
      }
    }
    if (el.tagName === 'INPUT' && (el.type === 'submit' || el.type === 'button') && el.value) {
      var v2 = tr(el.value);
      if (v2 != null && v2 !== el.value) el.value = v2;
    }
  }

  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { processText(root); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1) {
      if (SKIP_TAGS[root.tagName] || root.isContentEditable) return;
      processElement(root);
    }
    var w = document.createTreeWalker(root, 5, {
      acceptNode: function (n) {
        if (n.nodeType === 1) {
          return (SKIP_TAGS[n.tagName] || n.isContentEditable) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = w.nextNode())) {
      if (n.nodeType === 3) processText(n); else processElement(n);
    }
  }

  var mo = new MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      var m = muts[i];
      if (m.type === 'characterData') {
        processText(m.target);
      } else if (m.type === 'attributes') {
        if (m.target.nodeType === 1) processElement(m.target);
      } else {
        for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
      }
    }
  });

  function start() {
    walk(document.documentElement);
    var t = tr(document.title);
    if (t) document.title = t;
    mo.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRS
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
