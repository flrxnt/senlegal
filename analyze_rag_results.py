#!/usr/bin/env python3
"""
Analyse des résultats du test RAG SenLegal — 100 questions.
Génère des graphiques PNG et un rapport JSON détaillé.
"""

import json
import os
import statistics
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BASE_DIR = os.path.dirname(__file__)
RESULTS_FILE = os.path.join(BASE_DIR, "rag_test_results.json")
CHARTS_DIR = os.path.join(BASE_DIR, "rag_charts")
ANALYSIS_FILE = os.path.join(BASE_DIR, "rag_analysis.json")

CATEGORIES = {
    "Cadre juridique général": list(range(1, 11)),
    "Définitions": list(range(11, 21)),
    "Champ d'application": list(range(21, 31)),
    "Procédures de passation": list(range(31, 41)),
    "Garanties et exécution": list(range(41, 51)),
    "Achats durables et PME": list(range(51, 61)),
    "Organes (ARCOP/DCMP)": list(range(61, 71)),
    "PPP et concessions": list(range(71, 81)),
    "Directives UEMOA": list(range(81, 91)),
    "Questions transversales": list(range(91, 101)),
}

GREEN = "#00853F"
GREEN_LIGHT = "#66BB6A"
RED = "#E53935"
ORANGE = "#FF9800"
BLUE = "#1E88E5"
GRAY = "#9E9E9E"
BG = "#FAFAFA"


def load_results():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_answer(r):
    """Classify answer quality: 'answered', 'partial', 'refused'."""
    answer = r.get("answer", "").lower()
    answer_nospaces = answer.replace(" ", "")
    refusal_markers = [
        "je ne dispose pas",
        "je n'ai pas",
        "hors du périmètre",
        "pas d'information",
        "ne permet pas de",
        "je ne peux pas",
        "le contexte fourni ne permet pas",
        "les extraits fournis ne",
        "jenedisposepas",
        "jen'aipas",
        "horsdu périmètre",
        "lecontextefourni nepermetpas",
        "lesextraits fournisne",
        "nepermetpas dedistinguer",
        "nepermetpasdedistinguer",
        "neprécisentpas",
        "ne précisent pas",
    ]
    if any(m in answer for m in refusal_markers) or any(m in answer_nospaces for m in refusal_markers):
        if len(answer) > 200:
            return "partial"
        return "refused"
    if r.get("used_context") is False:
        return "refused"
    return "answered"


def analyze(data):
    results = data["results"]
    stats = data["stats"]

    analysis = {
        "summary": {},
        "per_category": {},
        "response_times": {},
        "token_stats": {},
        "citation_stats": {},
        "quality": {},
        "refused_questions": [],
        "slowest_questions": [],
        "fastest_questions": [],
    }

    times = [r["response_time_ms"] for r in results if r["status"] == "success"]
    tokens = [r["token_count"] for r in results if r["status"] == "success"]
    cit_counts = [len(r["citations"]) for r in results if r["status"] == "success"]

    classifications = [classify_answer(r) for r in results]
    answered = classifications.count("answered")
    partial = classifications.count("partial")
    refused = classifications.count("refused")

    analysis["summary"] = {
        "total": len(results),
        "success_rate": f"{stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.0f}%)",
        "answered": answered,
        "partial": partial,
        "refused": refused,
        "answer_rate": f"{answered}/{len(results)} ({answered/len(results)*100:.1f}%)",
        "avg_response_ms": stats["avg_response_time_ms"],
        "median_response_ms": int(statistics.median(times)) if times else 0,
        "p95_response_ms": int(np.percentile(times, 95)) if times else 0,
        "min_response_ms": min(times) if times else 0,
        "max_response_ms": max(times) if times else 0,
    }

    analysis["response_times"] = {
        "mean": round(statistics.mean(times)),
        "median": int(statistics.median(times)),
        "stdev": round(statistics.stdev(times)) if len(times) > 1 else 0,
        "p5": int(np.percentile(times, 5)),
        "p25": int(np.percentile(times, 25)),
        "p75": int(np.percentile(times, 75)),
        "p95": int(np.percentile(times, 95)),
        "p99": int(np.percentile(times, 99)),
    }

    analysis["token_stats"] = {
        "mean": round(statistics.mean(tokens), 1),
        "median": int(statistics.median(tokens)),
        "min": min(tokens),
        "max": max(tokens),
        "total": sum(tokens),
    }

    for cat_name, q_nums in CATEGORIES.items():
        cat_results = [r for r in results if r["question_number"] in q_nums]
        cat_classes = [classify_answer(r) for r in cat_results]
        cat_times = [r["response_time_ms"] for r in cat_results if r["status"] == "success"]
        cat_tokens = [r["token_count"] for r in cat_results if r["status"] == "success"]
        analysis["per_category"][cat_name] = {
            "total": len(cat_results),
            "answered": cat_classes.count("answered"),
            "partial": cat_classes.count("partial"),
            "refused": cat_classes.count("refused"),
            "avg_time_ms": round(statistics.mean(cat_times)) if cat_times else 0,
            "avg_tokens": round(statistics.mean(cat_tokens), 1) if cat_tokens else 0,
        }

    for i, r in enumerate(results):
        if classifications[i] in ("refused", "partial"):
            analysis["refused_questions"].append({
                "number": r["question_number"],
                "question": r["question"],
                "classification": classifications[i],
                "answer_preview": r["answer"][:200],
            })

    sorted_by_time = sorted(results, key=lambda x: x["response_time_ms"], reverse=True)
    analysis["slowest_questions"] = [
        {"number": r["question_number"], "question": r["question"][:80], "time_ms": r["response_time_ms"]}
        for r in sorted_by_time[:5]
    ]
    analysis["fastest_questions"] = [
        {"number": r["question_number"], "question": r["question"][:80], "time_ms": r["response_time_ms"]}
        for r in sorted_by_time[-5:]
    ]

    return analysis, results, classifications


