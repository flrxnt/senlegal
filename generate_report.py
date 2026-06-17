#!/usr/bin/env python3
"""Generate academic PDF report for SenLegal project."""

from fpdf import FPDF
import os

FONT_DIR = "/System/Library/Fonts/Supplemental/"
FONT_FILE = os.path.join(FONT_DIR, "Arial Unicode.ttf")


class AcademicPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("ArialUni", "", FONT_FILE, uni=True)
        self.add_font("ArialUni", "B", FONT_FILE, uni=True)
        self.add_font("ArialUni", "I", FONT_FILE, uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font("ArialUni", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "SenL\u00e9gal \u2014 Rapport Technique", 0, 0, "L")
            self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", 0, 1, "R")
            self.line(10, 14, 200, 14)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("ArialUni", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Projet IA \u2014 Juin 2026 \u2014 Encadrant : Dr KEITA", 0, 0, "C")

    def title_page(self):
        self.add_page()
        self.ln(50)
        self.set_font("ArialUni", "B", 28)
        self.set_text_color(0, 133, 63)
        self.cell(0, 14, "SenL\u00e9gal", 0, 1, "C")
        self.ln(6)
        self.set_font("ArialUni", "", 14)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, "Assistant Juridique IA sp\u00e9cialis\u00e9 dans le", 0, 1, "C")
        self.cell(0, 8, "Code des March\u00e9s Publics du S\u00e9n\u00e9gal", 0, 1, "C")
        self.ln(10)
        self.set_draw_color(0, 133, 63)
        self.set_line_width(0.8)
        self.line(70, self.get_y(), 140, self.get_y())
        self.ln(12)
        self.set_font("ArialUni", "", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 7, "Rapport Technique", 0, 1, "C")
        self.cell(0, 7, "Projet Intelligence Artificielle \u2014 Juin 2026", 0, 1, "C")
        self.ln(16)
        self.set_font("ArialUni", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, "Encadrant : Dr KEITA", 0, 1, "C")
        self.ln(4)
        self.set_font("ArialUni", "", 10)
        authors = [
            "Aboubakar ABDOULAYE",
            "Samuel AISSI",
            "T\u00e9kiyath AMOUSSA",
            "Leslie SAWADOGO",
        ]
        for a in authors:
            self.cell(0, 6, a, 0, 1, "C")

    def section_title(self, title):
        self.ln(8)
        self.set_font("ArialUni", "B", 14)
        self.set_text_color(0, 133, 63)
        self.cell(0, 10, title, 0, 1)
        self.set_draw_color(0, 133, 63)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.ln(4)
        self.set_font("ArialUni", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, title, 0, 1)
        self.ln(2)

    def body_text(self, text):
        self.set_font("ArialUni", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("ArialUni", "", 10)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.cell(5, 5.5, "\u2022")
        self.multi_cell(185, 5.5, text)
        self.set_x(x)

    def code_block(self, text):
        self.set_font("ArialUni", "", 8)
        self.set_fill_color(240, 243, 245)
        self.set_text_color(30, 30, 30)
        y = self.get_y()
        self.rect(10, y, 190, 5 * text.count("\n") + 12, "F")
        self.ln(3)
        for line in text.split("\n"):
            self.cell(6)
            self.cell(0, 4.5, line, 0, 1)
        self.ln(4)

    def table(self, headers, rows):
        self.set_font("ArialUni", "B", 9)
        self.set_fill_color(0, 133, 63)
        self.set_text_color(255, 255, 255)
        col_w = 190 / len(headers)
        for h in headers:
            self.cell(col_w, 7, h, 1, 0, "C", True)
        self.ln()
        self.set_font("ArialUni", "", 9)
        self.set_text_color(50, 50, 50)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(245, 250, 247)
            else:
                self.set_fill_color(255, 255, 255)
            for cell in row:
                self.cell(col_w, 6, cell, 1, 0, "L", True)
            self.ln()
            fill = not fill
        self.ln(4)


def generate():
    pdf = AcademicPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Title page
    pdf.title_page()

    # 1. Introduction
    pdf.add_page()
    pdf.section_title("1. Introduction")
    pdf.body_text(
        "SenL\u00e9gal est un assistant juridique bas\u00e9 sur "
        "l'intelligence artificielle, sp\u00e9cialement con\u00e7u pour le droit de la "
        "commande publique au S\u00e9n\u00e9gal. Le syst\u00e8me utilise une architecture "
        "RAG (Retrieval-Augmented Generation) pour fournir des r\u00e9ponses pr\u00e9cises "
        "et cit\u00e9es, ancr\u00e9es sur les textes juridiques officiels."
    )
    pdf.body_text(
        "La probl\u00e9matique adress\u00e9e est double : d'une part, les textes juridiques "
        "s\u00e9n\u00e9galais sont volumineux et complexes (Code des March\u00e9s Publics, "
        "Recueil des Textes Juridiques 2023, d\u00e9cisions ARCOP/CRD). D'autre part, les "
        "mod\u00e8les de langage g\u00e9n\u00e9ralistes hallucinent syst\u00e9matiquement sur "
        "le droit sp\u00e9cifique s\u00e9n\u00e9galais qui n'est pas repr\u00e9sent\u00e9 dans "
        "leurs donn\u00e9es d'entra\u00eenement."
    )
    pdf.sub_title("Objectifs")
    pdf.bullet("Fournir un acc\u00e8s instantan\u00e9 aux textes juridiques via langage naturel")
    pdf.bullet("Garantir la tra\u00e7abilit\u00e9 (citations article par article)")
    pdf.bullet("\u00c9liminer les hallucinations gr\u00e2ce \u00e0 5 couches de protection")
    pdf.bullet("D\u00e9ployer une solution compl\u00e8te et production-ready")

    # 2. Sources Juridiques
    pdf.add_page()
    pdf.section_title("2. Sources Juridiques Index\u00e9es")
    pdf.body_text(
        "Le syst\u00e8me indexe l'ensemble du corpus juridique relatif \u00e0 la commande "
        "publique s\u00e9n\u00e9galaise. Les documents sont trait\u00e9s par un pipeline "
        "d'ingestion sp\u00e9cialis\u00e9 qui pr\u00e9serve la structure article par article."
    )
    pdf.table(
        ["Source", "Contenu", "Type"],
        [
            ["D\u00e9cret 2022-2295", "Code des March\u00e9s Publics", "L\u00e9gislation"],
            ["Recueil Vol. 1 (2023)", "Textes commande publique", "Compilation"],
            ["Recueil Vol. 2 (2023)", "Textes compl\u00e9mentaires", "Compilation"],
            ["D\u00e9cisions ARCOP/CRD", "Jurisprudence (2026)", "Jurisprudence"],
        ],
    )
    pdf.sub_title("Glossaire juridique int\u00e9gr\u00e9")
    pdf.body_text(
        "Un glossaire sp\u00e9cifique au droit des march\u00e9s publics s\u00e9n\u00e9galais "
        "est utilis\u00e9 pour l'expansion automatique des requ\u00eates. Il couvre les "
        "acronymes suivants :"
    )
    pdf.bullet("ARCOP \u2014 Autorit\u00e9 de R\u00e9gulation de la Commande Publique")
    pdf.bullet("CRD \u2014 Comit\u00e9 de R\u00e8glement des Diff\u00e9rends")
    pdf.bullet("DRP \u2014 Demande de R\u00e8glement Pr\u00e9alable")
    pdf.bullet("AOO \u2014 Appel d'Offres Ouvert")
    pdf.bullet("DCE \u2014 Dossier de Consultation des Entreprises")
    pdf.bullet("DRPCM \u2014 Direction de la R\u00e9glementation et des March\u00e9s Publics")
    pdf.bullet("DAO \u2014 Dossier d'Appel d'Offres")

    # 3. Architecture
    pdf.add_page()
    pdf.section_title("3. Architecture du Syst\u00e8me")
    pdf.body_text(
        "SenL\u00e9gal adopte une architecture microservices compos\u00e9e de 4 services "
        "applicatifs et 3 services d'infrastructure, orchestr\u00e9s via Docker Compose."
    )
    pdf.sub_title("Services applicatifs")
    pdf.table(
        ["Service", "Technologie", "Port", "R\u00f4le"],
        [
            ["Frontend", "Nuxt 4 + Vue 3 + Tailwind", "3000", "Interface utilisateur"],
            ["Backend", "NestJS 11 + Prisma 7", "3001", "API Gateway + logique m\u00e9tier"],
            ["Service IA", "FastAPI + Python 3.11", "8001", "RAG + embeddings + LLM"],
            ["Caddy", "Caddy Server", "443", "Reverse proxy + TLS"],
        ],
    )
    pdf.sub_title("Services d'infrastructure")
    pdf.table(
        ["Service", "Technologie", "Port", "R\u00f4le"],
        [
            ["PostgreSQL", "PostgreSQL 16", "5433", "Base relationnelle"],
            ["ChromaDB", "ChromaDB 0.5", "8002", "Base vectorielle"],
            ["MinIO", "MinIO (S3-compatible)", "9000", "Stockage objets"],
        ],
    )
    pdf.sub_title("Flux de donn\u00e9es")
    pdf.body_text(
        "Le frontend communique exclusivement avec le backend NestJS via JWT. "
        "Le backend proxifie les requ\u00eates IA vers FastAPI en utilisant un token admin. "
        "Le service IA acc\u00e8de \u00e0 ChromaDB pour la recherche vectorielle et \u00e0 "
        "Ollama Cloud pour la g\u00e9n\u00e9ration LLM. Le frontend n'a jamais acc\u00e8s "
        "direct au service IA."
    )

    # 4. Modele d'Embedding
    pdf.add_page()
    pdf.section_title("4. Mod\u00e8le d'Embedding")
    pdf.sub_title("intfloat/multilingual-e5-small")
    pdf.body_text(
        "Le mod\u00e8le d'embedding choisi est multilingual-e5-small de la famille E5 "
        "(Embeddings from bidirectional Encoder representations). Ce mod\u00e8le est "
        "sp\u00e9cifiquement optimis\u00e9 pour les langues multiples dont le fran\u00e7ais, "
        "ce qui est essentiel pour un corpus juridique francophone."
    )
    pdf.table(
        ["Propri\u00e9t\u00e9", "Valeur"],
        [
            ["Dimensions", "384"],
            ["Param\u00e8tres", "~33M"],
            ["Langues", "100+ (fran\u00e7ais natif)"],
            ["Pr\u00e9fixe query", "query: <texte>"],
            ["Pr\u00e9fixe passage", "passage: <texte>"],
            ["M\u00e9trique", "Similarit\u00e9 cosinus"],
            ["GPU requis", "Non (CPU compatible)"],
        ],
    )
    pdf.sub_title("Avantages pour le projet")
    pdf.bullet("Support natif du fran\u00e7ais \u2014 crucial pour le corpus juridique")
    pdf.bullet("L\u00e9ger et rapide \u2014 inf\u00e9rence CPU en temps r\u00e9el")
    pdf.bullet("Pr\u00e9fixage asymetrique query/passage \u2014 am\u00e9liore la pertinence")
    pdf.bullet("Open-source \u2014 disponible sur HuggingFace sans cl\u00e9 API")

    # 5. Pipeline Ingestion
    pdf.add_page()
    pdf.section_title("5. Pipeline d'Ingestion")
    pdf.body_text(
        "Le pipeline d'ingestion transforme les documents PDF juridiques en vecteurs "
        "interrogeables dans ChromaDB. Il est con\u00e7u pour pr\u00e9server la granularit\u00e9 "
        "article par article des textes de loi."
    )
    pdf.sub_title("\u00c9tape 1 : Parsing PDF")
    pdf.body_text(
        "Utilisation de pdfplumber pour l'extraction textuelle. Normalisation des ligatures "
        "typographiques (fi, fl, ff) et r\u00e9paration des c\u00e9sures en fin de ligne."
    )
    pdf.sub_title("\u00c9tape 2 : Chunking par article")
    pdf.body_text(
        "D\u00e9coupage intelligent bas\u00e9 sur des expressions r\u00e9guli\u00e8res "
        "d\u00e9tectant les en-t\u00eates d'articles juridiques : Article 53, Art. premier, "
        "Article 7-1, etc. Les chunks d\u00e9passant 1500 caract\u00e8res sont sous-d\u00e9coup\u00e9s."
    )
    pdf.sub_title("\u00c9tape 3 : Enrichissement m\u00e9tadonn\u00e9es")
    pdf.body_text(
        "Chaque chunk est annot\u00e9 avec : source (nom du document), num\u00e9ro d'article, "
        "et pour les d\u00e9cisions ARCOP : num\u00e9ro de d\u00e9cision, date, parties impliqu\u00e9es."
    )
    pdf.sub_title("\u00c9tape 4 : Embedding et stockage")
    pdf.body_text(
        "Vectorisation par batch de 32 via multilingual-e5-small avec pr\u00e9fixe 'passage:'. "
        "Upsert dans ChromaDB (collection senlegal_v1) avec index HNSW cosine."
    )

    # 6. Pipeline Recherche
    pdf.add_page()
    pdf.section_title("6. Pipeline de Recherche & G\u00e9n\u00e9ration")
    pdf.body_text(
        "Le pipeline de recherche est compos\u00e9 de 5 \u00e9tapes successives qui "
        "transforment la question utilisateur en r\u00e9ponse cit\u00e9e et valid\u00e9e."
    )
    pdf.sub_title("\u00c9tape 1 : Query Rewriting")
    pdf.body_text(
        "Le LLM (Gemma 4 31B) corrige l'orthographe et la ponctuation de la requ\u00eate "
        "sans en modifier le sens. Cela am\u00e9liore la qualit\u00e9 de l'embedding."
    )
    pdf.sub_title("\u00c9tape 2 : Keyword Extraction")
    pdf.body_text(
        "Extraction automatique des termes juridiques cl\u00e9s, synonymes et acronymes "
        "via le LLM. Exemple : 'march\u00e9s publics' \u2192 'commande publique', 'AOO', "
        "'appel d'offres ouvert'."
    )
    pdf.sub_title("\u00c9tape 3 : Multi-Query Retrieval")
    pdf.body_text(
        "Deux requ\u00eates sont envoy\u00e9es \u00e0 ChromaDB : la requ\u00eate originale "
        "et la requ\u00eate enrichie (keywords + glossaire). Les r\u00e9sultats sont fusionn\u00e9s "
        "par meilleur score. Seuil minimum : 0.35 de similarit\u00e9 cosinus."
    )
    pdf.sub_title("\u00c9tape 4 : G\u00e9n\u00e9ration LLM")
    pdf.body_text(
        "Le LLM re\u00e7oit un prompt strict avec les chunks r\u00e9cup\u00e9r\u00e9s comme "
        "contexte. Il doit obligatoirement citer ses sources au format "
        "[Article X \u2014 Document]. Temperature = 0.1, repeat_penalty = 1.1."
    )
    pdf.sub_title("\u00c9tape 5 : Post-validation")
    pdf.body_text(
        "V\u00e9rification que chaque citation [Article X \u2014 Document] existe "
        "effectivement dans le contexte r\u00e9cup\u00e9r\u00e9. Si la validation \u00e9choue "
        "apr\u00e8s 1 retry, un fallback d\u00e9terministe (extrait brut du meilleur chunk) "
        "est renvoy\u00e9 \u00e0 la place."
    )

    # 7. Anti-Hallucination
    pdf.add_page()
    pdf.section_title("7. Syst\u00e8me Anti-Hallucination")
    pdf.body_text(
        "Le syst\u00e8me anti-hallucination est le coeur de la fiabilit\u00e9 de SenL\u00e9gal. "
        "Il se compose de 5 couches de protection ind\u00e9pendantes et compl\u00e9mentaires."
    )
    pdf.table(
        ["Couche", "M\u00e9canisme", "Action"],
        [
            ["1", "Score minimum (0.35)", "Refus sans appel LLM si aucun chunk pertinent"],
            ["2", "Prompt strict", "Interdiction connaissances externes"],
            ["3", "Few-shot examples", "Exemples in-scope vs hors-sujet"],
            ["4", "Post-validation", "V\u00e9rif. format citations vs contexte"],
            ["5", "Fallback d\u00e9terministe", "Extrait brut si g\u00e9n\u00e9ration invalide"],
        ],
    )
    pdf.sub_title("Param\u00e8tres LLM")
    pdf.bullet("Mod\u00e8le : Gemma 4 31B via Ollama Cloud")
    pdf.bullet("Temperature : 0.1 (tr\u00e8s conservateur)")
    pdf.bullet("Repeat penalty : 1.1")
    pdf.bullet("Streaming : SSE (Server-Sent Events)")
    pdf.sub_title("Principe de refus")
    pdf.body_text(
        "Quand le syst\u00e8me ne trouve aucun chunk avec un score sup\u00e9rieur \u00e0 0.35, "
        "il refuse explicitement de r\u00e9pondre avec un message standardis\u00e9 expliquant "
        "que la question est hors du p\u00e9rim\u00e8tre de sa base de connaissances. "
        "Aucun appel LLM n'est effectu\u00e9 dans ce cas."
    )

    # 8. Stack Technique
    pdf.add_page()
    pdf.section_title("8. Stack Technique")
    pdf.sub_title("Backend (TypeScript)")
    pdf.table(
        ["Technologie", "Version", "R\u00f4le"],
        [
            ["NestJS", "11", "Framework API + injection de d\u00e9pendances"],
            ["Prisma", "7", "ORM + migrations + type safety"],
            ["PostgreSQL", "16", "Base relationnelle principale"],
            ["Passport", "JWT HS256", "Authentification + guards RBAC"],
            ["MinIO", "S3-compatible", "Stockage fichiers (documents, avatars)"],
            ["Bun", "1.x", "Runtime JavaScript rapide"],
            ["Nodemailer", "-", "Emails transactionnels"],
        ],
    )
    pdf.sub_title("Service IA (Python)")
    pdf.table(
        ["Technologie", "Version", "R\u00f4le"],
        [
            ["FastAPI", "0.115+", "Framework web async"],
            ["sentence-transformers", "3.x", "Embeddings E5 multilingue"],
            ["ChromaDB", "0.5.20", "Base vectorielle HNSW"],
            ["Ollama (Cloud)", "-", "LLM Gemma 4 31B"],
            ["pdfplumber", "-", "Parsing PDF juridiques"],
            ["Python", "3.11+", "Runtime"],
        ],
    )
    pdf.sub_title("Frontend (TypeScript)")
    pdf.table(
        ["Technologie", "Version", "R\u00f4le"],
        [
            ["Nuxt", "4", "Framework Vue full-stack SSR"],
            ["Vue.js", "3.5", "UI r\u00e9active composants"],
            ["Tailwind CSS", "4", "Styling utilitaire"],
            ["Pinia", "2", "State management"],
            ["VeeValidate + Zod", "-", "Validation formulaires"],
            ["Motion-V", "-", "Animations"],
        ],
    )

    # 9. Fonctionnalites
    pdf.add_page()
    pdf.section_title("9. Fonctionnalit\u00e9s")
    pdf.sub_title("Interface utilisateur")
    pdf.bullet("Inscription / connexion / r\u00e9cup\u00e9ration mot de passe")
    pdf.bullet("Chat IA avec streaming SSE et citations cliquables")
    pdf.bullet("Historique et gestion des conversations (titre, \u00e9pingler, archiver)")
    pdf.bullet("Coffre-fort documents personnels (upload/download via URLs pr\u00e9sign\u00e9es)")
    pdf.sub_title("Interface administrateur")
    pdf.bullet("Gestion utilisateurs (r\u00f4les USER/ADMIN, activation)")
    pdf.bullet("Upload de nouveaux PDF \u2192 ingestion asynchrone dans le RAG")
    pdf.bullet("Consultation de toutes les conversations")
    pdf.bullet("Logs d'erreurs serveur (HTTP \u2265 500)")
    pdf.bullet("Backup complet (base + fichiers) et restauration")
    pdf.bullet("Tableau analytique d'\u00e9v\u00e9nements")
    pdf.sub_title("S\u00e9curit\u00e9")
    pdf.bullet("JWT HS256 + guards RBAC (USER / ADMIN)")
    pdf.bullet("Throttler global : 120 req/min, plus strict sur auth/chat")
    pdf.bullet("Bcrypt 12 rounds pour les mots de passe")
    pdf.bullet("Token admin partag\u00e9 backend \u2194 service IA")
    pdf.bullet("Filtrage erreurs 5xx + logging")

    # 10. Deploiement
    pdf.add_page()
    pdf.section_title("10. D\u00e9ploiement")
    pdf.body_text(
        "Le projet est enti\u00e8rement containeris\u00e9 avec Docker et supporte "
        "3 environnements de d\u00e9ploiement."
    )
    pdf.table(
        ["Environnement", "Fichier", "Particularit\u00e9s"],
        [
            ["D\u00e9veloppement", "docker-compose.yml", "Hot-reload, Mailpit, ports expos\u00e9s"],
            ["Production", "docker-compose.prod.yml", "Build GitHub, Caddy TLS, 3 domaines"],
            ["Coolify", "docker-compose.coolify.yml", "Variables magiques, Traefik"],
        ],
    )
    pdf.sub_title("Containers (7 au total)")
    pdf.bullet("frontend \u2014 Nuxt SSR build")
    pdf.bullet("backend \u2014 NestJS + seed automatique au d\u00e9marrage")
    pdf.bullet("ai \u2014 FastAPI + mod\u00e8le E5 pr\u00e9-t\u00e9l\u00e9charg\u00e9 dans l'image")
    pdf.bullet("postgres \u2014 PostgreSQL 16 avec volumes persistants")
    pdf.bullet("chromadb \u2014 ChromaDB avec persistance")
    pdf.bullet("minio \u2014 Stockage S3-compatible")
    pdf.bullet("caddy \u2014 Reverse proxy avec certificats TLS auto")

    # 11. Tests RAG — 100 Questions
    pdf.add_page()
    pdf.section_title("11. Tests RAG \u2014 100 Questions")
    pdf.body_text(
        "Le système RAG a été soumis à un test exhaustif de 100 questions "
        "couvrant 10 catégories thématiques du droit de la commande publique "
        "sénégalais. Chaque question a été envoyée via l'API de streaming SSE "
        "et la réponse complète (texte, citations, scores, temps) a été collectée "
        "et analysée automatiquement."
    )
    pdf.sub_title("Résultats globaux")
    pdf.table(
        ["Métrique", "Valeur"],
        [
            ["Questions posées", "100"],
            ["Succès API", "100/100 (100%)"],
            ["Réponses complètes", "91/100 (91%)"],
            ["Réponses partielles", "2/100 (2%)"],
            ["Refus (hors périmètre)", "7/100 (7%)"],
            ["Temps médian", "7.3 secondes"],
            ["Temps moyen", "13.1 secondes"],
            ["P95", "42.5 secondes"],
            ["Citations par réponse", "5.0 en moyenne"],
        ],
    )

    # Chart: quality donut
    chart_dir = os.path.join(os.path.dirname(__file__), "rag_charts")
    chart1 = os.path.join(chart_dir, "01_quality_donut.png")
    if os.path.exists(chart1):
        pdf.add_page()
        pdf.sub_title("Qualité globale des réponses")
        img_w = 130
        x = (210 - img_w) / 2
        pdf.image(chart1, x=x, w=img_w)
        pdf.ln(4)

    pdf.sub_title("Résultats par catégorie thématique")
    pdf.table(
        ["Catégorie", "Répondu", "Partiel", "Refusé", "Taux", "Temps moy."],
        [
            ["Cadre juridique général", "10", "0", "0", "100%", "18.4s"],
            ["Définitions", "10", "0", "0", "100%", "5.9s"],
            ["Champ d'application", "9", "0", "1", "90%", "15.8s"],
            ["Procédures de passation", "10", "0", "0", "100%", "11.6s"],
            ["Garanties et exécution", "9", "0", "1", "90%", "10.2s"],
            ["Achats durables et PME", "9", "0", "1", "90%", "7.5s"],
            ["Organes (ARCOP/DCMP)", "10", "0", "0", "100%", "8.9s"],
            ["PPP et concessions", "8", "1", "1", "80%", "17.3s"],
            ["Directives UEMOA", "8", "1", "1", "80%", "24.5s"],
            ["Questions transversales", "8", "0", "2", "80%", "11.1s"],
        ],
    )

    # Chart: category quality
    chart4 = os.path.join(chart_dir, "04_category_quality.png")
    if os.path.exists(chart4):
        pdf.add_page()
        pdf.sub_title("Qualité par catégorie thématique")
        pdf.image(chart4, x=10, w=190)
        pdf.ln(4)

    # Chart: response time histogram
    chart2 = os.path.join(chart_dir, "02_response_time_hist.png")
    if os.path.exists(chart2):
        pdf.sub_title("Distribution des temps de réponse")
        pdf.image(chart2, x=10, w=190)
        pdf.ln(4)

    # Chart: similarity scores
    chart7 = os.path.join(chart_dir, "07_similarity_scores.png")
    if os.path.exists(chart7):
        pdf.add_page()
        pdf.sub_title("Scores de similarité des citations")
        pdf.image(chart7, x=10, w=190)
        pdf.ln(4)

    # Chart: score distribution
    chart8 = os.path.join(chart_dir, "08_score_distribution.png")
    if os.path.exists(chart8):
        pdf.sub_title("Distribution des scores de similarité")
        pdf.image(chart8, x=10, w=190)
        pdf.ln(4)

    # Chart: response time scatter
    chart3 = os.path.join(chart_dir, "03_response_time_scatter.png")
    if os.path.exists(chart3):
        pdf.add_page()
        pdf.sub_title("Temps de réponse par question")
        pdf.image(chart3, x=10, w=190)
        pdf.ln(4)

    # Chart: tokens
    chart6 = os.path.join(chart_dir, "06_tokens_per_question.png")
    if os.path.exists(chart6):
        pdf.sub_title("Tokens générés par réponse")
        pdf.image(chart6, x=10, w=190)
        pdf.ln(4)

    # Chart: top sources
    chart9 = os.path.join(chart_dir, "09_top_sources.png")
    if os.path.exists(chart9):
        pdf.add_page()
        pdf.sub_title("Sources documentaires les plus citées")
        pdf.image(chart9, x=10, w=190)
        pdf.ln(4)

    # Chart: category time
    chart5 = os.path.join(chart_dir, "05_category_time.png")
    if os.path.exists(chart5):
        pdf.sub_title("Temps moyen par catégorie")
        pdf.image(chart5, x=10, w=190)
        pdf.ln(4)

    # Questions refusées
    pdf.add_page()
    pdf.sub_title("Questions refusées et partielles (9/100)")
    pdf.body_text(
        "Le système anti-hallucination fonctionne correctement : les refus "
        "correspondent à des informations effectivement absentes du corpus "
        "indexé. Le RAG préfère refuser plutôt qu'inventer une réponse."
    )
    pdf.table(
        ["Q#", "Question", "Statut"],
        [
            ["28", "Missions diplomatiques à l'étranger", "Refusé"],
            ["48", "Assurances du maître d'œuvre", "Refusé"],
            ["54", "Charte de l'éthique", "Refusé"],
            ["73", "PPP paiement public vs usagers", "Partiel"],
            ["76", "Concession d'aménagement", "Refusé"],
            ["81", "Code des Obligations de l'Admin.", "Refusé"],
            ["88", "Considérations budgétaires PPP", "Partiel"],
            ["93", "Procédure contredisant le Code", "Refusé"],
            ["95", "Contrat de travail vs marché", "Refusé"],
        ],
    )
    pdf.body_text(
        "Analyse : Les catégories « Cadre juridique », « Définitions », "
        "« Procédures » et « Organes ARCOP/DCMP » obtiennent un score "
        "parfait de 100%. Les refus se concentrent sur les PPP (concepts "
        "non détaillés dans le corpus), les directives UEMOA et les "
        "questions transversales nécessitant des textes non indexés (COA, "
        "charte d'éthique, concession d'aménagement)."
    )

    # Summary table chart
    chart10 = os.path.join(chart_dir, "10_summary_table.png")
    if os.path.exists(chart10):
        pdf.add_page()
        pdf.sub_title("Tableau récapitulatif")
        pdf.image(chart10, x=10, w=190)
        pdf.ln(4)

    # 12. Conclusion
    pdf.add_page()
    pdf.section_title("12. Conclusion & Perspectives")
    pdf.body_text(
        "SenLégal démontre la faisabilité d'un assistant juridique IA fiable "
        "et spécialisé, adapté au contexte ouest-africain. L'architecture RAG "
        "multi-couches, combinée à un système anti-hallucination en 5 niveaux, "
        "garantit des réponses toujours ancrées dans les textes officiels."
    )
    pdf.body_text(
        "Les tests exhaustifs sur 100 questions couvrant l'ensemble du droit "
        "de la commande publique sénégalais confirment un taux de réponse de "
        "91% avec zéro hallucination. Les 9 questions non répondues correspondent "
        "à des informations effectivement absentes du corpus indexé, validant "
        "ainsi le système anti-hallucination."
    )
    pdf.body_text(
        "L'architecture microservices containerisée permet un "
        "déploiement simple et une évolutivité horizontale."
    )
    pdf.sub_title("Perspectives")
    pdf.bullet("Extension à d'autres domaines du droit sénégalais (OHADA, droit du travail)")
    pdf.bullet("Fine-tuning d'un LLM local sur le corpus juridique francophone")
    pdf.bullet("Application mobile avec support vocal (Wolof + Français)")
    pdf.bullet("Partenariats institutionnels avec ARCOP et l'Ordre des Avocats")
    pdf.bullet("Cross-encoder pour le re-ranking des résultats de recherche")
    pdf.bullet("Indexation automatique des nouvelles décisions ARCOP (flux RSS)")
    pdf.bullet("Enrichir le corpus pour couvrir les 9 questions actuellement refusées")

    # Save
    output_path = os.path.join(os.path.dirname(__file__), "SenLegal_Rapport_Technique.pdf")
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    generate()
