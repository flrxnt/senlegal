#!/usr/bin/env python3
"""
Test RAG SenLegal — 100 questions sur la commande publique au Sénégal.
Envoie chaque question via l'API streaming, collecte la réponse complète,
les citations et les métriques, puis sauvegarde le tout en JSON.
"""

import json
import time
import sys
import os
import requests
from datetime import datetime

API_BASE = "https://senlegal.flrxnt.com/api"
CONVERSATION_ID = "cmqiel5ff000706pmo7wzgqu8"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbW9tazBqOTIwMDAwMXlwZ3ljbTd2d3J6IiwiZW1haWwiOiJqZC5hem9ubm91ZG9AZ21haWwuY29tIiwicm9sZSI6IkFETUlOIiwicGxhbiI6IlBSTyIsImlhdCI6MTc4MTcyMTY3MCwiZXhwIjoxNzgyMzI2NDcwfQ.W108K-85h_8MKbgXNLi_wAiH1TLrAdybIVdUn8RjXKw"

QUESTIONS = [
    "Quel texte fixe les règles de préparation, de passation, d'exécution et de contrôle des marchés publics au Sénégal ?",
    "Quelle est la date du décret portant Code des marchés publics cité dans le recueil ?",
    "Quels sont les trois grands types de besoins couverts par les marchés publics ?",
    "Quels sont les principes fondamentaux applicables aux marchés publics selon le décret ?",
    "Quelles personnes morales sont concernées par l'article 2 du décret ?",
    "Quel est le rôle de l'organe en charge du contrôle des marchés publics ?",
    "Quel est le rôle de l'organe en charge de la régulation des marchés publics ?",
    "Quelle autorité fixe les seuils de contrôle a priori des dossiers de marchés ?",
    "Quelle autorité fixe les taux de la redevance de régulation des marchés publics ?",
    "Quel texte crée la Direction centrale des Marchés publics ?",
    "Comment le décret définit-il un marché public ?",
    "Comment le décret définit-il un accord-cadre ?",
    "Comment le décret définit-il un candidat ?",
    "Comment le décret définit-il un attributaire ?",
    "Comment le décret définit-il une autorité contractante ?",
    "Comment le décret définit-il un ouvrage ?",
    "Comment le décret définit-il une fourniture ?",
    "Comment le décret définit-il la dématérialisation ?",
    "Comment le décret définit-il le cycle de vie d'un produit ?",
    "Comment le décret définit-il le contenu local ?",
    "À quelles catégories d'autorités contractantes s'applique le décret ?",
    "Les marchés passés pour le compte d'une autorité contractante suivent-ils les mêmes règles que ceux passés directement par elle ?",
    "Les marchés financés par un accord de financement international sont-ils soumis au Code ?",
    "Dans quel cas un accord international peut-il primer sur le Code ?",
    "Quelles prestations sont expressément exclues du champ du décret ?",
    "Les contrats de travail entrent-ils dans le champ du Code ?",
    "Les marchés de défense et sécurité suivent-ils toujours les procédures ordinaires ?",
    "Les missions diplomatiques et consulaires à l'étranger sont-elles soumises aux procédures ordinaires ?",
    "Les acquisitions de mobilier national aux enchères publiques sont-elles encadrées par le Code ?",
    "Une réglementation particulière peut-elle déroger au Code pour une catégorie d'acheteurs publics ?",
    "Quelles procédures de passation sont mentionnées dans le recueil pour les marchés publics ?",
    "Quel texte encadre les procédures de demande de renseignements et de prix ?",
    "Quel texte fixe les seuils en dessous desquels la garantie de soumission peut ne pas être requise ?",
    "Quel texte fixe les seuils à partir desquels une garantie de bonne exécution est requise ?",
    "Quel texte fixe les seuils de contrôle a priori des dossiers de marchés ?",
    "Quelle est la logique générale du contrôle a priori dans le système sénégalais ?",
    "Comment les délais de recours sont-ils qualifiés dans le Code ?",
    "Les délais prévus dans le décret sont-ils calendaires ou ouvrés par défaut ?",
    "Quel rôle joue la publicité dans les procédures de marché public ?",
    "Quelle procédure permet de consulter plusieurs opérateurs pour déterminer un prix ou un renseignement ?",
    "Qu'est-ce qu'une garantie de soumission dans le contexte des marchés publics ?",
    "Dans quels cas l'autorité contractante peut-elle ne pas exiger cette garantie ?",
    "Qu'est-ce qu'une garantie de bonne exécution ?",
    "À quel moment cette garantie devient-elle obligatoire ?",
    "Quel est le lien entre l'exécution du marché et la responsabilité du titulaire ?",
    "Quelles sont les règles générales relatives à la souscription d'assurances par les titulaires ?",
    "Quelles assurances doivent être prises en charge par l'assistant à maîtrise d'ouvrage ?",
    "Quelles assurances doivent être prises en charge par le maître d'œuvre ?",
    "Le contrat de marché peut-il prévoir des pénalités ?",
    "Le contrat de maîtrise d'œuvre comporte-t-il une annexe sur la rémunération ?",
    "Comment le décret définit-il un achat public durable ?",
    "Quels sont les trois piliers du développement durable mentionnés dans la définition ?",
    "Comment le décret définit-il un achat public responsable ?",
    "À quel engagement renvoie la charte de l'éthique et de la commande publique responsable ?",
    "Quels objectifs environnementaux peuvent être intégrés dans un dossier d'appel à la concurrence ?",
    "Qu'est-ce qu'un circuit court local dans le décret ?",
    "Que signifie la prise en compte du cycle de vie dans un achat public ?",
    "Comment le texte favorise-t-il la participation des PME ?",
    "Quels types d'acteurs peuvent bénéficier d'un marché réservé ?",
    "Quelles catégories de PME sont définies dans le décret ?",
    "Quel est le rôle de l'ARCOP dans la commande publique ?",
    "Quel est le rôle de la DCMP ?",
    "Quelle différence fais-tu entre régulation et contrôle des marchés publics ?",
    "Quel texte fixe les règles d'organisation et de fonctionnement de l'ARCOP ?",
    "Quel texte crée la DCMP ?",
    "Quel organe est rattaché au ministère en charge des Finances pour la revue préalable ?",
    "Quel organe est compétent pour statuer sur les demandes liées à la passation et à l'exécution ?",
    "L'organe de recours non juridictionnel peut-il s'autosaisir ?",
    "En combien de jours ouvrables l'autorité de recours non juridictionnelle doit-elle rendre sa décision ?",
    "Quel effet a le silence de l'autorité de recours au-delà du délai ?",
    "Quel texte fixe le cadre juridique et institutionnel des PPP dans l'UEMOA ?",
    "Comment le décret PPP définit-il un partenariat public-privé ?",
    "Quelle différence existe entre PPP à paiement public et PPP à paiement par les usagers ?",
    "Qu'est-ce qu'une concession de service ?",
    "Qu'est-ce qu'une concession de travaux ?",
    "Qu'est-ce qu'une concession d'aménagement ?",
    "Quelles sont les grandes caractéristiques de la rémunération dans un PPP à paiement public ?",
    "Quelle part de risque doit être transférée dans un PPP à paiement par les usagers ?",
    "Dans quel cas une concession de service public est-elle qualifiée d'affermage ?",
    "Dans quel cas une concession de service public est-elle qualifiée de régie intéressée ?",
    "Quel est le rôle du Code des Obligations de l'Administration dans la commande publique ?",
    "Quelle directive UEMOA traite des procédures de passation, d'exécution et de règlement des marchés publics ?",
    "Quelle directive UEMOA traite du contrôle et de la régulation des marchés publics ?",
    "Quelle directive UEMOA traite de l'éthique et de la déontologie dans les marchés publics ?",
    "Quelle directive UEMOA traite de la maîtrise d'ouvrage publique déléguée ?",
    "Quel est l'objectif général de la directive sur la maîtrise d'ouvrage publique déléguée ?",
    "Pourquoi l'UEMOA a-t-elle adopté une directive sur les PPP ?",
    "Quelles considérations budgétaires justifient le recours aux PPP ?",
    "Quel texte encadre la stratégie d'encadrement des PPP dans l'UEMOA ?",
    "Quel lien le texte établit-il entre PPP et développement des PME ?",
    "Un marché public est-il toujours un contrat administratif ?",
    "Pourquoi certaines sociétés publiques échappent-elles au régime administratif classique ?",
    "Une autorité contractante peut-elle créer une procédure spécifique qui contredit le Code ?",
    "Un marché financé par des ressources extérieures est-il automatiquement hors du Code ?",
    "Un contrat de travail passé par une autorité contractante relève-t-il des marchés publics ?",
    "Peut-on cumuler une mission d'assistance à maîtrise d'ouvrage et une mission d'entrepreneur sur la même opération ?",
    "Peut-on cumuler une mission de maîtrise d'œuvre et celle d'entrepreneur sur la même opération ?",
    "Quelles sont les conséquences d'une violation du principe de publicité dans une procédure de passation ?",
    "Quels sont les cas où le recours à la concurrence peut être limité pour des raisons de sécurité nationale ?",
    "Comment distinguer un marché public classique d'un PPP dans le cadre sénégalais ?",
]

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "rag_test_results.json")
DELAY_BETWEEN_QUESTIONS = 2.5  # seconds — stay well under 30 req/min


