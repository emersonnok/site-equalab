"""
gerar_paginas_juridicas.py — publica os Termos e a Política no site.

O QUE ELE FAZ
    Lê os dois documentos de origem (que continuam sendo a fonte de verdade,
    na pasta "Subir no projeto") e gera duas páginas HTML no site:

        Site/termos/index.html       ->  equalab.com.br/termos/
        Site/privacidade/index.html  ->  equalab.com.br/privacidade/

    Corta automaticamente as seções internas (o bloco "⚠️ Antes de publicar" e
    o "O que mudou nesta versão") — elas são recado para nós, não para o
    cliente.

COMO RODAR (uma linha, no Prompt de Comando)
    python "C:\\Emerson\\Programas\\Produto para podcasts\\Site\\gerar_paginas_juridicas.py"

QUANDO RODAR
    Toda vez que o Termos_de_Uso.md ou a Politica_de_Privacidade.md mudarem.
    Assim o site nunca fica com uma versão antiga — que é o defeito clássico
    de copiar e colar texto jurídico à mão.
"""
import html
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DOCS = AQUI.parent.parent / "Subir no projeto"

PAGINAS = [
    {
        "origem": DOCS / "Termos_de_Uso.md",
        "destino": AQUI / "termos" / "index.html",
        "titulo": "Termos de Uso — eQualab Cortex",
        "url": "https://equalab.com.br/termos/",
        "descricao": "Termos de Uso do Cortex: planos, cotas, pagamento, "
                     "cancelamento e responsabilidades.",
    },
    {
        "origem": DOCS / "Politica_de_Privacidade.md",
        "destino": AQUI / "privacidade" / "index.html",
        "titulo": "Política de Privacidade — eQualab Cortex",
        "url": "https://equalab.com.br/privacidade/",
        "descricao": "Como o Cortex trata dados pessoais: o que é coletado, "
                     "com quem é compartilhado e os seus direitos pela LGPD.",
    },
]

# Tudo daqui para baixo é recado interno e NÃO vai para o site.
CORTES = ("## ⚠️ Antes de publicar", "## O que mudou nesta versão")


def limpar(texto: str) -> str:
    for marca in CORTES:
        pos = texto.find(marca)
        if pos != -1:
            texto = texto[:pos]
    return texto.strip()


def inline(txt: str) -> str:
    """negrito, itálico, código e links — o suficiente para texto jurídico."""
    txt = html.escape(txt)
    txt = re.sub(r"`([^`]+)`", r"<code>\1</code>", txt)
    txt = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", txt)
    txt = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", txt)
    txt = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', txt)
    return txt


def markdown_para_html(md: str) -> str:
    """Converte o markdown dos documentos jurídicos em HTML.

    ⚠️ A regra que este conversor é obrigado a respeitar: no markdown, um
    parágrafo continua enquanto não vier uma linha em branco. Os documentos são
    escritos com quebra em ~78 colunas, então quase todo parágrafo ocupa 4 ou 5
    linhas do arquivo — e cada uma delas NÃO é um parágrafo.

    A primeira versão tratava linha por linha. O resultado: cada linha virava um
    <p>, o texto saía com buraco entre todas as frases, e o negrito que
    atravessava a quebra (`**cartão de\\ncrédito**`) nunca fechava — aparecia
    `no** Pix**` na tela. Por isso as linhas são ACUMULADAS e só viram HTML
    quando o bloco termina.
    """
    saida, lista, paragrafo, citacao = [], False, [], []

    def fechar_lista():
        nonlocal lista
        if lista:
            saida.append("</ul>")
            lista = False

    def fechar_paragrafo():
        if paragrafo:
            saida.append(f"<p>{inline(' '.join(paragrafo))}</p>")
            paragrafo.clear()

    def fechar_citacao():
        if citacao:
            saida.append(f"<blockquote>{inline(' '.join(citacao))}</blockquote>")
            citacao.clear()

    def fechar_tudo():
        fechar_paragrafo()
        fechar_citacao()
        fechar_lista()

    for linha in md.split("\n"):
        crua = linha.rstrip()

        if not crua.strip():          # linha em branco = fim do bloco
            fechar_tudo()
            continue

        if crua.strip() == "---":
            fechar_tudo()
            saida.append("<hr>")
            continue

        cab = re.match(r"^(#{1,4})\s+(.*)$", crua)
        if cab:
            fechar_tudo()
            n = len(cab.group(1))
            saida.append(f"<h{n}>{inline(cab.group(2))}</h{n}>")
            continue

        if crua.startswith(">"):
            fechar_paragrafo()
            fechar_lista()
            texto = crua.lstrip(">").strip()
            # dentro da citação, título vira negrito — <h3> num blockquote fica
            # maior que o texto ao redor e rouba a hierarquia da página
            texto = re.sub(r"^#{1,4}\s+(.*)$", r"**\1**", texto)
            if texto:
                citacao.append(texto)
            continue
        fechar_citacao()

        item = re.match(r"^\s*[-*]\s+(.*)$", crua)
        if item:
            fechar_paragrafo()
            if not lista:
                saida.append("<ul>")
                lista = True
            saida.append(f"<li>{inline(item.group(1))}</li>")
            continue

        # continuação de um item de lista (linha indentada) entra no item
        if lista and linha.startswith(("  ", "\t")):
            if saida and saida[-1].endswith("</li>"):
                saida[-1] = saida[-1][:-5] + " " + inline(crua.strip()) + "</li>"
            continue
        fechar_lista()

        paragrafo.append(crua.strip())

    fechar_tudo()
    return "\n".join(saida)


