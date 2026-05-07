"""LLM 报告生成 + DOCX/PDF 导出"""
import os
import re
import subprocess
import numpy as np
from datetime import datetime
from docx import Document
from app.config.settings import get_settings
from app.utils.log_config import get_logger

logger = get_logger("services.report")
settings = get_settings()

PROMPT = """你是一名资深水质分析专家。请根据以下数据生成专业的水质巡航分析报告。

巡航基础信息：
水库：{reservoir_name}
时间：{date}
采样点数：{point_count}，深度层：{depth_layers}

水质指标统计：
【叶绿素】均值 {chl_mean:.2f}，标准差 {chl_std:.2f}，异常比例 {chl_anomaly_rate:.1%}
【溶解氧】均值 {odo_mean:.2f}，标准差 {odo_std:.2f}，异常比例 {odo_anomaly_rate:.1%}
【水温】均值 {temp_mean:.2f}，标准差 {temp_std:.2f}，异常比例 {temp_anomaly_rate:.1%}
【pH】均值 {ph_mean:.2f}，标准差 {ph_std:.2f}，异常比例 {ph_anomaly_rate:.1%}
【浊度】均值 {turb_mean:.2f}，标准差 {turb_std:.2f}，异常比例 {turb_anomaly_rate:.1%}

异常点位（示例）：
{anomaly_sample}

历史相似案例：
{cases_summary}

请按以下大纲撰写：
1. 总体水质评价
2. 主要异常区域及可能原因
3. 与历史相似案例对比分析
4. 改善建议"""


def compute_stats(rows, anomalies):
    indicators = ["chlorophyll", "dissolved_oxygen", "temperature", "ph", "turbidity"]
    shorts = ["chl", "odo", "temp", "ph", "turb"]
    stats = {}
    for ind, sn in zip(indicators, shorts):
        vals = [getattr(r, ind) for r in rows if getattr(r, ind) is not None]
        anom = [a for a in anomalies if a.get("indicator") == sn]
        stats[f"{sn}_mean"] = float(np.mean(vals)) if vals else 0
        stats[f"{sn}_std"] = float(np.std(vals)) if vals else 0
        stats[f"{sn}_anomaly_rate"] = len(anom) / len(rows) if rows else 0
    return stats


def build_prompt(task_info, stats, anomalies, similar):
    anomaly_text = "\n".join(
        f"  坐标({a['lon']:.5f}, {a['lat']:.5f}) 深度{a['depth']}m "
        f"指标{a['indicator']}={a['value']:.2f} 方法:{a['method']}"
        for a in anomalies[:20]
    ) or "无异常点"

    if similar:
        cases = "\n".join(
            f"  - {c.get('reservoir', '未知')} 相似度{c.get('similarity', 0):.2f}"
            for c in similar
        )
    else:
        cases = "暂无历史相似案例可供对比"

    return PROMPT.format(
        reservoir_name=task_info.get("reservoir_name", "未知"),
        date=task_info.get("created_at", datetime.utcnow().strftime("%Y-%m-%d")),
        point_count=task_info.get("total_points", 0),
        depth_layers=task_info.get("depth_layers", "N/A"),
        anomaly_sample=anomaly_text, cases_summary=cases, **stats,
    )


def call_llm(prompt: str) -> str:
    from openai import OpenAI
    if settings.LLM_PROVIDER == "deepseek":
        client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)
        model = settings.DEEPSEEK_MODEL
    else:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
        model = settings.OPENAI_MODEL
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=2048,
    )
    return resp.choices[0].message.content


def generate_docx(text: str, image_paths: list[str], task_id: str) -> str:
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    doc = Document()
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        else:
            doc.add_paragraph(re.sub(r"\*\*(.+?)\*\*", r"\1", line))
    for p in image_paths:
        if os.path.exists(p):
            doc.add_picture(p, width=5200000)
    path = os.path.join(settings.REPORT_DIR, f"{task_id}.docx")
    doc.save(path)
    return path


def convert_pdf(docx_path: str, task_id: str) -> str:
    pdf_path = os.path.join(settings.REPORT_DIR, f"{task_id}.pdf")
    try:
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf",
             "--outdir", settings.REPORT_DIR, docx_path],
            timeout=60, check=True,
        )
        if os.path.exists(pdf_path):
            return pdf_path
    except Exception as e:
        logger.warning(f"PDF 转换失败: {e}")
    return docx_path


def generate(task_info, rows, anomalies, similar=None, images=None):
    stats = compute_stats(rows, anomalies)
    prompt = build_prompt(task_info, stats, anomalies, similar or [])
    text = call_llm(prompt)
    docx = generate_docx(text, images or [], task_info["id"])
    return convert_pdf(docx, task_info["id"])
