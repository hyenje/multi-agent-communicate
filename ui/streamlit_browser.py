from __future__ import annotations

import streamlit.components.v1 as components


def scroll_chat_to_bottom(smooth: bool = True) -> None:
    behavior = "smooth" if smooth else "auto"
    components.html(
        """
<script>
const root = window.parent.document;
const anchor = root.getElementById("pg-chat-bottom");
if (anchor) {
  anchor.scrollIntoView({ block: "end", behavior: "__PG_SCROLL_BEHAVIOR__" });
}
</script>
""".replace("__PG_SCROLL_BEHAVIOR__", behavior),
        height=0,
        width=0,
    )

def install_composer_autosize() -> None:
    components.html(
        """
<script>
(function () {
  const root = window.parent.document;
  const minHeight = 41;
  const maxHeight = 132;
  const layoutVersion = "chat-column-v2";

  function composerTextareas() {
    return root.querySelectorAll(
      'div[data-testid="stForm"]:has(.pg-empty-composer-anchor) textarea, ' +
      'div[data-testid="stForm"]:has(.pg-docked-composer-anchor) textarea'
    );
  }

  function composerForms() {
    return root.querySelectorAll(
      'div[data-testid="stForm"]:has(.pg-empty-composer-anchor), ' +
      'div[data-testid="stForm"]:has(.pg-docked-composer-anchor)'
    );
  }

  function updateLayoutVars() {
    const sidebar = root.querySelector('section[data-testid="stSidebar"]');
    const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;
    const sidebarWidth = sidebarRect && sidebarRect.width > 48 ? Math.round(sidebarRect.width) : 0;
    root.documentElement.style.setProperty("--pg-sidebar-live-width", sidebarWidth + "px");

    const chatAnchor = Array.from(
      root.querySelectorAll(
        ".pg-chat-shell:not(.pg-activity-shell), " +
        ".pg-agent-group-details, " +
        ".pg-empty-state"
      )
    ).find(function (node) {
      const rect = node.getBoundingClientRect();
      return rect.width > 240 && rect.height > 0;
    });
    if (chatAnchor) {
      const rect = chatAnchor.getBoundingClientRect();
      const width = Math.min(780, Math.max(280, Math.round(rect.width)));
      root.documentElement.style.setProperty("--pg-chat-live-left", Math.round(rect.left + rect.width / 2) + "px");
      root.documentElement.style.setProperty("--pg-chat-live-width", width + "px");
    } else {
      const main = root.querySelector('div[data-testid="stAppViewContainer"] .main');
      const rect = main ? main.getBoundingClientRect() : { left: 0, width: window.parent.innerWidth };
      const width = Math.min(780, Math.max(280, Math.round(rect.width - 32)));
      root.documentElement.style.setProperty("--pg-chat-live-left", Math.round(rect.left + rect.width / 2) + "px");
      root.documentElement.style.setProperty("--pg-chat-live-width", width + "px");
    }

    const dockedForm = root.querySelector('div[data-testid="stForm"]:has(.pg-docked-composer-anchor)');
    if (!dockedForm) {
      root.documentElement.style.setProperty("--pg-composer-safe-space", "6rem");
      return;
    }
    const rect = dockedForm.getBoundingClientRect();
    const bottomGap = Math.max(0, window.parent.innerHeight - rect.bottom);
    const safeSpace = Math.max(82, Math.ceil(rect.height + bottomGap + 16));
    root.documentElement.style.setProperty("--pg-composer-safe-space", safeSpace + "px");
  }

  function hideFocusedSubmitHint() {
    composerForms().forEach(function (form) {
      form.querySelectorAll("div, span, small, p").forEach(function (node) {
        const text = (node.textContent || "").replace(/\\s+/g, " ").trim();
        if (/^Press\\s+(?:⌘|Cmd|Command|Ctrl|Control)\\s*\\+?\\s*Enter\\s+to\\s+submit\\s+form$/i.test(text)) {
          node.style.setProperty("display", "none", "important");
        }
      });
    });
  }

  function setStyleIfChanged(node, property, value) {
    if (
      node.style.getPropertyValue(property) === value &&
      node.style.getPropertyPriority(property) === "important"
    ) {
      return;
    }
    node.style.setProperty(property, value, "important");
  }

  function resize(textarea) {
    setStyleIfChanged(textarea, "height", minHeight + "px");
    const nextHeight = Math.min(maxHeight, Math.max(minHeight, textarea.scrollHeight));
    setStyleIfChanged(textarea, "height", nextHeight + "px");
    setStyleIfChanged(
      textarea,
      "overflow-y",
      textarea.scrollHeight > maxHeight ? "auto" : "hidden"
    );
    setStyleIfChanged(textarea, "overflow-x", "hidden");
  }

  function wire(textarea) {
    if (textarea.dataset.pgComposerAutosize !== "1") {
      textarea.dataset.pgComposerAutosize = "1";
      textarea.addEventListener("input", function () {
        resize(textarea);
      });
      textarea.addEventListener("focus", function () {
        window.setTimeout(hideFocusedSubmitHint, 0);
        window.setTimeout(hideFocusedSubmitHint, 80);
      });
      textarea.addEventListener("keydown", function (event) {
        if (
          event.key !== "Enter" ||
          event.shiftKey ||
          event.isComposing ||
          event.keyCode === 229
        ) {
          return;
        }

        const form = textarea.closest('div[data-testid="stForm"]');
        const submitButton = form && form.querySelector('div[data-testid="stFormSubmitButton"] button');
        if (!submitButton || submitButton.disabled) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        submitButton.click();
      });
    }
    resize(textarea);
  }

  function resizeAll() {
    composerTextareas().forEach(wire);
    hideFocusedSubmitHint();
    updateLayoutVars();
  }

  function scheduleLayoutRefresh() {
    updateLayoutVars();
    window.setTimeout(updateLayoutVars, 120);
    window.setTimeout(updateLayoutVars, 360);
    window.setTimeout(updateLayoutVars, 800);
  }

  if (!window.parent.__pgComposerAutosizeInstalled) {
    window.parent.__pgComposerAutosizeInstalled = true;
    window.parent.addEventListener("resize", resizeAll);
    const observer = new MutationObserver(resizeAll);
    observer.observe(root.body, { childList: true, subtree: true });
  }
  if (window.parent.__pgComposerLayoutInterval) {
    window.parent.clearInterval(window.parent.__pgComposerLayoutInterval);
  }
  if (window.parent.__pgComposerLayoutClickListener) {
    root.removeEventListener("click", window.parent.__pgComposerLayoutClickListener, true);
  }
  window.parent.__pgComposerLayoutInterval = window.parent.setInterval(updateLayoutVars, 400);
  window.parent.__pgComposerLayoutClickListener = scheduleLayoutRefresh;
  window.parent.__pgComposerLayoutIntervalVersion = layoutVersion;
  root.addEventListener("click", scheduleLayoutRefresh, true);

  window.setTimeout(resizeAll, 0);
  window.setTimeout(resizeAll, 120);
  window.setTimeout(scheduleLayoutRefresh, 320);
})();
</script>
""",
        height=0,
        width=0,
    )

