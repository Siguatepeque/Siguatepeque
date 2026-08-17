#!/usr/bin/env node
// Regenerates the ACTIVE_LOG block in README.md from real GitHub activity.
// No hardcoded repos: eligibility and selection are computed fresh each run.

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const OWNER = process.env.GITHUB_REPOSITORY_OWNER || "Siguatepeque";
const TOKEN = process.env.GITHUB_TOKEN;
const README_PATH = fileURLToPath(new URL("../README.md", import.meta.url));
const START_MARK = "<!-- ACTIVE_LOG:START -->";
const END_MARK = "<!-- ACTIVE_LOG:END -->";

const WINDOW_DAYS = 14; // "currently active" horizon
const MAX_ITEMS = 3;
const LINE_WIDTH = 56;
const DESC_MAX = 46;

// Repo names treated as configuration/community-health, not project work.
const CONFIG_REPO_NAMES = new Set([".github", "config"]);

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function truncate(str, max) {
  if (!str) return null;
  const clean = str.trim().replace(/\s+/g, " ");
  return clean.length > max ? `${clean.slice(0, max - 1).trimEnd()}…` : clean;
}

// An absolute stamp, not a relative one: relative text ("2h ago") drifts on
// every run even with zero real change, which would force a commit each
// schedule tick. An absolute date only changes when something actually did.
function dateStamp(iso) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

function isEligible(repo) {
  return (
    repo.owner.login.toLowerCase() === OWNER.toLowerCase() &&
    repo.name.toLowerCase() !== OWNER.toLowerCase() && // the profile repo itself
    !repo.archived &&
    !repo.fork &&
    repo.size > 0 && // empty repos report size 0
    !CONFIG_REPO_NAMES.has(repo.name)
  );
}

async function fetchRepos() {
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "active-log-script",
  };
  if (TOKEN) headers.Authorization = `Bearer ${TOKEN}`;
  const res = await fetch(
    `https://api.github.com/users/${OWNER}/repos?type=owner&per_page=100&sort=pushed&direction=desc`,
    { headers },
  );
  if (!res.ok) throw new Error(`GitHub API responded ${res.status}`);
  return res.json();
}

function ruleLine() {
  return "─".repeat(LINE_WIDTH);
}

function headerLine(label) {
  const left = `&gt; ${label} `;
  const visibleLeft = `> ${label} `; // ">" renders as one char; measure on this
  const dashes = "─".repeat(Math.max(3, LINE_WIDTH - visibleLeft.length));
  return left + dashes;
}

function renderEntry(repo) {
  const lang = repo.language ? repo.language.toLowerCase() : "unlabeled";
  const desc = truncate(repo.description, DESC_MAX) || "no description logged";
  const name = escapeHtml(repo.name);
  return [
    `  <a href="${repo.html_url}"><b>${name}</b></a>  [${lang}]`,
    `      ${escapeHtml(desc)}`,
    `      last signal ${dateStamp(repo.pushed_at)}`,
  ].join("\n");
}

function renderBlock(items, mode) {
  const label = mode === "active" ? "ACTIVE_LOG" : mode === "recent" ? "LAST_SIGNAL" : "STANDBY";
  const lines = ["<pre>", headerLine(label)];

  if (items.length === 0) {
    lines.push("  no transmissions in range. instruments idle.");
  } else {
    lines.push(items.map(renderEntry).join("\n\n"));
  }

  lines.push(ruleLine());
  lines.push(
    `  STATUS  ${
      items.length === 0
        ? "idle"
        : mode === "active"
          ? `${items.length} experiment${items.length > 1 ? "s" : ""} running`
          : "last known activity"
    }`,
  );
  lines.push("</pre>");
  return lines.join("\n");
}

function selectRepos(repos) {
  const eligible = repos.filter(isEligible).sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at));
  const windowMs = WINDOW_DAYS * 24 * 60 * 60 * 1000;
  const active = eligible.filter((r) => Date.now() - new Date(r.pushed_at).getTime() <= windowMs);

  if (active.length > 0) return { mode: "active", items: active.slice(0, MAX_ITEMS) };
  if (eligible.length > 0) return { mode: "recent", items: [eligible[0]] };
  return { mode: "idle", items: [] };
}

async function main() {
  const repos = await fetchRepos();
  const { mode, items } = selectRepos(repos);
  const block = renderBlock(items, mode);

  const readme = await readFile(README_PATH, "utf8");
  const startIdx = readme.indexOf(START_MARK);
  const endIdx = readme.indexOf(END_MARK);
  if (startIdx === -1 || endIdx === -1) {
    throw new Error("ACTIVE_LOG markers not found in README.md");
  }

  const before = readme.slice(0, startIdx + START_MARK.length);
  const after = readme.slice(endIdx);
  const next = `${before}\n${block}\n${after}`;

  if (next === readme) {
    console.log("No change to ACTIVE_LOG — skipping write.");
    return;
  }
  await writeFile(README_PATH, next, "utf8");
  console.log(`ACTIVE_LOG updated: mode=${mode} items=${items.length}`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