def create_conversation(title: str) -> str | None:
    """Create a new conversation and return its ID."""
    resp = requests.post(
        f"{API_BASE}/chat/conversations",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        json={"title": title},
        timeout=15,
    )
    if resp.status_code == 201 or resp.status_code == 200:
        data = resp.json()
        return data.get("id")
    print(f"  [WARN] Failed to create conversation: {resp.status_code} {resp.text[:200]}")
    return None


def send_question_stream(conversation_id: str, question: str, top_k: int = 5) -> dict:
    """Send a question via SSE streaming and collect the full response."""
    url = f"{API_BASE}/chat/conversations/{conversation_id}/stream"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    body = {"question": question, "topK": top_k}

    result = {
        "question": question,
        "rewritten_question": None,
        "answer": "",
        "citations": [],
        "used_context": None,
        "conversation_id": conversation_id,
        "status": "pending",
        "error": None,
        "response_time_ms": 0,
        "token_count": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120)
        if resp.status_code != 200:
            result["status"] = "error"
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:300]}"
            result["response_time_ms"] = int((time.time() - start) * 1000)
            return result

        current_event = None
        for line in resp.iter_lines(decode_unicode=True):
            if line is None:
                continue
            line = line.strip()
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:"):
                data_str = line[5:].strip()
                if current_event == "rewritten":
                    try:
                        d = json.loads(data_str)
                        result["rewritten_question"] = d.get("rewritten_question", d.get("rewrittenQuestion"))
                    except json.JSONDecodeError:
                        pass
                elif current_event == "citations":
                    try:
                        d = json.loads(data_str)
                        result["citations"] = d.get("citations", [])
                        result["used_context"] = d.get("used_context", d.get("usedContext"))
                    except json.JSONDecodeError:
                        pass
                elif current_event == "token":
                    result["answer"] += data_str
                    result["token_count"] += 1
                elif current_event == "done":
                    pass  # stream finished

        result["status"] = "success"
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "Request timed out after 120s"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["response_time_ms"] = int((time.time() - start) * 1000)
    return result


