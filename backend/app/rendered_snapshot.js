(budgetMs) => {
  const started = performance.now();
  const check = () => {
    if (performance.now() - started > budgetMs) throw new Error('Rendered style snapshot time budget exceeded');
  };
  const paths = new WeakMap();
  function path(element) {
    if (paths.has(element)) return paths.get(element);
    check();
    let position = 1;
    for (let sibling = element.previousElementSibling; sibling; sibling = sibling.previousElementSibling) {
      check();
      if (sibling.localName === element.localName) position++;
    }
    const part = CSS.escape(element.localName) + ':nth-of-type(' + position + ')';
    const result = element.parentElement ? path(element.parentElement) + ' > ' + part : part;
    paths.set(element, result);
    return result;
  }
  const observations = [];
  for (const element of document.querySelectorAll('*')) {
    check();
    if (!(element instanceof HTMLElement) || element.closest('head,script,style,template,noscript')) continue;
    const sourceText = Array.from(element.childNodes).filter(node => node.nodeType === Node.TEXT_NODE)
      .map(node => node.nodeValue).join('');
    if (!sourceText.trim()) continue;
    const style = getComputedStyle(element);
    let hiddenDisplay = false, zeroOpacity = false, background = null, backgroundUnknown = false;
    for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
      check();
      const parentStyle = getComputedStyle(ancestor);
      hiddenDisplay ||= parentStyle.display === 'none';
      zeroOpacity ||= Number(parentStyle.opacity) === 0;
      if (background === null && !backgroundUnknown) {
        const color = parentStyle.backgroundColor;
        if (parentStyle.backgroundImage !== 'none') backgroundUnknown = true;
        else if (color !== 'transparent' && !/^rgba\([\d.]+,\s*[\d.]+,\s*[\d.]+,\s*0(?:\.0*)?\)$/.test(color)) {
          // Python accepts only an opaque, simple RGB color; no blending guess.
          background = color;
        }
      }
    }
    const rect = element.getBoundingClientRect();
    observations.push({
      selector: path(element), source_text: sourceText,
      display_none: hiddenDisplay, zero_opacity: zeroOpacity,
      visibility: style.visibility, color: style.webkitTextFillColor || style.color,
      text_effects: style.textShadow !== 'none' || parseFloat(style.webkitTextStrokeWidth || '0') > 0,
      background: backgroundUnknown ? null : background, font_size: style.fontSize,
      rect: {left: rect.left + scrollX, top: rect.top + scrollY,
             right: rect.right + scrollX, bottom: rect.bottom + scrollY,
             width: rect.width, height: rect.height}
    });
  }
  check();
  return {
    html: (document.doctype ? '<!DOCTYPE ' + document.doctype.name + '>' : '') + document.documentElement.outerHTML,
    rendered_style: {schema_version: 1, observations}
  };
}
