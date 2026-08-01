(function () {
  'use strict';
  var DICT = __I18N_DICT__;
  var HTML_LANG = __I18N_HTML_LANG__;
  var RULES = [
    [/^Showing (\d+)\s*(?:to|-|–)\s*(\d+) of (\d+)(?: results?)?$/, 'Showing $1 to $2 of $3'],
    [/^Total (\d+) items?$/, 'Total $1 items'],
    [/^Page (\d+) of (\d+)$/, 'Page $1 of $2'],
    [/^(\d+) \/ page$/, '$1 / page'],
    [/^Showing (\d+) of (\d+) results?$/, 'Showing $1 of $2 results'],
    [/^(\d+) selected$/, '$1 selected'],
    [/^(\d+) models?$/, '$1 models'],
    [/^(\d+) members?$/, '$1 members'],
    [/^(\d+) keys?$/, '$1 keys'],
    [/^(\d+) rows?$/, '$1 rows'],
    [/^(\d+) results?$/, '$1 results'],
    [/^(\d+) teams?$/, '$1 teams'],
    [/^(\d+) users?$/, '$1 users'],
    [/^(\d+) organizations?$/, '$1 organizations'],
    [/^(\d+) items?$/, '$1 items']
  ];
  var ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1, PRE: 1, KBD: 1, SAMP: 1 };

  function lookup(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key) ? DICT[key] : undefined;
  }

  function tr(raw) {
    if (!raw) return null;
    var normalized = raw.replace(/\s+/g, ' ');
    var key = normalized.trim();
    if (!key || key.length > 300) return null;
    var hit = lookup(key);
    if (hit === undefined && normalized !== key) hit = lookup(normalized);
    if (hit !== undefined) return hit;
    if (HTML_LANG === 'en') return null;
    for (var i = 0; i < RULES.length; i++) {
      var match = key.match(RULES[i][0]);
      if (!match) continue;
      var template = lookup(RULES[i][1]);
      if (template === undefined) return null;
      return template.replace(/\$(\d+)/g, function (token, index) {
        return match[Number(index)] !== undefined ? match[Number(index)] : token;
      });
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
    document.documentElement.setAttribute('lang', HTML_LANG);
    if (HTML_LANG === 'en') return;
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