def make_charts(analysis, results, classifications):
    os.makedirs(CHARTS_DIR, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.facecolor": BG,
        "figure.facecolor": "white",
    })

    # 1. Taux de réponse global (donut)
    fig, ax = plt.subplots(figsize=(7, 7))
    answered = classifications.count("answered")
    partial = classifications.count("partial")
    refused = classifications.count("refused")
    sizes = [answered, partial, refused]
    labels = [f"Répondu ({answered})", f"Partiel ({partial})", f"Refusé ({refused})"]
    colors = [GREEN, ORANGE, RED]
    non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
    if non_zero:
        sizes_nz, labels_nz, colors_nz = zip(*non_zero)
    else:
        sizes_nz, labels_nz, colors_nz = sizes, labels, colors
    wedges, texts, autotexts = ax.pie(
        sizes_nz, labels=labels_nz, colors=colors_nz, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75, textprops={"fontsize": 12}
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_color("white")
    centre = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre)
    ax.text(0, 0, f"{answered + partial}\n/100", ha="center", va="center", fontsize=22, fontweight="bold", color=GREEN)
    ax.set_title("Qualité des réponses RAG — 100 questions", fontsize=14, fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "01_quality_donut.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 01_quality_donut.png")

    # 2. Temps de réponse — histogramme
    fig, ax = plt.subplots(figsize=(10, 5))
    times = [r["response_time_ms"] / 1000 for r in results if r["status"] == "success"]
    ax.hist(times, bins=20, color=GREEN, edgecolor="white", alpha=0.85)
    med = statistics.median(times)
    ax.axvline(med, color=RED, linestyle="--", linewidth=2, label=f"Médiane : {med:.1f}s")
    ax.set_xlabel("Temps de réponse (secondes)", fontsize=12)
    ax.set_ylabel("Nombre de questions", fontsize=12)
    ax.set_title("Distribution des temps de réponse", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "02_response_time_hist.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 02_response_time_hist.png")

    # 3. Temps de réponse par question (scatter)
    fig, ax = plt.subplots(figsize=(14, 5))
    q_nums = [r["question_number"] for r in results]
    times_ms = [r["response_time_ms"] / 1000 for r in results]
    colors_scatter = [RED if classifications[i] == "refused" else (ORANGE if classifications[i] == "partial" else GREEN) for i in range(len(results))]
    ax.scatter(q_nums, times_ms, c=colors_scatter, s=30, alpha=0.8, edgecolors="white", linewidth=0.5)
    avg_line = statistics.mean(times_ms)
    ax.axhline(avg_line, color=BLUE, linestyle="--", linewidth=1.5, alpha=0.7, label=f"Moyenne : {avg_line:.1f}s")
    ax.set_xlabel("Numéro de question", fontsize=12)
    ax.set_ylabel("Temps (secondes)", fontsize=12)
    ax.set_title("Temps de réponse par question", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xlim(0, 101)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "03_response_time_scatter.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 03_response_time_scatter.png")

    # 4. Performance par catégorie (barres horizontales)
    fig, ax = plt.subplots(figsize=(12, 7))
    cat_names = list(CATEGORIES.keys())
    cat_answered = [analysis["per_category"][c]["answered"] for c in cat_names]
    cat_partial = [analysis["per_category"][c]["partial"] for c in cat_names]
    cat_refused = [analysis["per_category"][c]["refused"] for c in cat_names]
    y = np.arange(len(cat_names))
    h = 0.6
    ax.barh(y, cat_answered, h, label="Répondu", color=GREEN, edgecolor="white")
    ax.barh(y, cat_partial, h, left=cat_answered, label="Partiel", color=ORANGE, edgecolor="white")
    left2 = [a + p for a, p in zip(cat_answered, cat_partial)]
    ax.barh(y, cat_refused, h, left=left2, label="Refusé", color=RED, edgecolor="white")
    ax.set_yticks(y)
    ax.set_yticklabels(cat_names, fontsize=11)
    ax.set_xlabel("Nombre de questions", fontsize=12)
    ax.set_title("Qualité des réponses par catégorie thématique", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=11)
    ax.set_xlim(0, 11)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "04_category_quality.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 04_category_quality.png")

    # 5. Temps moyen par catégorie
    fig, ax = plt.subplots(figsize=(12, 6))
    cat_times = [analysis["per_category"][c]["avg_time_ms"] / 1000 for c in cat_names]
    bars = ax.barh(y, cat_times, h, color=BLUE, edgecolor="white", alpha=0.85)
    for bar, val in zip(bars, cat_times):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}s", va="center", fontsize=10)
    ax.set_yticks(y)
    ax.set_yticklabels(cat_names, fontsize=11)
    ax.set_xlabel("Temps moyen (secondes)", fontsize=12)
    ax.set_title("Temps de réponse moyen par catégorie", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "05_category_time.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 05_category_time.png")

    # 6. Nombre de tokens par question
    fig, ax = plt.subplots(figsize=(14, 5))
    tok_counts = [r["token_count"] for r in results]
    ax.bar(q_nums, tok_counts, color=GREEN, edgecolor="white", alpha=0.8, width=0.8)
    ax.axhline(statistics.mean(tok_counts), color=RED, linestyle="--", linewidth=1.5,
               label=f"Moyenne : {statistics.mean(tok_counts):.0f} tokens")
    ax.set_xlabel("Numéro de question", fontsize=12)
    ax.set_ylabel("Tokens générés", fontsize=12)
    ax.set_title("Nombre de tokens par réponse", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xlim(0, 101)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "06_tokens_per_question.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 06_tokens_per_question.png")

    # 7. Score de similarité moyen par question
    fig, ax = plt.subplots(figsize=(14, 5))
    avg_scores = []
    for r in results:
        scores = [c.get("score", 0) for c in r.get("citations", []) if c.get("score")]
        avg_scores.append(statistics.mean(scores) if scores else 0)
    ax.bar(q_nums, avg_scores, color=BLUE, edgecolor="white", alpha=0.8, width=0.8)
    ax.axhline(0.35, color=RED, linestyle="--", linewidth=2, label="Seuil minimum (0.35)")
    ax.axhline(statistics.mean(avg_scores), color=ORANGE, linestyle="--", linewidth=1.5,
               label=f"Moyenne : {statistics.mean(avg_scores):.3f}")
    ax.set_xlabel("Numéro de question", fontsize=12)
    ax.set_ylabel("Score de similarité cosinus", fontsize=12)
    ax.set_title("Score de similarité moyen des citations par question", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xlim(0, 101)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "07_similarity_scores.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 07_similarity_scores.png")

    # 8. Distribution des scores
    fig, ax = plt.subplots(figsize=(10, 5))
    all_scores = []
    for r in results:
        for c in r.get("citations", []):
            if c.get("score"):
                all_scores.append(c["score"])
    ax.hist(all_scores, bins=30, color=GREEN, edgecolor="white", alpha=0.85)
    ax.axvline(0.35, color=RED, linestyle="--", linewidth=2, label="Seuil minimum (0.35)")
    ax.axvline(statistics.mean(all_scores), color=BLUE, linestyle="--", linewidth=1.5,
               label=f"Moyenne : {statistics.mean(all_scores):.3f}")
    ax.set_xlabel("Score de similarité cosinus", fontsize=12)
    ax.set_ylabel("Nombre de citations", fontsize=12)
    ax.set_title("Distribution des scores de similarité (toutes citations)", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "08_score_distribution.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 08_score_distribution.png")

    # 9. Top sources documentaires citées
    fig, ax = plt.subplots(figsize=(12, 5))
    doc_counter = Counter()
    for r in results:
        for c in r.get("citations", []):
            doc = c.get("document", "Inconnu")
            if doc:
                short = doc[:60] + ("..." if len(doc) > 60 else "")
                doc_counter[short] += 1
    if doc_counter:
        top_docs = doc_counter.most_common(8)
        docs, counts = zip(*top_docs)
        y_d = np.arange(len(docs))
        ax.barh(y_d, counts, 0.6, color=GREEN, edgecolor="white")
        ax.set_yticks(y_d)
        ax.set_yticklabels(docs, fontsize=10)
        ax.set_xlabel("Nombre de citations", fontsize=12)
        ax.set_title("Sources documentaires les plus citées", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "09_top_sources.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 09_top_sources.png")

    # 10. Tableau résumé par catégorie (image)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis("off")
    headers = ["Catégorie", "Répondu", "Partiel", "Refusé", "Taux", "Temps moy.", "Tokens moy."]
    table_data = []
    for cat in cat_names:
        c = analysis["per_category"][cat]
        rate = (c["answered"] + c["partial"]) / c["total"] * 100 if c["total"] else 0
        table_data.append([
            cat,
            str(c["answered"]),
            str(c["partial"]),
            str(c["refused"]),
            f"{rate:.0f}%",
            f"{c['avg_time_ms']/1000:.1f}s",
            str(c["avg_tokens"]),
        ])
    table = ax.table(cellText=table_data, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)
    for j, header in enumerate(headers):
        table[0, j].set_facecolor(GREEN)
        table[0, j].set_text_props(color="white", fontweight="bold")
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            table[i, j].set_facecolor("#F5FAF7" if i % 2 == 0 else "white")
    ax.set_title("Résumé par catégorie thématique", fontsize=14, fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "10_summary_table.png"), dpi=150)
    plt.close(fig)
    print("  ✓ 10_summary_table.png")

    print(f"\n  📊 {len(os.listdir(CHARTS_DIR))} graphiques sauvegardés dans {CHARTS_DIR}/")


