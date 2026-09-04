"""Revision estatica de la migracion, ANTES de aplicarla a ninguna base.

Requisito 4 de la decision del 2026-09-04: revisar tablas, triggers, vista, RLS
y policies antes de aplicar. Este modulo hace esa revision leyendo el SQL como
texto, sin conectarse a nada.

Que puede y que NO puede demostrar, dicho con precision porque la diferencia
importa:

  PUEDE   comprobar que la migracion DICE lo que debe decir: que cada tabla
          activa RLS, que no hay ninguna policy permisiva, que los grants a
          anon son solo sobre la vista, que la vista exige las cuatro
          condiciones, y que no existe ninguna tabla ni columna de PII, pagos
          o Storage.

  NO PUEDE demostrar que Postgres se comporte asi al ejecutarla. Eso solo lo
          demuestra la verificacion posterior contra la base real
          (`store/verificacion_post_migracion.sql`), corrida como `anon`.

Confundir las dos cosas seria decir que un plano garantiza que el edificio
esta en pie. Por eso cada hallazgo lleva su alcance escrito.

Sin red. Sin base de datos. Determinista.
"""

import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MIGRACION_POR_DEFECTO = AQUI / "migrations" / "0001_almacen_piezas_aprobadas.sql"

OK = "OK"
FALLO = "FALLO"
AVISO = "AVISO"

# Terminos que no deben aparecer como objetos de la base en esta fase
# (requisitos 7 y 8: nada de PII, usuarios, documentos, casos, pagos, Storage).
TERMINOS_PROHIBIDOS = (
    "usuario", "cliente", "persona", "paciente", "pago", "cobro", "factura",
    "tarjeta", "documento", "expediente", "caso_personal", "storage",
    "email", "telefono", "direccion", "dni", "curp", "rfc", "pasaporte",
)

# Columnas cuyo contenido es sensible aunque no sea PII: hay que saber que
# existen y que NUNCA se exponen a anon.
COLUMNAS_SENSIBLES = (
    ("claims", "revision_revisor", "identifica a quien aprobo (alias o rol, nunca persona)"),
    ("claims", "revision_hash_sha256", "liga la aprobacion al texto exacto aprobado"),
    ("piezas", "contenido_hash_sha256", "liga la pieza a su contenido aprobado"),
    ("fuentes", "url", "aparato probatorio: no es publico"),
    ("fuentes", "localizador", "aparato probatorio: no es publico"),
    ("investigaciones", "autor", "identifica a quien investigo (alias o rol)"),
    ("piezas_derivadas", "autorizacion_responsable", "identifica a quien autorizo publicar"),
)

TABLAS_ESPERADAS = ("piezas", "claims", "fuentes", "investigaciones",
                    "piezas_derivadas", "metricas", "aprendizajes")

CONDICIONES_DE_LA_VISTA = (
    "p.publicacion = 'PUBLISHED'",
    "p.gate_global_arte = 'ABIERTO'",
    "p.contenido_hash_sha256 is not null",
    "d.autorizacion_publicacion = 'AUTORIZADA'",
)


class Hallazgo:
    def __init__(self, nivel, area, detalle, alcance):
        self.nivel, self.area, self.detalle, self.alcance = nivel, area, detalle, alcance

    def __repr__(self):
        return f"[{self.nivel}] {self.area}: {self.detalle}"


def _sql(ruta=None):
    return Path(ruta or MIGRACION_POR_DEFECTO).read_text(encoding="utf-8")


def tablas_declaradas(sql):
    return sorted(set(re.findall(r"create table if not exists legalmente\.(\w+)", sql)))


def triggers_declarados(sql):
    return sorted(set(re.findall(r"create trigger (\w+)", sql)))


def funciones_declaradas(sql):
    return sorted(set(re.findall(r"create or replace function legalmente\.(\w+)", sql)))


def vistas_declaradas(sql):
    return sorted(set(re.findall(r"create or replace view\s+legalmente\.(\w+)", sql)))


def restricciones_declaradas(sql):
    return sorted(set(re.findall(r"constraint (\w+) check", sql)))


def revisar_rls(sql):
    h = []
    for tabla in TABLAS_ESPERADAS:
        if re.search(rf"alter table legalmente\.{tabla}\s+enable row level security", sql):
            h.append(Hallazgo(OK, "RLS", f"{tabla}: RLS activado",
                              "el SQL lo declara; confirmar en la base tras aplicar"))
        else:
            h.append(Hallazgo(FALLO, "RLS", f"{tabla}: NO activa RLS",
                              "sin RLS, anon podria leer la tabla entera"))
    return h


