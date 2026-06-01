from __future__ import annotations

import streamlit as st


def render_chat_styles() -> None:
    st.markdown(
        """
<style>
:root {
  --pg-bg-app: #212121;
  --pg-bg-sidebar: #171717;
  --pg-bg-main: #212121;
  --pg-bg-surface: #2f2f2f;
  --pg-bg-surface-muted: #343434;
  --pg-bg-surface-subtle: #262626;
  --pg-bg-input: #303030;
  --pg-bg-user: #303030;
  --pg-bg-agent: #242424;
  --pg-bg-system: #262626;
  --pg-text-primary: #f2f2f2;
  --pg-text-secondary: #d6d6d6;
  --pg-text-muted: #a6a6a6;
  --pg-text-inverse: #111111;
  --pg-border-default: rgba(255, 255, 255, 0.10);
  --pg-border-strong: rgba(255, 255, 255, 0.18);
  --pg-accent: #8ab4f8;
  --pg-accent-soft: rgba(138, 180, 248, 0.14);
  --pg-danger: #f87171;
  --pg-success: #86efac;
  --pg-persona-nori-border: #f59e0b;
  --pg-persona-nori-soft: rgba(245, 158, 11, 0.12);
  --pg-persona-orbit-border: #8ea3ff;
  --pg-persona-orbit-soft: rgba(142, 163, 255, 0.12);
  --pg-persona-milmil-border: #d6a45f;
  --pg-persona-milmil-soft: rgba(214, 164, 95, 0.12);
  --pg-persona-sori-border: #f08a9a;
  --pg-persona-sori-soft: rgba(240, 138, 154, 0.12);
  --pg-persona-mori-border: #a8a29e;
  --pg-persona-mori-soft: rgba(168, 162, 158, 0.12);
  --pg-persona-gyeol-border: #b89cff;
  --pg-persona-gyeol-soft: rgba(184, 156, 255, 0.12);
  --pg-persona-jari-border: #67d7a5;
  --pg-persona-jari-soft: rgba(103, 215, 165, 0.12);
  --pg-persona-sallycore-border: #8ab4f8;
  --pg-persona-sallycore-soft: rgba(138, 180, 248, 0.12);
  --pg-persona-lumi-border: #6fd0df;
  --pg-persona-lumi-soft: rgba(111, 208, 223, 0.12);
  --pg-persona-haneul-border: #c99cff;
  --pg-persona-haneul-soft: rgba(201, 156, 255, 0.12);
  --pg-radius-sm: 6px;
  --pg-radius-md: 10px;
  --pg-radius-lg: 16px;
  --pg-radius-xl: 20px;
  --pg-radius-full: 999px;
  --pg-chat-max-width: 780px;
  --pg-composer-max-width: 780px;
  --pg-composer-safe-space: 6rem;
  --pg-chat-live-left: 50vw;
  --pg-chat-live-width: min(var(--pg-chat-max-width), calc(100vw - 2rem));
  --pg-sidebar-width: 16.25rem;
  --pg-sidebar-live-width: var(--pg-sidebar-width);
}

html,
body,
.stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > .main {
  background: var(--pg-bg-main) !important;
  color: var(--pg-text-primary) !important;
  overflow-x: hidden;
}

header[data-testid="stHeader"],
div[data-testid="stHeader"] {
  background: transparent !important;
}

div[data-testid="stStatusWidget"],
div[data-testid="stDecoration"],
.stDeployButton,
#MainMenu,
footer {
  display: none !important;
  visibility: hidden !important;
}

div[data-testid="stToolbar"] {
  background: transparent !important;
}

div[data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) {
  display: none !important;
  visibility: hidden !important;
}

button[data-testid="stExpandSidebarButton"],
button[data-testid="stExpandSidebarButton"] * {
  visibility: visible !important;
}

.block-container,
div[data-testid="stAppViewContainer"] .main .block-container,
div[data-testid="stMainBlockContainer"] {
  max-width: none;
  width: 100%;
  min-height: 100vh;
  padding: 0 !important;
  padding-bottom: var(--pg-composer-safe-space) !important;
}

section[data-testid="stSidebar"] {
  position: relative;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  background: var(--pg-bg-sidebar) !important;
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, 0.36);
}

section[data-testid="stSidebar"] > div:first-child > div:first-child {
  display: flex !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
  visibility: visible !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  background: var(--pg-bg-sidebar) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  min-height: 100vh;
  padding: 1.05rem 0.72rem 5.8rem 0.72rem;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
  color: var(--pg-text-primary) !important;
}

div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
  min-height: 2.35rem;
  border: 1px solid var(--pg-border-default) !important;
  border-radius: var(--pg-radius-md) !important;
  background: var(--pg-bg-surface) !important;
  color: var(--pg-text-primary) !important;
  box-shadow: none !important;
  font-weight: 650 !important;
}

div[data-testid="stButton"] > button p,
div[data-testid="stFormSubmitButton"] > button p {
  color: inherit !important;
  margin: 0;
}

div[data-testid="stButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--pg-border-strong) !important;
  background: var(--pg-bg-surface-muted) !important;
  color: var(--pg-text-primary) !important;
}

div[data-testid="stButton"] > button:focus,
div[data-testid="stFormSubmitButton"] > button:focus {
  border-color: var(--pg-border-strong) !important;
  box-shadow: 0 0 0 1px var(--pg-border-strong) !important;
}

div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid="baseButton-primary"],
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"],
div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primaryFormSubmit"] {
  border-color: var(--pg-text-primary) !important;
  background: var(--pg-text-primary) !important;
  color: var(--pg-text-inverse) !important;
}

div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stButton"] > button[data-testid="baseButton-primary"]:hover,
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover,
div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primaryFormSubmit"]:hover {
  border-color: #ffffff !important;
  background: #ffffff !important;
  color: var(--pg-text-inverse) !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
  justify-content: flex-start;
  min-height: 2.25rem;
  border-color: transparent !important;
  background: transparent !important;
  padding: 0.42rem 0.65rem;
  text-align: left;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
  border-color: transparent !important;
  background: var(--pg-bg-surface-muted) !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.35;
  text-align: left;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
  border: 1px solid var(--pg-border-default) !important;
  border-radius: var(--pg-radius-lg) !important;
  background: var(--pg-bg-input) !important;
  color: var(--pg-text-primary) !important;
  box-shadow: none !important;
}

div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
  border-color: var(--pg-border-strong) !important;
  box-shadow: 0 0 0 1px var(--pg-border-strong) !important;
}

div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stTextInput"] input::placeholder {
  color: var(--pg-text-muted) !important;
  opacity: 1;
}

div[data-testid="stSlider"] label,
div[data-testid="stToggle"] label,
div[data-testid="stRadio"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stExpander"] summary {
  color: var(--pg-text-primary) !important;
}

div[data-testid="stCaptionContainer"],
div[data-testid="stMarkdownContainer"] {
  color: var(--pg-text-secondary);
}

details[data-testid="stExpander"] {
  border-color: var(--pg-border-default) !important;
  background: var(--pg-bg-surface-subtle) !important;
  border-radius: var(--pg-radius-md) !important;
}

details[data-testid="stExpander"]:has(.pg-agent-group-content-anchor) {
  max-width: var(--pg-chat-max-width);
  margin: 0 auto 1rem auto;
  border-color: var(--pg-border-default) !important;
  background: var(--pg-bg-system) !important;
}

details[data-testid="stExpander"]:has(.pg-agent-group-content-anchor) summary {
  min-height: 2.9rem;
  color: var(--pg-text-primary) !important;
  font-size: 0.9rem;
  font-weight: 750;
}

details[data-testid="stExpander"]:has(.pg-agent-group-content-anchor) summary:hover {
  background: var(--pg-bg-surface-muted) !important;
}

.pg-agent-group-details {
  max-width: var(--pg-chat-max-width);
  margin: 0 auto 1rem auto;
  border: 1px solid var(--pg-border-default);
  border-radius: var(--pg-radius-md);
  background: var(--pg-bg-system);
  overflow: hidden;
}

.pg-agent-group-details summary {
  display: flex;
  align-items: center;
  min-height: 2.9rem;
  padding: 0.55rem 0.85rem;
  color: var(--pg-text-primary);
  font-size: 0.9rem;
  font-weight: 750;
  line-height: 1.35;
  cursor: pointer;
}

.pg-agent-group-details summary:hover {
  background: var(--pg-bg-surface-muted);
}

.pg-agent-group-content {
  padding: 0.2rem 0.85rem 0.75rem;
}

.pg-agent-group-content-anchor {
  display: none;
}

.pg-agent-group-message {
  display: flex;
  gap: 0.65rem;
  width: 100%;
  padding: 0.2rem 0 0.85rem;
}

.pg-agent-group-message:last-child {
  padding-bottom: 0.1rem;
}

.pg-agent-group-body {
  flex: 1 1 auto;
  max-width: none;
  border-radius: var(--pg-radius-md);
  padding: 0.68rem 0.78rem;
  font-size: 0.92rem;
  line-height: 1.52;
  color: var(--pg-text-primary);
  word-break: keep-all;
  overflow-wrap: anywhere;
}

div[data-testid="stDialog"] div[role="dialog"] {
  border: 1px solid var(--pg-border-default) !important;
  background: var(--pg-bg-surface-subtle) !important;
  color: var(--pg-text-primary) !important;
}

.pg-sidebar-brand {
  color: var(--pg-text-primary);
  font-size: 1rem;
  font-weight: 750;
  line-height: 1.2;
  padding: 0.1rem 0 1.05rem 0.25rem;
}

.pg-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  margin-bottom: 0.45rem;
}

.pg-sidebar-header div[data-testid="stButton"] > button {
  width: 2rem !important;
  min-width: 2rem !important;
  height: 2rem !important;
  min-height: 2rem !important;
  justify-content: center !important;
  border-radius: var(--pg-radius-md) !important;
  padding: 0 !important;
}

.pg-sidebar-history {
  display: flex;
  flex-direction: column;
  gap: 0.08rem;
  padding-bottom: 1rem;
}

.pg-sidebar-run {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border: 1px solid transparent;
  border-radius: var(--pg-radius-sm);
  background: rgba(255, 255, 255, 0.06);
  padding: 0.52rem 0.55rem;
  margin: 0.04rem 0;
}

.pg-sidebar-run-title {
  color: var(--pg-text-primary);
  font-size: 0.86rem;
  font-weight: 700;
  line-height: 1.3;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pg-sidebar-run:hover {
  background: var(--pg-bg-surface-muted);
}

.pg-sidebar-active-dot {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: var(--pg-radius-full);
  background: var(--pg-accent);
  flex: 0 0 auto;
}

.pg-top-actions-spacer {
  height: 0.15rem;
}

.pg-main-topbar {
  height: 0.65rem;
}

.pg-status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 1.7rem;
  border: 1px solid var(--pg-border-default);
  border-radius: var(--pg-radius-full);
  padding: 0.15rem 0.65rem;
  background: var(--pg-bg-surface-muted);
  color: var(--pg-text-muted);
  font-size: 0.78rem;
  font-weight: 650;
  white-space: nowrap;
}

.pg-chat-shell {
  max-width: var(--pg-chat-max-width);
  margin: 0 auto 1rem auto;
}

.pg-empty-state {
  min-height: 41vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  text-align: center;
  padding: 0 clamp(1rem, 4vw, 3rem) 0.9rem;
}

.pg-empty-title {
  color: var(--pg-text-primary);
  font-size: clamp(1.38rem, 2vw, 1.7rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0;
}

.pg-empty-subtitle {
  color: var(--pg-text-muted);
  font-size: 0.94rem;
  line-height: 1.45;
  max-width: 34rem;
  margin-top: 0.68rem;
}

.pg-chat-thread {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.35rem 0 1rem 0;
}

.pg-chat-row {
  display: flex;
  width: 100%;
  gap: 0.65rem;
}

.pg-chat-row-user {
  justify-content: flex-end;
}

.pg-chat-row-agent,
.pg-chat-row-system {
  justify-content: flex-start;
}

.pg-chat-avatar-wrap {
  width: 2.3rem;
  min-width: 2.3rem;
  padding-top: 0.1rem;
}

.pg-chat-avatar-img {
  width: 2.25rem;
  height: 2.8rem;
  border-radius: 9px;
  object-fit: contain;
  background: var(--pg-bg-surface-muted);
  border: 1px solid var(--pg-border-default);
}

.pg-chat-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: var(--pg-radius-full);
  background: var(--pg-bg-surface-muted);
  color: var(--pg-text-secondary);
  font-size: 0.74rem;
  font-weight: 800;
}

.pg-chat-bubble {
  max-width: 72%;
  border-radius: var(--pg-radius-lg);
  padding: 0.72rem 0.86rem;
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--pg-text-primary);
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.pg-chat-bubble-user {
  background: var(--pg-bg-user);
  border: 0;
  border-radius: 1.45rem;
  padding: 0.7rem 0.96rem;
  font-size: 0.98rem;
  line-height: 1.55;
  font-weight: 400;
}

.pg-chat-bubble-agent {
  --pg-persona-border: var(--pg-border-default);
  --pg-persona-soft: var(--pg-bg-agent);
  background: linear-gradient(90deg, var(--pg-persona-soft), var(--pg-bg-agent) 32%);
  border: 1px solid var(--pg-border-default);
  border-left: 3px solid var(--pg-persona-border);
}

.pg-chat-bubble-system {
  background: var(--pg-bg-system);
  border: 1px solid var(--pg-border-default);
}

.pg-moderator-preview {
  color: var(--pg-text-primary);
}

.pg-moderator-full {
  margin-top: 0.58rem;
  border-top: 1px solid var(--pg-border-default);
  padding-top: 0.42rem;
}

.pg-moderator-full summary {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--pg-text-muted);
  font-size: 0.78rem;
  font-weight: 750;
  line-height: 1.35;
  cursor: pointer;
  list-style: none;
}

.pg-moderator-full summary::-webkit-details-marker {
  display: none;
}

.pg-moderator-full summary::after {
  content: "v";
  color: var(--pg-text-muted);
  font-size: 0.8rem;
}

.pg-moderator-full[open] summary::after {
  content: "^";
}

.pg-moderator-full summary:hover {
  color: var(--pg-text-primary);
}

.pg-moderator-full-body {
  margin-top: 0.45rem;
  color: var(--pg-text-secondary);
  font-size: 0.9rem;
  line-height: 1.55;
}

.pg-chat-bubble-agent:hover {
  border-color: var(--pg-persona-border);
}

.pg-message-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.28rem;
  color: var(--pg-text-muted);
  font-size: 0.76rem;
  line-height: 1.35;
}

.pg-message-name {
  color: var(--pg-text-primary);
  font-weight: 750;
}

.pg-message-content {
  margin: 0;
}

.pg-final-answer-only {
  width: min(var(--pg-chat-max-width), calc(100% - 2rem));
  margin: 0 auto 1.05rem auto;
  color: var(--pg-text-primary);
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.75;
  letter-spacing: 0;
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.pg-final-answer-only strong,
.pg-chat-bubble-user strong {
  font-weight: 520;
}

div[data-testid="stExpander"]:has(.pg-work-history-anchor) {
  width: min(var(--pg-chat-max-width), calc(100% - 2rem));
  margin: 0.25rem auto 1rem auto;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

div[data-testid="stExpander"]:has(.pg-work-history-anchor) details {
  border: 0 !important;
  background: transparent !important;
}

div[data-testid="stExpander"]:has(.pg-work-history-anchor) summary {
  color: var(--pg-text-muted) !important;
  font-size: 0.94rem !important;
  font-weight: 650 !important;
  padding: 0.62rem 0 !important;
  border-top: 1px solid var(--pg-border-default);
}

div[data-testid="stExpander"]:has(.pg-work-history-anchor) summary:hover {
  color: var(--pg-text-primary) !important;
}

.pg-character-nori {
  --pg-persona-border: var(--pg-persona-nori-border);
  --pg-persona-soft: var(--pg-persona-nori-soft);
}
.pg-character-orbit {
  --pg-persona-border: var(--pg-persona-orbit-border);
  --pg-persona-soft: var(--pg-persona-orbit-soft);
}
.pg-character-milmil {
  --pg-persona-border: var(--pg-persona-milmil-border);
  --pg-persona-soft: var(--pg-persona-milmil-soft);
}
.pg-character-sori {
  --pg-persona-border: var(--pg-persona-sori-border);
  --pg-persona-soft: var(--pg-persona-sori-soft);
}
.pg-character-mori {
  --pg-persona-border: var(--pg-persona-mori-border);
  --pg-persona-soft: var(--pg-persona-mori-soft);
}
.pg-character-gyeol {
  --pg-persona-border: var(--pg-persona-gyeol-border);
  --pg-persona-soft: var(--pg-persona-gyeol-soft);
}
.pg-character-jari {
  --pg-persona-border: var(--pg-persona-jari-border);
  --pg-persona-soft: var(--pg-persona-jari-soft);
}
.pg-character-sallycore {
  --pg-persona-border: var(--pg-persona-sallycore-border);
  --pg-persona-soft: var(--pg-persona-sallycore-soft);
}
.pg-character-lumi {
  --pg-persona-border: var(--pg-persona-lumi-border);
  --pg-persona-soft: var(--pg-persona-lumi-soft);
}
.pg-character-haneul {
  --pg-persona-border: var(--pg-persona-haneul-border);
  --pg-persona-soft: var(--pg-persona-haneul-soft);
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) {
  max-width: var(--pg-chat-max-width);
  margin: 0 auto 1rem auto;
  padding: 0 !important;
  background: transparent !important;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) [data-testid="stChatMessageAvatar"],
div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) > div:first-child {
  width: 2.3rem;
  min-width: 2.3rem;
  padding-top: 0.1rem;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) [data-testid="stChatMessageContent"],
div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) > div:last-child {
  width: min(72%, 100%);
  max-width: 72%;
  border: 1px solid var(--pg-border-default);
  border-radius: var(--pg-radius-lg);
  background: var(--pg-bg-system);
  padding: 0.72rem 0.86rem 0.86rem;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) [data-testid="stSlider"] {
  margin: 0.1rem 0 0.9rem;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) [data-testid="stCaptionContainer"] {
  margin-top: -0.35rem;
  margin-bottom: 0.65rem;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) div[data-testid="stButton"] > button {
  color: var(--pg-text-inverse) !important;
}

div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) div[data-testid="stButton"] > button * {
  color: var(--pg-text-inverse) !important;
}

.pg-config-title {
  color: var(--pg-text-primary);
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.35;
  margin-bottom: 0.8rem;
}

.pg-config-meta {
  color: var(--pg-text-muted);
  font-size: 0.84rem;
  line-height: 1.45;
}

.pg-config-control-label {
  color: var(--pg-text-primary);
  font-size: 0.9rem;
  font-weight: 750;
  line-height: 1.35;
  margin-top: 0.25rem;
}

.pg-config-control-description {
  color: var(--pg-text-muted);
  font-size: 0.82rem;
  line-height: 1.45;
  margin: 0.22rem 0 0.35rem;
}

.pg-composer-wrap {
  max-width: var(--pg-composer-max-width);
  margin: 0 auto;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor),
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) {
  position: relative;
  box-sizing: border-box;
  width: min(var(--pg-composer-max-width), calc(100% - 2rem));
  height: fit-content !important;
  min-height: 3.35rem;
  max-height: 9.25rem;
  overflow: visible !important;
  border: 1px solid var(--pg-border-default) !important;
  border-radius: 1.85rem !important;
  background: var(--pg-bg-input) !important;
  box-shadow: 0 18px 52px rgba(0, 0, 0, 0.28) !important;
  padding: 0.42rem 0.48rem 0.42rem 1.2rem !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) {
  max-width: var(--pg-composer-max-width);
  margin: 0 auto;
}

p:has(.pg-empty-composer-anchor),
p:has(.pg-docked-composer-anchor) {
  display: none !important;
  margin: 0 !important;
}

div[data-testid="stElementContainer"]:has(.pg-empty-composer-anchor),
div[data-testid="stElementContainer"]:has(.pg-docked-composer-anchor) {
  display: none !important;
}

div[data-testid="stForm"]:has(.pg-docked-composer-anchor) {
  position: fixed;
  z-index: 50;
  left: var(--pg-chat-live-left);
  transform: translateX(-50%);
  width: min(var(--pg-composer-max-width), var(--pg-chat-live-width), calc(100vw - 2rem));
  bottom: 1.05rem;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) [data-testid="stVerticalBlock"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) [data-testid="stVerticalBlock"] {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 2.3rem;
  grid-auto-rows: min-content !important;
  height: auto !important;
  min-height: 0 !important;
  align-items: end !important;
  align-content: center !important;
  gap: 0.7rem !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextArea"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextArea"],
div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextInput"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextInput"] {
  min-width: 0 !important;
  margin: 0 !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextArea"] > div,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextArea"] > div,
div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextInput"] > div,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextInput"] > div,
div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-baseweb="textarea"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-baseweb="textarea"],
div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-baseweb="input"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-baseweb="input"] {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextArea"] *,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextArea"] *,
div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextInput"] *,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextInput"] * {
  border-color: transparent !important;
  background: transparent !important;
  box-shadow: none !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextArea"] textarea,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextArea"] textarea {
  width: 100% !important;
  max-width: 100% !important;
  min-height: 2.35rem !important;
  height: 2.55rem !important;
  max-height: 8.25rem !important;
  resize: none !important;
  overflow-y: hidden !important;
  overflow-x: hidden !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 0.52rem 0.25rem 0.4rem !important;
  box-shadow: none !important;
  color: var(--pg-text-primary) !important;
  line-height: 1.35 !important;
  white-space: pre-wrap !important;
  overflow-wrap: anywhere !important;
  word-break: break-word !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextArea"] textarea::placeholder,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextArea"] textarea::placeholder {
  color: var(--pg-text-muted) !important;
  opacity: 1;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextInput"] input,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextInput"] input {
  height: 2.35rem !important;
  min-height: 2.35rem !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 0.2rem 0.25rem !important;
  box-shadow: none !important;
  color: var(--pg-text-primary) !important;
  line-height: 1.35 !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stTextInput"] input::placeholder {
  color: var(--pg-text-muted) !important;
  opacity: 1;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] {
  width: 2.1rem !important;
  height: 2.1rem !important;
  margin: 0 !important;
  padding: 0 !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"] button,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] button {
  position: static !important;
  transform: none !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] > button {
  width: 2.1rem !important;
  min-width: 2.1rem !important;
  height: 2.1rem !important;
  min-height: 2.1rem !important;
  border-radius: var(--pg-radius-full) !important;
  border-color: #f1f1f1 !important;
  background: #f1f1f1 !important;
  color: var(--pg-text-inverse) !important;
  justify-content: center !important;
  gap: 0 !important;
  padding: 0 !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"] > button div[data-testid="stMarkdownContainer"],
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] > button div[data-testid="stMarkdownContainer"] {
  display: none !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"] > button span,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] > button span {
  margin-right: 0 !important;
}

div[data-testid="stForm"]:has(.pg-empty-composer-anchor) div[data-testid="stFormSubmitButton"] > button p,
div[data-testid="stForm"]:has(.pg-docked-composer-anchor) div[data-testid="stFormSubmitButton"] > button p {
  display: none !important;
}

div[data-testid="stBottom"],
div[data-testid="stBottomBlockContainer"] {
  background: transparent !important;
}

.pg-sidebar-title {
  color: var(--pg-text-primary);
  font-size: 0.82rem;
  font-weight: 800;
  margin: 1.05rem 0 0.45rem 0.25rem;
}

.pg-sidebar-empty {
  color: var(--pg-text-muted);
  font-size: 0.82rem;
  line-height: 1.45;
  margin-top: 0.4rem;
}

.pg-sidebar-profile {
  position: absolute;
  left: 0.75rem;
  bottom: 0.75rem;
  width: calc(var(--pg-sidebar-width) - 1.5rem);
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border-top: 1px solid rgba(255, 255, 255, 0.10);
  background: var(--pg-bg-sidebar);
  padding: 0.78rem 0.18rem 0.1rem;
}

.pg-sidebar-profile-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.8rem;
  height: 1.8rem;
  border-radius: var(--pg-radius-full);
  background: #1f80e0;
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 800;
}

.pg-sidebar-profile-name {
  color: var(--pg-text-primary);
  font-size: 0.82rem;
  font-weight: 750;
  line-height: 1.2;
}

.pg-sidebar-profile-plan {
  color: var(--pg-text-muted);
  font-size: 0.78rem;
  line-height: 1.2;
}

.pg-active-status {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  max-width: 72%;
  border: 1px dashed var(--pg-border-strong);
  border-radius: var(--pg-radius-lg);
  background: var(--pg-bg-system);
  padding: 0.68rem 0.78rem;
  color: var(--pg-text-secondary);
  font-size: 0.9rem;
  line-height: 1.45;
}

.pg-chat-shell.pg-activity-shell {
  margin: 0.1rem auto 0.55rem auto;
}

.pg-activity-row {
  width: calc(100% - 3.45rem);
  margin-left: 3.45rem;
}

.pg-work-activity {
  display: inline-block;
  max-width: 100%;
  color: var(--pg-text-muted);
  font-size: 0.88rem;
  line-height: 1.45;
}

.pg-work-activity summary {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  cursor: pointer;
  list-style: none;
  color: var(--pg-text-muted);
  font-weight: 700;
  user-select: none;
}

.pg-work-activity summary::-webkit-details-marker {
  display: none;
}

.pg-work-activity summary:hover {
  color: var(--pg-text-secondary);
}

.pg-work-title {
  color: inherit;
}

.pg-work-summary {
  color: var(--pg-text-muted);
  font-size: 0.82rem;
  font-weight: 650;
}

.pg-work-chevron {
  display: inline-flex;
  transform: translateY(-0.01rem);
  color: var(--pg-text-muted);
  font-size: 1rem;
  transition: transform 120ms ease;
}

.pg-work-activity[open] .pg-work-chevron {
  transform: rotate(90deg);
}

.pg-work-body {
  margin-top: 0.72rem;
  border-top: 1px solid var(--pg-border-default);
  padding-top: 0.68rem;
}

.pg-work-step + .pg-work-step {
  margin-top: 0.62rem;
}

.pg-work-step-title {
  color: var(--pg-text-primary);
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.35;
}

.pg-work-step-detail {
  color: var(--pg-text-secondary);
  font-size: 0.8rem;
  line-height: 1.5;
  margin-top: 0.14rem;
}

.pg-work-query-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.34rem;
  margin-top: 0.42rem;
}

.pg-work-query {
  display: inline-flex;
  max-width: 100%;
  border: 1px solid var(--pg-border-default);
  border-radius: var(--pg-radius-full);
  background: var(--pg-bg-surface-muted);
  color: var(--pg-text-secondary);
  padding: 0.2rem 0.46rem;
  font-size: 0.76rem;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.pg-scroll-anchor {
  width: 1px;
  height: calc(var(--pg-composer-safe-space) + 0.4rem);
  pointer-events: none;
  scroll-margin-bottom: var(--pg-composer-safe-space);
}

@media (max-width: 720px) {
  .pg-chat-bubble,
  .pg-active-status {
    max-width: 86%;
  }
  .pg-final-answer-only,
  div[data-testid="stExpander"]:has(.pg-work-history-anchor) {
    width: calc(100% - 1.6rem);
  }
  .pg-activity-row {
    width: calc(100% - 2.55rem);
    margin-left: 2.55rem;
  }
  div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) [data-testid="stChatMessageContent"],
  div[data-testid="stChatMessage"]:has(.pg-config-bubble-anchor) > div:last-child {
    width: min(86%, 100%);
    max-width: 86%;
  }
  .pg-chat-avatar-wrap {
    width: 2rem;
    min-width: 2rem;
  }
  div[data-testid="stForm"]:has(.pg-empty-composer-anchor),
  div[data-testid="stForm"]:has(.pg-docked-composer-anchor) {
    width: calc(100vw - 1.6rem);
  }
  .pg-empty-state {
    min-height: 38vh;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )
