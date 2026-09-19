"""Primera corrida real del radar de temas — 15-sep-2026.

Datos reales, no sintéticos: 28 vacantes jurídicas activas en México
(Cancún, Quintana Roo + Ciudad de México), capturadas vía el conector
Indeed en esta sesión el 15-sep-2026. Búsquedas: "abogado" (Cancún),
"abogado laboral" / "abogado inmobiliario" / "oficial de cumplimiento PLD"
/ "abogado protección de datos" (CDMX). Cada título y URL es real y
verificable — ver `POSTINGS` abajo.

    python3 demo_vacancy_radar.py     (desde el directorio visual/)

Registra la corrida en `corpus/radar-vacantes-log.json` (append-only) y
escribe el informe legible en `docs/radar-vacantes-2026-09-15.md`. No
modifica materias-seed-v1.json, el corpus, ni ningún banco de contenido —
todo lo que produce es PROPUESTA para revisión humana.
"""

from pathlib import Path

import vacancy_radar as vr

# (titulo, empresa, url) — reales, capturados 15-sep-2026 vía Indeed MX.
POSTINGS = [
    ("Abogado Litigante", "Legal & Fixer", "https://to.indeed.com/aaj8ygmxl4yn"),
    ("ABOGADO/A LITIGANTE – MATERIA PENAL Y CIVIL", "Servicios en recursos humanos.",
     "https://to.indeed.com/aamsgr4zy9yr"),
    ("Legal Escalations Specialist", "Rockpoint Legal Funding",
     "https://to.indeed.com/aaddvcpghcvq"),
    ("Legal Assistant (LATAM - Remote)", "StaffScout", "https://to.indeed.com/aa82fsqy9xm9"),
    ("Remote Family Law Paralegal", "Aw Labor Solutions", "https://to.indeed.com/aamdrjkvzhwf"),
    ("Abogados Senior con Amplia Experiencia", "MURPHY LAW CONSULTING",
     "https://to.indeed.com/aaqxb98t8fwn"),
    ("Abogado Corporativo / Notarial", "INIX", "https://to.indeed.com/aawph4fygqs2"),
    ("Abogado Corporativo SR", "Constructora GB", "https://to.indeed.com/aa7pk6sz88lq"),
    ("Abogado Corporativo", "Shineray mexico", "https://to.indeed.com/aa2jtrvlcvhj"),
    ("Abogado Líder Corporativo y Litigios", "PCM RECLICLADORA",
     "https://to.indeed.com/aayjj9kz8lkx"),
    ("ABOGADO OUTSORCING Y REPSE", "Centro telecom", "https://to.indeed.com/aacgdn44gdmy"),
    ("ABOGADO SR INFRAESTRUCTURA", "C3ntro Telecom", "https://to.indeed.com/aarjlwj2hz72"),
    ("Abogado Sr. Legal Inmobiliario", "Cobalto Talent", "https://to.indeed.com/aagdlckjgfbj"),
    ("Abogado Inmobiliario Transaccional", "OPERADORA DE HOTELES NORTE 19 S.A DE C.V",
     "https://to.indeed.com/aafb98dwsqmk"),
    ("Gerente de Gestión Urbana, Normatividad y Licencias", "WorkBox",
     "https://to.indeed.com/aaqdxqkcktvq"),
    ("Director de Expansión y Adquisición de Terrenos", "WorkBox",
     "https://to.indeed.com/aa7qp7dns74t"),
    ("Oficial de Cumplimiento", "MILLENIALS INNOVATIONS", "https://to.indeed.com/aan8c2tfjg4f"),
    ("Oficial de Cumplimiento y Normatividad", "CREDITO MAESTRO",
     "https://to.indeed.com/aamf4k2692zd"),
    ("Oficial de cumplimiento PLD/FT", "Alianza Nacional Multimarca",
     "https://to.indeed.com/aanzrvkkvsh4"),
    ("ANALISTA DE PLD Y CUMPLIMIENTO", "World Vision International",
     "https://to.indeed.com/aa8yy2kvrpnd"),
    ("Head PLD/AML | Servicios Financieros", "Global Executive",
     "https://to.indeed.com/aamw7gpqlbfg"),
    ("Money Laundering Reporting Officer (MLRO), Mexico - Global Payment", "TikTok",
     "https://to.indeed.com/aarlddbmkxr6"),
    ("Senior Regulatory Compliance Manager, Mexico", "Airwallex",
     "https://to.indeed.com/aa4zsfh2yydd"),
    ("Abogado/a Laboral Corporativo", "ROCINANTE REDES MX",
     "https://to.indeed.com/aamzctxl67v4"),
    ("Abogado Fiscalista", "Biz Group", "https://to.indeed.com/aakwp6krx26k"),
    ("Abogado contratos - Publicación vencida", "Grupo Sura",
     "https://to.indeed.com/aatqblrljdv7"),
    ("ABOGADO SR. DE CUMPLIMIENTO", "Amedirh TALENTO", "https://to.indeed.com/aaf6264d9gn6"),
    ("Facilitador de proyecto especial en Protección - Villahermosa - Tabasco",
     "World Vision International", "https://to.indeed.com/aazyd97yxxy7"),
]

FUENTE = ("Indeed MX, búsqueda en vivo 15-sep-2026 — \"abogado\" (Cancún, Quintana Roo); "
         "\"abogado laboral\", \"abogado inmobiliario\", \"oficial de cumplimiento PLD\", "
         "\"abogado protección de datos\" (Ciudad de México).")


def main():
    postings = [vr.VacancyPosting(titulo=t, empresa=e, url=u) for t, e, u in POSTINGS]
    historial = vr.cargar_historial()
    result = vr.ejecutar_radar(postings, fuente=FUENTE, historial_previo=historial)

    log_path = vr.registrar_corrida(result)
    print(f"Corrida registrada en {log_path} ({len(historial) + 1} corrida(s) en el log).")

    informe = vr.render_markdown(result)
    docs_dir = Path(__file__).resolve().parent.parent / "docs"
    salida = docs_dir / "radar-vacantes-2026-09-15.md"
    salida.write_text(informe, encoding="utf-8")
    print(f"Informe escrito en {salida}")
    print()
    print(informe)


if __name__ == "__main__":
    main()