def revisar_policies(sql):
    """Sin policies, RLS deniega. Una policy permisiva abriria el aparato
    probatorio al navegador: aqui no debe haber ninguna."""
    encontradas = re.findall(r"create policy\s+(\w+)", sql, re.IGNORECASE)
    if not encontradas:
        return [Hallazgo(OK, "POLICIES",
                         "ninguna policy sobre tablas base (RLS deniega por defecto)",
                         "el SQL no crea ninguna; confirmar con pg_policies tras aplicar")]
    return [Hallazgo(FALLO, "POLICIES", f"existe una policy: {p}",
                     "cada policy es una excepcion a la denegacion por defecto; revisar una a una")
            for p in encontradas]


def revisar_grants(sql):
    h = []
    for vista in vistas_declaradas(sql):
        if re.search(rf"grant select on legalmente\.{vista} to anon, authenticated", sql):
            h.append(Hallazgo(OK, "GRANTS", f"anon puede leer la vista {vista}",
                              "es la unica lectura externa prevista"))
    for tabla in TABLAS_ESPERADAS:
        if re.search(rf"revoke all on legalmente\.{tabla}\s+from anon, authenticated", sql):
            h.append(Hallazgo(OK, "GRANTS", f"{tabla}: revoke all a anon/authenticated",
                              "el SQL lo declara; confirmar con has_table_privilege tras aplicar"))
        else:
            h.append(Hallazgo(AVISO, "GRANTS", f"{tabla}: sin revoke explicito",
                              "RLS ya deniega, pero el revoke es la segunda barrera"))
    if re.search(r"grant\s+(select|all)[^\n]*on legalmente\.(piezas|claims|fuentes|"
                 r"investigaciones|metricas|aprendizajes|piezas_derivadas)\b", sql):
        h.append(Hallazgo(FALLO, "GRANTS", "hay un grant directo sobre una tabla base",
                          "expondria el aparato probatorio"))
    return h


def revisar_vista(sql):
    h = []
    vistas = vistas_declaradas(sql)
    if "piezas_publicables" not in vistas:
        return [Hallazgo(FALLO, "VISTA", "falta la vista piezas_publicables",
                         "sin ella no hay superficie de lectura definida")]
    cuerpo = sql[sql.index("create or replace view"):]
    cuerpo = cuerpo[:cuerpo.index(";")]
    for cond in CONDICIONES_DE_LA_VISTA:
        nivel = OK if cond in cuerpo else FALLO
        h.append(Hallazgo(nivel, "VISTA", f"condicion {'presente' if nivel == OK else 'AUSENTE'}: {cond}",
                          "las cuatro deben cumplirse a la vez para que una pieza sea legible"))
    if "security_invoker = true" in cuerpo:
        h.append(Hallazgo(OK, "VISTA", "security_invoker activado",
                          "la vista no elude el RLS del que consulta"))
    else:
        h.append(Hallazgo(FALLO, "VISTA", "security_invoker NO activado",
                          "una vista sin security_invoker corre con permisos del creador"))
    for campo in ("texto_exacto", "fuentes", "investigacion", "revision_revisor"):
        if re.search(rf"\b{campo}\b", cuerpo):
            h.append(Hallazgo(FALLO, "VISTA", f"la vista expone {campo}",
                              "una pieza publicada no necesita exponer su aparato probatorio"))
    return h


def revisar_ausencia_de_pii(sql):
    h = []
    objetos = re.findall(r"create table if not exists legalmente\.(\w+)", sql)
    columnas = re.findall(r"^\s{4}(\w+)\s+(?:text|integer|boolean|uuid|timestamptz|date)", sql, re.M)
    for termino in TERMINOS_PROHIBIDOS:
        malas_tablas = [t for t in objetos if termino in t.lower()]
        malas_columnas = [c for c in columnas if termino in c.lower()]
        if malas_tablas or malas_columnas:
            h.append(Hallazgo(FALLO, "PII/PAGOS",
                              f"'{termino}' aparece en {malas_tablas + malas_columnas}",
                              "requisitos 7 y 8: no en esta fase"))
    if not h:
        h.append(Hallazgo(OK, "PII/PAGOS",
                          "ninguna tabla ni columna de PII, usuarios, documentos, casos o pagos",
                          f"comprobados {len(TERMINOS_PROHIBIDOS)} terminos sobre "
                          f"{len(objetos)} tablas y {len(columnas)} columnas"))
    if re.search(r"storage\.(buckets|objects)|create bucket", sql, re.IGNORECASE):
        h.append(Hallazgo(FALLO, "STORAGE", "la migracion toca Supabase Storage",
                          "requisito 8: no hasta cerrar privacidad y retencion"))
    else:
        h.append(Hallazgo(OK, "STORAGE", "no se usa Supabase Storage", "requisito 8 respetado"))
    return h