MOLDE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descricao}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--fundo:#2B2F38;--branco:#343945;--borda:#434959;--grafite:#F1F3F7;
--texto:#D6DAE3;--fraco:#A6ACBB;--azul:#4FC0F0;--violeta:#5B4FC0;--escuro:#1C1F26;
--grad:linear-gradient(90deg,#29A8E0,#5B4FC0,#C81E82);}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--fundo);color:var(--texto);font-family:Inter,system-ui,sans-serif;line-height:1.7}}
.wrap{{max-width:760px;margin:0 auto;padding:0 22px}}
header{{border-bottom:1px solid var(--borda);background:var(--escuro)}}
.nav{{display:flex;align-items:center;height:62px;gap:18px;max-width:760px;margin:0 auto;padding:0 22px}}
.marca{{font-family:Poppins;font-weight:600;font-size:21px;color:var(--grafite);letter-spacing:-.5px}}
.marca b{{color:var(--azul)}}
.nav a.volta{{margin-left:auto;color:var(--fraco);font-size:14.5px}}
main{{padding:46px 0 20px}}
h1{{font-family:Poppins;font-size:clamp(26px,4vw,34px);color:var(--grafite);line-height:1.25;margin-bottom:8px}}
h2{{font-family:Poppins;font-size:20px;color:var(--grafite);margin:34px 0 10px}}
h3{{font-family:Poppins;font-size:17px;color:var(--grafite);margin:24px 0 8px}}
p{{margin-bottom:14px;font-size:15.6px}}
strong{{color:var(--grafite)}}
ul{{margin:0 0 16px 22px}}
li{{margin-bottom:7px;font-size:15.6px}}
hr{{border:0;border-top:1px solid var(--borda);margin:30px 0}}
a{{color:var(--azul)}}
code{{background:var(--escuro);border:1px solid var(--borda);border-radius:5px;padding:1px 6px;font-size:14px}}
blockquote{{border-left:3px solid var(--violeta);padding:6px 0 6px 16px;margin:0 0 16px;color:var(--fraco);font-size:15px}}
em{{color:var(--fraco)}}
footer{{background:var(--escuro);padding:28px 0;color:#B9BCC6;font-size:14px;margin-top:50px}}
footer a{{color:#8FD4F5}}
.aviso{{background:var(--branco);border:1px solid var(--borda);border-left:3px solid var(--violeta);
border-radius:10px;padding:14px 16px;font-size:14px;color:var(--fraco);margin-bottom:26px}}
</style>
</head>
<body>
<header>
  <div class="nav">
    <a href="/" class="marca">Cortex<b>.</b></a>
    <a href="/ouvir/" class="volta">Voltar aos podcasts</a>
  </div>
</header>
<main>
  <div class="wrap">
    <div class="aviso">Página gerada a partir do documento oficial. Em caso de
    dúvida, escreva para <a href="mailto:contato@equalab.com.br">contato@equalab.com.br</a>.</div>
{corpo}
  </div>
</main>
<footer>
  <div class="wrap">
    © <span id="ano"></span> eQualab · Palhoça/SC ·
    <a href="/termos/">Termos</a> ·
    <a href="/privacidade/">Privacidade</a> ·
    <a href="/ouvir/">Podcasts</a>
  </div>
</footer>
<script>document.getElementById("ano").textContent=new Date().getFullYear();</script>
</body>
</html>
"""


def main():
    for pagina in PAGINAS:
        origem = pagina["origem"]
        if not origem.exists():
            print(f"[ERRO] não achei {origem}")
            continue
        corpo = markdown_para_html(limpar(origem.read_text(encoding="utf-8")))
        pagina["destino"].parent.mkdir(parents=True, exist_ok=True)
        pagina["destino"].write_text(
            MOLDE.format(
                titulo=html.escape(pagina["titulo"]),
                descricao=html.escape(pagina["descricao"]),
                url=pagina["url"],
                corpo=corpo,
            ),
            encoding="utf-8",
        )
        print(f"[ok] {origem.name} -> {pagina['destino']}")


if __name__ == "__main__":
    main()