def main():
    print("=== Analyse des résultats RAG SenLegal ===\n")
    data = load_results()
    analysis, results, classifications = analyze(data)

    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"  📄 Analyse sauvegardée → {ANALYSIS_FILE}")

    print("\n--- Génération des graphiques ---")
    make_charts(analysis, results, classifications)

    print("\n" + "=" * 60)
    print("RÉSUMÉ DE L'ANALYSE")
    print("=" * 60)
    s = analysis["summary"]
    print(f"  Taux de succès API :     {s['success_rate']}")
    print(f"  Réponses complètes :     {s['answered']}/100")
    print(f"  Réponses partielles :    {s['partial']}/100")
    print(f"  Refus (hors périmètre) : {s['refused']}/100")
    print(f"  Taux de réponse :        {s['answer_rate']}")
    print(f"  Temps moyen :            {s['avg_response_ms']}ms")
    print(f"  Temps médian :           {s['median_response_ms']}ms")
    print(f"  P95 :                    {s['p95_response_ms']}ms")
    print(f"  Min/Max :                {s['min_response_ms']}ms / {s['max_response_ms']}ms")
    print()
    if analysis["refused_questions"]:
        print(f"  Questions refusées/partielles ({len(analysis['refused_questions'])}):")
        for rq in analysis["refused_questions"]:
            print(f"    Q{rq['number']}: {rq['question'][:70]}... [{rq['classification']}]")
    print("=" * 60)


if __name__ == "__main__":
    main()