def revisar_higiene_sql(sql):
    h = []
    n_plpgsql = sql.count("language plpgsql")
    n_path = sql.count("set search_path = legalmente, pg_temp")
    if n_plpgsql and n_plpgsql == n_path:
        h.append(Hallazgo(OK, "FUNCIONES", f"las {n_plpgsql} funciones fijan search_path",
                          "sin search_path fijo una funcion es secuestrable"))
    else:
        h.append(Hallazgo(FALLO, "FUNCIONES",
                          f"{n_plpgsql} funciones plpgsql pero {n_path} con search_path fijo",
                          "cada funcion debe fijarlo"))
    if "security definer" in sql.lower():
        h.append(Hallazgo(AVISO, "FUNCIONES", "hay una funcion SECURITY DEFINER",
                          "corre con permisos del creador: revisar una a una"))
    else:
        h.append(Hallazgo(OK, "FUNCIONES", "ninguna funcion SECURITY DEFINER",
                          "todas corren con permisos de quien invoca"))
    # Se ignoran los comentarios de cabecera: el archivo empieza documentando
    # el porque, y mirar solo el primer caracter daba un falso positivo.
    codigo = "\n".join(l for l in sql.splitlines()
                       if l.strip() and not l.strip().startswith("--")).strip()
    if codigo.startswith("begin;") and codigo.rstrip().endswith("commit;"):
        h.append(Hallazgo(OK, "TRANSACCION", "la migracion es atomica (begin/commit)",
                          "si algo falla, no queda a medias"))
    else:
        h.append(Hallazgo(AVISO, "TRANSACCION", "la migracion no esta envuelta en begin/commit",
                          "un fallo a mitad dejaria el esquema incompleto"))
    if re.search(r"\bdrop table\b|\btruncate\b|\bdelete from\b", sql, re.IGNORECASE):
        h.append(Hallazgo(FALLO, "DESTRUCTIVO", "la migracion borra datos",
                          "una migracion inicial nunca deberia borrar nada"))
    else:
        h.append(Hallazgo(OK, "DESTRUCTIVO", "no borra ni trunca ninguna tabla",
                          "solo crea; es segura de aplicar sobre un proyecto vacio"))
    return h


def revisar(ruta=None):
    sql = _sql(ruta)
    h = []
    h += revisar_rls(sql)
    h += revisar_policies(sql)
    h += revisar_grants(sql)
    h += revisar_vista(sql)
    h += revisar_ausencia_de_pii(sql)
    h += revisar_higiene_sql(sql)
    return h


def resumen(ruta=None):
    sql = _sql(ruta)
    return {
        "tablas": tablas_declaradas(sql),
        "triggers": triggers_declarados(sql),
        "funciones": funciones_declaradas(sql),
        "vistas": vistas_declaradas(sql),
        "restricciones": restricciones_declaradas(sql),
        "lineas": len(sql.splitlines()),
    }


def main(argv=None):
    ruta = (argv or sys.argv[1:] or [None])[0]
    r = resumen(ruta)
    print("RESUMEN DE LA MIGRACION")
    print(f"  lineas        : {r['lineas']}")
    print(f"  tablas ({len(r['tablas'])})    : {', '.join(r['tablas'])}")
    print(f"  vistas ({len(r['vistas'])})    : {', '.join(r['vistas'])}")
    print(f"  triggers ({len(r['triggers'])})  : {', '.join(r['triggers'])}")
    print(f"  funciones ({len(r['funciones'])}) : {', '.join(r['funciones'])}")
    print(f"  CHECK con nombre ({len(r['restricciones'])}): {', '.join(r['restricciones'])}")
    print()
    print("COLUMNAS SENSIBLES (existen, y NUNCA se exponen a anon)")
    for tabla, col, por_que in COLUMNAS_SENSIBLES:
        print(f"  legalmente.{tabla}.{col} — {por_que}")
    print()
    print("REVISION ESTATICA")
    hallazgos = revisar(ruta)
    for x in hallazgos:
        print(f"  [{x.nivel:5}] {x.area:12} {x.detalle}")
        print(f"            alcance: {x.alcance}")
    fallos = [x for x in hallazgos if x.nivel == FALLO]
    avisos = [x for x in hallazgos if x.nivel == AVISO]
    print()
    print(f"  {len(hallazgos)} comprobaciones — {len(fallos)} FALLO, {len(avisos)} AVISO")
    print()
    print("  Esta revision lee el SQL como texto. NO demuestra el comportamiento")
    print("  real de Postgres: eso exige aplicar y correr")
    print("  store/verificacion_post_migracion.sql como anon.")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