def install_config_start_hide() -> None:
    components.html(
        """
<script>
(function () {
  const root = window.parent.document;

  function configMessages() {
    return root.querySelectorAll('div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor)');
  }

  function hideConfigMessages() {
    configMessages().forEach(function (message) {
      message.style.setProperty("display", "none", "important");
    });
  }

  function wireStartButtons() {
    configMessages().forEach(function (message) {
      message.querySelectorAll('button').forEach(function (button) {
        const label = (button.textContent || "").trim();
        if (!label.includes("시작하기") && !label.includes("이 설정으로 시작")) {
          return;
        }
        if (button.dataset.pgConfigStartHide === "1") {
          return;
        }
        button.dataset.pgConfigStartHide = "1";
        button.addEventListener("click", function () {
          window.parent.__pgConfigStartInFlight = true;
          hideConfigMessages();
          window.parent.setTimeout(hideConfigMessages, 0);
          window.parent.setTimeout(hideConfigMessages, 120);
          window.parent.setTimeout(function () {
            window.parent.__pgConfigStartInFlight = false;
          }, 5000);
        });
      });
    });
    if (window.parent.__pgConfigStartInFlight) {
      hideConfigMessages();
    }
  }

  if (!window.parent.__pgConfigStartHideInstalled) {
    window.parent.__pgConfigStartHideInstalled = true;
    const observer = new MutationObserver(wireStartButtons);
    observer.observe(root.body, { childList: true, subtree: true });
  }

  wireStartButtons();
})();
</script>
""",
        height=0,
        width=0,
    )
