from __future__ import annotations

import html
import json

import pandas as pd

MODALITY_ORDER = ["CT", "MR", "US", "CR", "DX"]

MODALITY_COLORS = {
    "CT": "#4C78A8",
    "MR": "#6F5BD3",
    "US": "#3BA272",
    "CR": "#D7A13B",
    "DX": "#7A8793",
}

SLA_COLORS = {
    "NORMAL": "#2E8B57",
    "WARNING": "#D99A2B",
    "CRITICAL": "#C0392B",
}


def _empty_html(title: str, message: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;padding:24px;">'
        f"<strong>{html.escape(title)}</strong>"
        f"<p>{html.escape(message)}</p>"
        "</div>"
    )


def _animated_columns_html(
    items: list[dict[str, object]],
    title: str,
    subtitle: str,
) -> str:
    if not items:
        return _empty_html(
            title,
            "No data available for the selected filters.",
        )

    payload = json.dumps(
        items,
        ensure_ascii=False,
    ).replace("</", "<\\/")

    template = r"""
<div id="rispacs-animation-root">
  <style>
    #rispacs-animation-root {
      --fg: #17202a;
      --muted: #65717e;
      --panel: #ffffff;
      --grid: #dfe5eb;
      font-family: Inter, Arial, sans-serif;
      color: var(--fg);
      background: transparent;
      width: 100%;
    }

    @media (prefers-color-scheme: dark) {
      #rispacs-animation-root {
        --fg: #f1f5f9;
        --muted: #a8b3bf;
        --panel: #0e1117;
        --grid: #303844;
      }
    }

    .viz-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 6px;
    }

    .viz-title {
      font-size: 18px;
      font-weight: 700;
      margin: 0;
    }

    .viz-subtitle {
      font-size: 12px;
      color: var(--muted);
      margin-top: 5px;
      line-height: 1.4;
    }

    .viz-replay {
      border: 1px solid var(--grid);
      background: transparent;
      color: var(--fg);
      border-radius: 7px;
      padding: 7px 13px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
    }

    .viz-replay:hover {
      background: rgba(128, 128, 128, 0.10);
    }

    .viz-svg {
      width: 100%;
      height: auto;
      display: block;
      overflow: visible;
    }

    .axis-line {
      stroke: var(--grid);
      stroke-width: 1.5;
    }

    .leader {
      stroke: var(--muted);
      stroke-width: 1.2;
      stroke-dasharray: 5 5;
    }

    .value-label {
      fill: var(--fg);
      font-size: 18px;
      font-weight: 700;
      text-anchor: middle;
    }

    .category-label {
      fill: var(--fg);
      font-size: 15px;
      font-weight: 650;
      text-anchor: middle;
    }

    .detail-label {
      fill: var(--muted);
      font-size: 11px;
      text-anchor: middle;
    }

    .footnote {
      color: var(--muted);
      font-size: 11px;
      margin-top: -8px;
    }
  </style>

  <div class="viz-header">
    <div>
      <div class="viz-title">__TITLE__</div>
      <div class="viz-subtitle">__SUBTITLE__</div>
    </div>

    <button
      class="viz-replay"
      type="button"
      aria-label="Repeat animation"
    >
      Repetir
    </button>
  </div>

  <svg
    class="viz-svg"
    viewBox="0 0 1000 455"
    role="img"
    aria-label="Animated analytical bar chart"
  >
    <defs id="gradient-defs"></defs>
    <line
      class="axis-line"
      x1="65"
      y1="365"
      x2="950"
      y2="365"
    ></line>
    <g class="chart-layer"></g>
  </svg>

  <div class="footnote">
    Animation plays once automatically. Values represent the current filtered analytical slice.
  </div>

  <script>
    (() => {
      const root = document.getElementById("rispacs-animation-root");
      if (!root || root.dataset.initialized === "true") return;
      root.dataset.initialized = "true";

      const data = __DATA__;
      const svg = root.querySelector(".viz-svg");
      const layer = root.querySelector(".chart-layer");
      const defs = root.querySelector("#gradient-defs");
      const replay = root.querySelector(".viz-replay");

      const NS = "http://www.w3.org/2000/svg";

      const width = 1000;
      const left = 75;
      const right = 55;
      const baseY = 365;
      const maxHeight = 235;

      const maxValue = Math.max(
        1,
        ...data.map(item => Number(item.value) || 0)
      );

      const slot = (width - left - right) / data.length;
      const barWidth = Math.min(105, slot * 0.48);

      const clamp = value =>
        Math.max(0, Math.min(1, value));

      const easeOut = value =>
        1 - Math.pow(1 - clamp(value), 3);

      const svgNode = (name, attrs = {}) => {
        const node = document.createElementNS(NS, name);

        Object.entries(attrs).forEach(([key, value]) => {
          node.setAttribute(key, String(value));
        });

        return node;
      };

      const shade = (hex, amount) => {
        const raw = hex.replace("#", "");
        const number = parseInt(raw, 16);

        const r = Math.max(
          0,
          Math.min(255, (number >> 16) + amount)
        );
        const g = Math.max(
          0,
          Math.min(255, ((number >> 8) & 255) + amount)
        );
        const b = Math.max(
          0,
          Math.min(255, (number & 255) + amount)
        );

        return (
          "#" +
          ((1 << 24) + (r << 16) + (g << 8) + b)
            .toString(16)
            .slice(1)
        );
      };

      const elements = data.map((item, index) => {
        const centerX = left + slot * index + slot / 2;
        const x = centerX - barWidth / 2;
        const color = item.color || "#4C78A8";

        const gradient = svgNode("linearGradient", {
          id: `grad-${index}`,
          x1: "0%",
          x2: "100%",
          y1: "0%",
          y2: "0%"
        });

        [
          ["0%", shade(color, -35)],
          ["30%", shade(color, 30)],
          ["58%", color],
          ["100%", shade(color, -35)]
        ].forEach(([offset, stopColor]) => {
          gradient.appendChild(
            svgNode("stop", {
              offset,
              "stop-color": stopColor
            })
          );
        });

        defs.appendChild(gradient);

        const body = svgNode("rect", {
          x,
          y: baseY,
          width: barWidth,
          height: 0,
          rx: 4,
          fill: `url(#grad-${index})`
        });

        const bottom = svgNode("ellipse", {
          cx: centerX,
          cy: baseY,
          rx: barWidth / 2,
          ry: 8,
          fill: shade(color, -15),
          opacity: 0
        });

        const cap = svgNode("ellipse", {
          cx: centerX,
          cy: baseY,
          rx: barWidth / 2,
          ry: 8,
          fill: shade(color, 25),
          opacity: 0
        });

        const leader = svgNode("line", {
          class: "leader",
          x1: centerX,
          x2: centerX,
          y1: baseY,
          y2: baseY,
          opacity: 0
        });

        const value = svgNode("text", {
          class: "value-label",
          x: centerX,
          y: baseY - 45,
          opacity: 0
        });

        const category = svgNode("text", {
          class: "category-label",
          x: centerX,
          y: baseY + 38,
          opacity: 0
        });

        category.textContent = item.label;

        const detail = svgNode("text", {
          class: "detail-label",
          x: centerX,
          y: baseY + 58,
          opacity: 0
        });

        detail.textContent = item.detail || "";

        layer.append(
          bottom,
          body,
          cap,
          leader,
          value,
          category,
          detail
        );

        const targetHeight =
          maxHeight * (Number(item.value) / maxValue);

        return {
          item,
          centerX,
          targetHeight,
          body,
          bottom,
          cap,
          leader,
          value,
          category,
          detail
        };
      });

      let raf = null;

      const render = elapsed => {
        const stagger = 170;
        const growDuration = 950;
        const revealDelay = 640;
        const revealDuration = 480;

        elements.forEach((entry, index) => {
          const local = elapsed - index * stagger;

          const p = easeOut(
            local / growDuration
          );

          const q = easeOut(
            (local - revealDelay) / revealDuration
          );

          const height = entry.targetHeight * p;
          const top = baseY - height;

          entry.body.setAttribute("y", top);
          entry.body.setAttribute("height", height);

          entry.bottom.setAttribute(
            "opacity",
            p > 0.02 ? 1 : 0
          );

          entry.cap.setAttribute("cy", top);
          entry.cap.setAttribute(
            "opacity",
            p > 0.02 ? 1 : 0
          );

          const leaderLength = 31 * q;

          entry.leader.setAttribute("y1", top - 3);
          entry.leader.setAttribute(
            "y2",
            top - 3 - leaderLength
          );
          entry.leader.setAttribute("opacity", q);

          entry.value.setAttribute(
            "y",
            top - 42
          );
          entry.value.setAttribute("opacity", q);

          entry.category.setAttribute("opacity", q);
          entry.detail.setAttribute("opacity", q);

          const shownValue = Math.round(
            Number(entry.item.value) * p
          );

          entry.value.textContent =
            shownValue.toLocaleString();
        });
      };

      const finalElapsed =
        (data.length - 1) * 170 + 1450;

      const startAnimation = () => {
        if (raf !== null) {
          cancelAnimationFrame(raf);
          raf = null;
        }

        const reducedMotion = window.matchMedia(
          "(prefers-reduced-motion: reduce)"
        ).matches;

        if (reducedMotion) {
          render(finalElapsed);
          replay.style.display = "none";
          return;
        }

        const start = performance.now();
        render(0);

        const tick = now => {
          const elapsed = now - start;
          render(elapsed);

          if (elapsed < finalElapsed) {
            raf = requestAnimationFrame(tick);
          } else {
            render(finalElapsed);
            raf = null;
          }
        };

        raf = requestAnimationFrame(tick);
      };

      replay.addEventListener(
        "click",
        startAnimation
      );

      startAnimation();
    })();
  </script>
</div>
"""

    return (
        template.replace(
            "__TITLE__",
            html.escape(title),
        )
        .replace(
            "__SUBTITLE__",
            html.escape(subtitle),
        )
        .replace(
            "__DATA__",
            payload,
        )
    )


