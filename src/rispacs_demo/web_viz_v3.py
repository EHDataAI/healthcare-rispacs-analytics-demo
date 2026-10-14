from __future__ import annotations

import html
import json
from hashlib import sha256

import pandas as pd

from rispacs_demo.reporting_sla import (
    ACTIVE_SLA_STATES,
    ReportingSLAConfig,
    active_sla_counts,
)

MODALITY_ORDER = [
    "CT",
    "MR",
    "US",
    "CR",
    "DX",
]

MODALITY_COLORS = {
    "CT": "#74A7D8",
    "MR": "#6FD2B0",
    "US": "#C7A76A",
    "CR": "#A88FD8",
    "DX": "#8FA2B4",
}

SLA_COLORS = {
    "NORMAL": "#6FD2B0",
    "WARNING": "#F6C85F",
    "CRITICAL": "#F28E5B",
    "BREACHED": "#FF6B6B",
}


def _safe_context_key(
    context_key: str,
) -> str:
    safe = "".join(
        character for character in str(context_key) if character.isalnum() or character in "-_"
    )

    return safe or "default"


def _empty_html(
    title: str,
    message: str,
) -> str:
    return f"""
<div style="
    box-sizing:border-box;
    min-height:245px;
    padding:18px;
    border-radius:10px;
    background:#151D26;
    color:#F3F6F8;
    font-family:Inter,Arial,sans-serif;
">
    <strong style="
        display:block;
        font-size:15px;
        font-weight:700;
        margin-bottom:6px;
    ">{html.escape(title)}</strong>
    <p style="
        color:#A7B3BE;
        font-size:11px;
        line-height:1.45;
        margin:0;
    ">{html.escape(message)}</p>
</div>
"""


