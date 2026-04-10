"""
Testes automatizados do SQL Insert Validator.
Execute: python tests.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from validator import (
    parse_insert,
    validar_consistencia,
    separar_multiplos_inserts,
    inferir_tipo,
    TipoValor,
    StatusValidacao,
)

VERDE    = "\033[92m"
VERMELHO = "\033[91m"
RESET    = "\033[0m"

passed = 0
failed = 0


def check(descricao: str, condicao: bool):
    global passed, failed
    if condicao:
        print(f"  {VERDE}✅ PASS{RESET} — {descricao}")
        passed += 1
    else:
        print(f"  {VERMELHO}❌ FAIL{RESET} — {descricao}")
        failed += 1


def pipeline(sql):
    r = parse_insert(sql)
    return validar_consistencia(r)


print("\n" + "═" * 60)
print("  SQL Insert Validator — Suite de Testes")
print("═" * 60)

# ── Inferência de tipos ────────────────────────────────────
print("\n📦 Inferência de Tipos de Valor")
check("NULL detectado",          inferir_tipo("NULL")           == TipoValor.NULO)
check("String detectada",        inferir_tipo("'Texto'")        == TipoValor.STRING)
check("Número inteiro",          inferir_tipo("42")             == TipoValor.NUMERO)
check("Número decimal",          inferir_tipo("3.14")           == TipoValor.NUMERO)
check("Número negativo",         inferir_tipo("-99")            == TipoValor.NUMERO)
check("Data ISO string",         inferir_tipo("'2024-01-31'")   == TipoValor.DATA)
check("TO_DATE função",          inferir_tipo("TO_DATE('2024','YYYY')") == TipoValor.DATA)
check("SYSDATE",                 inferir_tipo("SYSDATE")        == TipoValor.DATA)
check("TRUE booleano",           inferir_tipo("TRUE")           == TipoValor.BOOLEANO)
check("FALSE booleano",          inferir_tipo("FALSE")          == TipoValor.BOOLEANO)
check("Função genérica",         inferir_tipo("SEQ.NEXTVAL()")  == TipoValor.EXPRESSAO)

# ── Parse básico ──────────────────────────────────────────
print("\n🔍 Parse de INSERT")

r = pipeline("INSERT INTO CLIENTES (ID, NOME) VALUES (1, 'Ana');")
check("Tabela extraída corretamente",    r.tabela == "CLIENTES")
check("2 colunas identificadas",         len(r.colunas) == 2)
check("2 valores identificados",         len(r.valores) == 2)
check("INSERT válido (status OK)",       r.status == StatusValidacao.OK)
check("Mapeamento ID→1",                r.mapeamento[0].coluna == "ID" and r.mapeamento[0].valor == "1")
check("Mapeamento NOME→'Ana'",          r.mapeamento[1].coluna == "NOME")

# ── Mais colunas que valores ──────────────────────────────
print("\n⚖️  Mais colunas que valores")
r = pipeline("INSERT INTO T (A, B, C) VALUES (1, 2);")
check("Status ERRO",                     r.status == StatusValidacao.ERRO)
check("Erro de divergência registrado",  any("col" in e.lower() for e in r.erros))

# ── Mais valores que colunas ──────────────────────────────
print("\n⚖️  Mais valores que colunas")
r = pipeline("INSERT INTO T (A) VALUES (1, 2, 3);")
check("Status ERRO",                     r.status == StatusValidacao.ERRO)
check("Erro de divergência registrado",  any("valor" in e.lower() for e in r.erros))

# ── Sem lista de colunas ──────────────────────────────────
print("\n📋 INSERT sem lista de colunas")
r = pipeline("INSERT INTO LOG VALUES (SYSDATE, 'USR', NULL);")
check("Aviso emitido",                   len(r.avisos) > 0)
check("3 valores extraídos",             len(r.valores) == 3)
check("Colunas genéricas no mapeamento", r.mapeamento[0].coluna.startswith("COLUNA_"))

# ── Comando inválido ──────────────────────────────────────
print("\n🚫 Comandos inválidos")
r = pipeline("SELECT * FROM TABELA;")
check("SELECT rejeitado (ERRO)",         r.status == StatusValidacao.ERRO)

r = pipeline("INSERT INTO SEM_VALUES (A) (1);")
check("Sem VALUES → ERRO",               r.status == StatusValidacao.ERRO)

# ── Múltiplos INSERTs ─────────────────────────────────────
print("\n🔁 Separação de múltiplos INSERTs")
bloco = """
INSERT INTO A (X) VALUES (1);
INSERT INTO B (Y) VALUES ('texto');
INSERT INTO C (Z) VALUES (NULL);
"""
lista = separar_multiplos_inserts(bloco)
check("3 INSERTs separados",             len(lista) == 3)

# ── Schema qualificado ────────────────────────────────────
print("\n🗄️  Schema.Tabela")
r = pipeline("INSERT INTO SCHEMA.TABELA (COL) VALUES (1);")
check("Schema.Tabela extraído",          r.tabela == "SCHEMA.TABELA")

# ── Tipo de valor no mapeamento ───────────────────────────
print("\n🔠 Tipo no mapeamento")
r = pipeline("INSERT INTO T (N, S, D) VALUES (42, 'abc', '2024-01-01');")
check("Número mapeado corretamente",     r.mapeamento[0].tipo == TipoValor.NUMERO)
check("String mapeada corretamente",     r.mapeamento[1].tipo == TipoValor.STRING)
check("Data mapeada corretamente",       r.mapeamento[2].tipo == TipoValor.DATA)

# ── Resumo ────────────────────────────────────────────────
total = passed + failed
print(f"\n{'═'*60}")
print(f"  Resultado: {VERDE}{passed} passou(ram){RESET} / {VERMELHO}{failed} falhou(aram){RESET} / {total} total")
print(f"{'═'*60}\n")

sys.exit(0 if failed == 0 else 1)