def executive_volume_animation_html(
    df: pd.DataFrame,
) -> str:
    if df.empty:
        return _empty_html(
            "Study volume by modality",
            "No studies available for the selected filters.",
        )

    valid = df[df["modality"].isin(MODALITY_ORDER)]

    counts = (
        valid["modality"]
        .value_counts()
        .reindex(
            MODALITY_ORDER,
            fill_value=0,
        )
    )

    items = [
        {
            "label": modality,
            "value": int(counts.loc[modality]),
            "detail": "studies",
            "color": MODALITY_COLORS[modality],
        }
        for modality in MODALITY_ORDER
        if int(counts.loc[modality]) > 0
    ]

    return _animated_columns_html(
        items,
        "Study volume by modality",
        "Current filtered synthetic study volume. Bars animate automatically once.",
    )


def reporting_backlog_animation_html(
    alerts: pd.DataFrame,
    warning_hours: float,
    critical_hours: float,
) -> str:
    pending = alerts[alerts["report_status"].eq("PENDING")]

    counts = (
        pending["operational_state"]
        .value_counts()
        .reindex(
            ["NORMAL", "WARNING", "CRITICAL"],
            fill_value=0,
        )
    )

    details = {
        "NORMAL": f"< {warning_hours:g} h",
        "WARNING": (f"{warning_hours:g}–<{critical_hours:g} h"),
        "CRITICAL": f"≥ {critical_hours:g} h",
    }

    items = [
        {
            "label": state.title(),
            "value": int(counts.loc[state]),
            "detail": details[state],
            "color": SLA_COLORS[state],
        }
        for state in [
            "NORMAL",
            "WARNING",
            "CRITICAL",
        ]
    ]

    return _animated_columns_html(
        items,
        "Active reporting backlog",
        (
            "Operational state at the current point-in-time snapshot. "
            "Thresholds are configurable demo values."
        ),
    )
