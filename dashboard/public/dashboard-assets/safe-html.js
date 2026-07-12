(() => {
  const allowedTags = new Set(['DIV', 'I', 'P', 'SPAN', 'TD', 'TR'])
  const allowedAttributes = new Set(['class', 'colspan', 'data-lucide'])
  const entities = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

  window.escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => entities[char])
  window.safeTemplate = (strings, ...values) => strings.reduce(
    (result, part, index) => result + part + (index < values.length ? window.escapeHtml(values[index]) : ''),
    '',
  )

  window.setSafeHtml = (target, html) => {
    const range = document.createRange()
    range.selectNodeContents(target)
    const fragment = range.createContextualFragment(String(html))

    for (const element of [...fragment.querySelectorAll('*')]) {
      if (!allowedTags.has(element.tagName)) {
        element.replaceWith(document.createTextNode(element.textContent || ''))
        continue
      }
      for (const attribute of [...element.attributes]) {
        if (!allowedAttributes.has(attribute.name)) {
          element.removeAttribute(attribute.name)
        }
      }
    }

    target.replaceChildren(fragment)
  }
})()