def run_tests():
    """Run all 100 questions and save results."""
    print(f"=== Test RAG SenLegal — {len(QUESTIONS)} questions ===")
    print(f"API: {API_BASE}")
    print(f"Delay: {DELAY_BETWEEN_QUESTIONS}s between questions")
    print()

    results = []
    stats = {
        "total": len(QUESTIONS),
        "success": 0,
        "error": 0,
        "timeout": 0,
        "with_citations": 0,
        "without_context": 0,
        "avg_response_time_ms": 0,
        "avg_token_count": 0,
        "avg_citations_count": 0,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
    }

    conv_id = CONVERSATION_ID
    batch_size = 20
    questions_in_conv = 0

    for i, question in enumerate(QUESTIONS):
        # Create a new conversation every batch_size questions to keep context clean
        if i % batch_size == 0:
            batch_num = i // batch_size + 1
            new_id = create_conversation(f"Test RAG Batch {batch_num} — {datetime.now().strftime('%H:%M')}")
            if new_id:
                conv_id = new_id
                questions_in_conv = 0
                print(f"  [NEW CONV] {conv_id}")
            elif i == 0:
                print(f"  [INFO] Using provided conversation: {conv_id}")

        q_num = i + 1
        short_q = question[:70] + ("..." if len(question) > 70 else "")
        print(f"[{q_num:3d}/100] {short_q}")

        result = send_question_stream(conv_id, question)
        result["question_number"] = q_num
        results.append(result)
        questions_in_conv += 1

        if result["status"] == "success":
            stats["success"] += 1
            if result["citations"]:
                stats["with_citations"] += 1
            if result["used_context"] is False:
                stats["without_context"] += 1
            answer_preview = result["answer"][:80].replace("\n", " ")
            print(f"         ✓ {result['response_time_ms']}ms | {result['token_count']} tokens | {len(result['citations'])} citations")
            print(f"         → {answer_preview}...")
        elif result["status"] == "error":
            stats["error"] += 1
            print(f"         ✗ ERROR: {result['error'][:100]}")
            if "429" in str(result.get("error", "")):
                print("         ⏳ Throttled — waiting 30s...")
                time.sleep(30)
            elif "403" in str(result.get("error", "")) and "Quota" in str(result.get("error", "")):
                print("         ⛔ Quota limit reached! Stopping...")
                break
        else:
            stats["timeout"] += 1
            print(f"         ⏰ TIMEOUT")

        # Save intermediate results
        if q_num % 10 == 0:
            _save(results, stats)

        if i < len(QUESTIONS) - 1:
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    # Final stats
    completed = [r for r in results if r["status"] == "success"]
    if completed:
        stats["avg_response_time_ms"] = round(sum(r["response_time_ms"] for r in completed) / len(completed))
        stats["avg_token_count"] = round(sum(r["token_count"] for r in completed) / len(completed))
        stats["avg_citations_count"] = round(sum(len(r["citations"]) for r in completed) / len(completed), 1)

    stats["end_time"] = datetime.utcnow().isoformat()
    stats["completed"] = len(results)
    _save(results, stats)
    _print_summary(stats)


def _save(results, stats):
    data = {"stats": stats, "results": results}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Saved → {OUTPUT_FILE}")


def _print_summary(stats):
    print()
    print("=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    print(f"  Questions posées :      {stats.get('completed', stats['total'])}/{stats['total']}")
    print(f"  Réponses réussies :     {stats['success']}")
    print(f"  Erreurs :               {stats['error']}")
    print(f"  Timeouts :              {stats['timeout']}")
    print(f"  Avec citations :        {stats['with_citations']}")
    print(f"  Sans contexte (refus) : {stats['without_context']}")
    print(f"  Temps moyen :           {stats['avg_response_time_ms']}ms")
    print(f"  Tokens moyen :          {stats['avg_token_count']}")
    print(f"  Citations moyen :       {stats['avg_citations_count']}")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