def _animated_bar_html(
    items: list[dict[str, object]],
    title: str,
    subtitle: str,
    context_key: str,
) -> str:
    if not items:
        return _empty_html(
            title,
            "No data available for the selected filters.",
        )

    safe_key = _safe_context_key(context_key)
    digest = sha256(title.encode("utf-8")).hexdigest()[:8]
    root_id = f"rispacs-v3-{safe_key}-{digest}"

    payload = json.dumps(
        items,
        ensure_ascii=False,
    ).replace(
        "</",
        "<\\/",
    )

    template = r"""
<style>
html,
body {
    margin: 0;
    padding: 0;
    background: #151D26;
    color: #F3F6F8;
    overflow: hidden;
}

#__ROOT_ID__ {
    --surface: #151D26;
    --surface-2: #1B2530;
    --fg: #F3F6F8;
    --muted: #A7B3BE;
    --border: #2B3743;
    --grid: #26323D;
    --accent: #C7A76A;

    box-sizing: border-box;
    width: 100%;
    min-height: 274px;
    padding: 14px 16px 8px 16px;
    border-radius: 10px;
    background: var(--surface);
    color: var(--fg);
    font-family: Inter, "Segoe UI", Arial, sans-serif;
}

#__ROOT_ID__ .chart-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
    margin: 0 0 2px 0;
}

#__ROOT_ID__ .chart-heading {
    min-width: 0;
}

#__ROOT_ID__ .chart-title {
    color: var(--fg);
    font-size: 15px;
    font-weight: 720;
    letter-spacing: -0.012em;
    line-height: 1.2;
    margin: 0;
}

#__ROOT_ID__ .chart-subtitle {
    color: var(--muted);
    font-size: 10.5px;
    line-height: 1.35;
    margin: 4px 0 0 0;
}

#__ROOT_ID__ .context-badge {
    flex: 0 0 auto;
    margin-top: 1px;
    padding: 4px 7px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--muted);
    font-size: 8.5px;
    font-weight: 650;
    letter-spacing: 0.035em;
    text-transform: uppercase;
}

#__ROOT_ID__ svg {
    width: 100%;
    height: auto;
    display: block;
    overflow: visible;
}

#__ROOT_ID__ .baseline {
    stroke: var(--border);
    stroke-width: 1.1;
}

#__ROOT_ID__ .leader {
    stroke: var(--muted);
    stroke-width: 1;
    stroke-dasharray: 3 4;
    opacity: 0.75;
}

#__ROOT_ID__ .value {
    fill: var(--fg);
    font-size: 15px;
    font-weight: 720;
    text-anchor: middle;
}

#__ROOT_ID__ .category {
    fill: var(--fg);
    font-size: 11px;
    font-weight: 680;
    text-anchor: middle;
}

#__ROOT_ID__ .detail {
    fill: var(--muted);
    font-size: 8.7px;
    text-anchor: middle;
}

@media (prefers-reduced-motion: reduce) {
    #__ROOT_ID__ {
        scroll-behavior: auto;
    }
}
</style>

<div id="__ROOT_ID__">
    <div class="chart-header">
        <div class="chart-heading">
            <div class="chart-title">__TITLE__</div>
            <div class="chart-subtitle">__SUBTITLE__</div>
        </div>
        <div class="context-badge">Applied context</div>
    </div>

    <svg
        viewBox="0 0 760 255"
        role="img"
        aria-label="Animated analytical bar chart"
    >
        <defs class="gradient-defs"></defs>

        <line
            class="baseline"
            x1="48"
            y1="198"
            x2="725"
            y2="198"
        ></line>

        <g class="chart-layer"></g>
    </svg>
</div>

<script>
(() => {
    const root =
        document.getElementById(
            "__ROOT_ID__"
        );

    if (!root) {
        return;
    }

    const data = __DATA__;

    const layer =
        root.querySelector(
            ".chart-layer"
        );

    const defs =
        root.querySelector(
            ".gradient-defs"
        );

    const NS =
        "http://www.w3.org/2000/svg";

    const width = 760;
    const left = 55;
    const right = 35;
    const baseY = 198;
    const maxHeight = 118;

    const maxValue = Math.max(
        1,
        ...data.map(
            item =>
                Number(item.value) || 0
        )
    );

    const slot =
        (width - left - right)
        / data.length;

    const barWidth =
        Math.min(
            68,
            slot * 0.42
        );

    const clamp = value =>
        Math.max(
            0,
            Math.min(
                1,
                value
            )
        );

    const easeOut = value =>
        1 - Math.pow(
            1 - clamp(value),
            3
        );

    const svgNode = (
        name,
        attrs = {}
    ) => {
        const node =
            document.createElementNS(
                NS,
                name
            );

        Object.entries(
            attrs
        ).forEach(
            ([key, value]) => {
                node.setAttribute(
                    key,
                    String(value)
                );
            }
        );

        return node;
    };

    const shade = (
        hex,
        amount
    ) => {
        const raw =
            hex.replace("#", "");

        const number =
            parseInt(raw, 16);

        const r = Math.max(
            0,
            Math.min(
                255,
                (number >> 16)
                + amount
            )
        );

        const g = Math.max(
            0,
            Math.min(
                255,
                ((number >> 8) & 255)
                + amount
            )
        );

        const b = Math.max(
            0,
            Math.min(
                255,
                (number & 255)
                + amount
            )
        );

        return (
            "#"
            + (
                (1 << 24)
                + (r << 16)
                + (g << 8)
                + b
            )
            .toString(16)
            .slice(1)
        );
    };

    const elements =
        data.map(
            (item, index) => {
                const centerX =
                    left
                    + slot * index
                    + slot / 2;

                const x =
                    centerX
                    - barWidth / 2;

                const color =
                    item.color
                    || "#74A7D8";

                const gradient =
                    svgNode(
                        "linearGradient",
                        {
                            id:
                                "__ROOT_ID__"
                                + "-g-"
                                + index,
                            x1: "0%",
                            x2: "100%",
                            y1: "0%",
                            y2: "0%"
                        }
                    );

                [
                    [
                        "0%",
                        shade(
                            color,
                            -30
                        )
                    ],
                    [
                        "28%",
                        shade(
                            color,
                            10
                        )
                    ],
                    [
                        "52%",
                        shade(
                            color,
                            24
                        )
                    ],
                    [
                        "72%",
                        color
                    ],
                    [
                        "100%",
                        shade(
                            color,
                            -24
                        )
                    ]
                ].forEach(
                    (
                        [
                            offset,
                            stopColor
                        ]
                    ) => {
                        gradient.appendChild(
                            svgNode(
                                "stop",
                                {
                                    offset,
                                    "stop-color":
                                        stopColor
                                }
                            )
                        );
                    }
                );

                defs.appendChild(
                    gradient
                );

                const shadow =
                    svgNode(
                        "ellipse",
                        {
                            cx: centerX,
                            cy: baseY + 5,
                            rx: barWidth * 0.58,
                            ry: 7,
                            fill: "#000000",
                            opacity: 0.18
                        }
                    );

                const body =
                    svgNode(
                        "rect",
                        {
                            x,
                            y: baseY,
                            width: barWidth,
                            height: 0,
                            rx: 3,
                            fill:
                                "url(#__ROOT_ID__"
                                + "-g-"
                                + index
                                + ")"
                        }
                    );

                const bottom =
                    svgNode(
                        "ellipse",
                        {
                            cx: centerX,
                            cy: baseY,
                            rx: barWidth / 2,
                            ry: 5.2,
                            fill:
                                shade(
                                    color,
                                    -18
                                ),
                            opacity: 0
                        }
                    );

                const cap =
                    svgNode(
                        "ellipse",
                        {
                            cx: centerX,
                            cy: baseY,
                            rx: barWidth / 2,
                            ry: 5.2,
                            fill:
                                shade(
                                    color,
                                    28
                                ),
                            opacity: 0
                        }
                    );

                const leader =
                    svgNode(
                        "line",
                        {
                            class: "leader",
                            x1: centerX,
                            x2: centerX,
                            y1: baseY,
                            y2: baseY,
                            opacity: 0
                        }
                    );

                const value =
                    svgNode(
                        "text",
                        {
                            class: "value",
                            x: centerX,
                            y: baseY - 27,
                            opacity: 0
                        }
                    );

                const category =
                    svgNode(
                        "text",
                        {
                            class:
                                "category",
                            x: centerX,
                            y: baseY + 25,
                            opacity: 0
                        }
                    );

                category.textContent =
                    item.label;

                const detail =
                    svgNode(
                        "text",
                        {
                            class:
                                "detail",
                            x: centerX,
                            y: baseY + 40,
                            opacity: 0
                        }
                    );

                detail.textContent =
                    item.detail || "";

                layer.append(
                    shadow,
                    bottom,
                    body,
                    cap,
                    leader,
                    value,
                    category,
                    detail
                );

                const rawValue =
                    Number(
                        item.value
                    ) || 0;

                const targetHeight =
                    rawValue > 0
                        ? Math.max(
                            6,
                            maxHeight
                            * (
                                rawValue
                                / maxValue
                            )
                        )
                        : 0;

                return {
                    item,
                    targetHeight,
                    shadow,
                    body,
                    bottom,
                    cap,
                    leader,
                    value,
                    category,
                    detail
                };
            }
        );

    const finalElapsed =
        (
            data.length - 1
        ) * 135
        + 1080;

    const render = elapsed => {
        const stagger = 135;
        const growDuration = 700;
        const revealDelay = 455;
        const revealDuration = 340;

        elements.forEach(
            (
                entry,
                index
            ) => {
                const local =
                    elapsed
                    - index * stagger;

                const p =
                    easeOut(
                        local
                        / growDuration
                    );

                const q =
                    easeOut(
                        (
                            local
                            - revealDelay
                        )
                        / revealDuration
                    );

                const height =
                    entry.targetHeight
                    * p;

                const top =
                    baseY - height;

                entry.shadow.setAttribute(
                    "opacity",
                    height > 0
                        ? 0.18 * p
                        : 0
                );

                entry.body.setAttribute(
                    "y",
                    top
                );

                entry.body.setAttribute(
                    "height",
                    height
                );

                entry.bottom.setAttribute(
                    "opacity",
                    p > 0.02
                        && height > 0
                        ? 1
                        : 0
                );

                entry.cap.setAttribute(
                    "cy",
                    top
                );

                entry.cap.setAttribute(
                    "opacity",
                    p > 0.02
                        && height > 0
                        ? 1
                        : 0
                );

                const lineLength =
                    19 * q;

                entry.leader.setAttribute(
                    "y1",
                    top - 2
                );

                entry.leader.setAttribute(
                    "y2",
                    top
                    - 2
                    - lineLength
                );

                entry.leader.setAttribute(
                    "opacity",
                    q
                );

                entry.value.setAttribute(
                    "y",
                    top - 26
                );

                entry.value.setAttribute(
                    "opacity",
                    q
                );

                entry.category.setAttribute(
                    "opacity",
                    q
                );

                entry.detail.setAttribute(
                    "opacity",
                    q
                );

                const shown =
                    Math.round(
                        Number(
                            entry.item.value
                        )
                        * p
                    );

                entry.value.textContent =
                    shown.toLocaleString();
            }
        );
    };

    const reducedMotion =
        window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

    if (reducedMotion) {
        render(finalElapsed);
        return;
    }

    const start =
        performance.now();

    const tick = now => {
        const elapsed =
            now - start;

        render(elapsed);

        if (
            elapsed
            < finalElapsed
        ) {
            requestAnimationFrame(
                tick
            );
        } else {
            render(
                finalElapsed
            );
        }
    };

    requestAnimationFrame(
        tick
    );
})();
</script>
"""

    return (
        template.replace(
            "__ROOT_ID__",
            root_id,
        )
        .replace(
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
    context_key: str,
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

    return _animated_bar_html(
        items,
        title="Study volume by modality",
        subtitle="Current applied analytical context.",
        context_key=context_key,
    )


def reporting_backlog_animation_html(
    sla_df: pd.DataFrame,
    config: ReportingSLAConfig,
    context_key: str,
) -> str:
    config.validate()

    counts = active_sla_counts(sla_df)

    details = {
        "NORMAL": (f">{config.warning_window_hours:g} h remaining"),
        "WARNING": (f">{config.critical_window_hours:g} to <= {config.warning_window_hours:g} h"),
        "CRITICAL": (f">0 to <= {config.critical_window_hours:g} h"),
        "BREACHED": ("Target exceeded"),
    }

    items = [
        {
            "label": state.title(),
            "value": int(counts[state]),
            "detail": details[state],
            "color": SLA_COLORS[state],
        }
        for state in ACTIVE_SLA_STATES
    ]

    return _animated_bar_html(
        items,
        title="Active reporting status",
        subtitle=("Time remaining relative to the configured synthetic reporting target."),
        context_key=context_key,
    )
