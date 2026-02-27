#!/usr/bin/env python3
"""
Convert Peter Watts' Behemoth from OpenOffice HTML export to Standard Ebooks format.

This is the most complex book in the Rifters trilogy:
- Originally published as TWO novels: "Behemoth: B-Max" (2004) and "Behemoth: Seppuku" (2005)
- Treated as a SINGLE volume with B-Max and Seppuku as divisions
- Has a Prelude ('lawbreaker), B-Max chapters, Seppuku chapters, Epilog
- 49 footnotes in the Notes and References section
- Symbol font issues (beta -> B for Behemoth, TM symbols, etc.)
"""

import re
import os
import html
from bs4 import BeautifulSoup, NavigableString

BASE_DIR = "/home/neel/projects/standardebooks/peter-watts_behemoth"
SRC_DIR = os.path.join(BASE_DIR, "src/epub")
TEXT_DIR = os.path.join(SRC_DIR, "text")
SOURCE_FILE = "/tmp/pw/Behemoth/Behemoth.htm"

XHTML_HEADER = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" epub:prefix="z3998: http://www.daisy.org/z3998/2012/vocab/structure/, se: https://standardebooks.org/vocab/1.0" xml:lang="en-US">
\t<head>
\t\t<title>{title}</title>
\t\t<link href="../css/core.css" rel="stylesheet" type="text/css"/>
\t\t<link href="../css/local.css" rel="stylesheet" type="text/css"/>
\t</head>
"""

def read_source():
    """Read the source HTML file with iso-8859-1 encoding."""
    with open(SOURCE_FILE, "rb") as f:
        raw = f.read()
    return raw.decode("iso-8859-1")

def fix_symbol_fonts(text):
    """Fix Symbol font characters.

    Symbol font 'b' or beta (ß) before 'ehemoth' -> 'B'
    &#61668; -> TM symbol
    &#61541; -> epsilon
    &#61555; -> sigma
    &#61549; -> mu
    &#61616; -> degree
    &#61472; -> space
    &#61484; -> comma (,)
    &#61486; -> period (.)
    """
    # Fix <FONT FACE="Symbol">b</FONT>ehemoth -> Behemoth
    text = re.sub(r'<FONT[^>]*FACE="Symbol"[^>]*>b</FONT>', 'B', text, flags=re.IGNORECASE)

    # Fix <FONT SIZE=3><FONT FACE="Symbol">b</FONT></FONT>ehemoth -> Behemoth
    text = re.sub(r'<FONT[^>]*><FONT[^>]*FACE="Symbol"[^>]*>b</FONT></FONT>', 'B', text, flags=re.IGNORECASE)

    # Fix <FONT FACE="Symbol, serif">ß</FONT>-max -> B-max  (and variants)
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>\xdf</FONT>', 'B', text)

    # Fix ß (the raw character in iso-8859-1) before ehemoth -> Behemoth
    text = re.sub(r'\xdfehemoth', 'Behemoth', text)
    text = re.sub(r'\xdf-Max', 'B-Max', text)
    text = re.sub(r'\xdf-max', 'B-max', text)

    # Fix remaining ß characters that should be B (in context of Behemoth references)
    # The raw ß in front of "-<FONT..." pattern for B-Max heading
    text = re.sub(r'\xdf-<FONT', 'B-<FONT', text)

    # Symbol font entity replacements
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61668;</FONT>', '\u2122', text)  # TM
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61541;</FONT>', '\u03b5', text)  # epsilon
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61555;</FONT>', '\u03c3', text)  # sigma
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61549;</FONT>', '\u03bc', text)  # mu
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61616;</FONT>', '\u00b0', text)  # degree
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61472;</FONT>', ' ', text)       # space
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61484;</FONT>', ',', text)       # comma
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>&#61486;</FONT>', '.', text)       # period

    # Handle Symbol font wrapping around SUP tags (footnote refs)
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*><SUP>(&#\d+;)</SUP></FONT>', lambda m: m.group(1), text)
    text = re.sub(r'<SUP><FONT[^>]*FACE="Symbol[^"]*"[^>]*>(.*?)</FONT></SUP>', lambda m: '<SUP>' + m.group(1) + '</SUP>', text)

    # Clean any remaining Symbol font wrappers around footnote links
    text = re.sub(r'<FONT[^>]*FACE="Symbol[^"]*"[^>]*>(<A CLASS="sdfootnoteanc"[^>]*><SUP>\d+</SUP></A>)</FONT>', r'\1', text)

    # Clean Saturday Sans ICG font wrappers
    text = re.sub(r'<FONT FACE="Saturday Sans ICG, Times New Roman">(.*?)</FONT>', r'\1', text, flags=re.DOTALL)

    return text

def clean_paragraph_text(text):
    """Clean up paragraph text from HTML source."""
    # Remove FONT tags that are just for sizing
    text = re.sub(r'<FONT[^>]*SIZE[^>]*>(.*?)</FONT>', r'\1', text, flags=re.DOTALL)

    # Convert HTML entities
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&shy;', '')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')

    # Convert <I> to <i>, <B> to <b>, <SUP> to <sup>
    text = re.sub(r'<I>(.*?)</I>', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'<B>(.*?)</B>', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'<SUP>(.*?)</SUP>', r'<sup>\1</sup>', text, flags=re.DOTALL)

    # Remove remaining FONT tags
    text = re.sub(r'</?FONT[^>]*>', '', text)

    # Remove NAME anchors
    text = re.sub(r'<A NAME="[^"]*"></A>\s*', '', text)
    text = re.sub(r'<A NAME="[^"]*">\s*</A>\s*', '', text)

    # Remove outline anchors but keep content
    text = re.sub(r'<A NAME="[^"]*">', '', text)

    # Clean up whitespace
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n\s+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Fix space issues around italic tags
    # Preserve spaces that were inside closing italics: "word</i> next" not "word</i>next"
    text = re.sub(r'</i>([A-Za-z])', r'</i> \1', text)
    text = re.sub(r'([A-Za-z])<i>', r'\1 <i>', text)

    # Fix double spaces
    text = re.sub(r'  +', ' ', text)

    return text

def parse_chapters(text):
    """Parse the source HTML into a structured list of chapters."""
    # Fix symbol fonts first
    text = fix_symbol_fonts(text)

    # Structure of the book:
    # 1. Front matter (title, dedication, author's note) - before TOC
    # 2. TOC
    # 3. Prelude: 'lawbreaker (H2)
    # 4. B-Max heading (H2)
    #    - B-Max epigraph
    #    - Chapters 1-31 (H3)
    # 5. Seppuku heading (H2)
    #    - Seppuku epigraph
    #    - Chapters 32-60 (H3)
    # 6. Epilog: Singular Hessian (H2)
    # 7. Acknowledgements (H2)
    # 8. Notes and references (H2) - contains footnote definitions
    # 9. Creative Commons info

    # Find the main body content (after the TOC div)
    toc_end = text.find('</DIV>', text.find('Table of Contents1'))
    if toc_end == -1:
        raise ValueError("Could not find end of Table of Contents")

    body_text = text[toc_end:]

    # Split on H2 and H3 headings
    # Pattern matches H2 and H3 tags
    heading_pattern = re.compile(r'<H([23])\s+CLASS="western"[^>]*>(.*?)</H\1>', re.DOTALL)

    sections = []
    last_end = 0

    for m in heading_pattern.finditer(body_text):
        heading_level = int(m.group(1))
        heading_raw = m.group(2)

        # Clean heading text
        heading_text = re.sub(r'<[^>]+>', '', heading_raw).strip()
        heading_text = re.sub(r'\s+', ' ', heading_text)

        # Skip empty headings
        if not heading_text or heading_text == '\n':
            continue

        # Get content after this heading until next heading
        content_start = m.end()

        # Find next heading
        next_heading = heading_pattern.search(body_text, content_start)
        if next_heading:
            content_end = next_heading.start()
        else:
            content_end = len(body_text)

        content = body_text[content_start:content_end]

        sections.append({
            'level': heading_level,
            'title': heading_text,
            'content': content
        })

    return sections

def extract_paragraphs(content_html):
    """Extract paragraphs from content HTML, handling section breaks."""
    paragraphs = []

    # Find all P tags
    p_pattern = re.compile(r'<P\s+[^>]*>(.*?)</P>', re.DOTALL | re.IGNORECASE)

    # Also find <hr> tags for section breaks
    parts = re.split(r'(<hr[^>]*>)', content_html)

    result_parts = []

    for part in parts:
        if re.match(r'<hr', part, re.IGNORECASE):
            result_parts.append({'type': 'hr'})
            continue

        for m in p_pattern.finditer(part):
            raw = m.group(1).strip()

            # Skip empty paragraphs (just <BR> or whitespace)
            cleaned = re.sub(r'<[^>]+>', '', raw).strip()
            if not cleaned or cleaned == '\n':
                continue

            # Check if centered (potential network post or epigraph)
            is_centered = 'ALIGN=CENTER' in m.group(0)
            is_right = 'ALIGN=RIGHT' in m.group(0)

            text = clean_paragraph_text(raw)

            if text:
                result_parts.append({
                    'type': 'p',
                    'text': text,
                    'centered': is_centered,
                    'right': is_right
                })

    return result_parts

def format_paragraph(p_data):
    """Format a paragraph data dict into XHTML."""
    text = p_data['text']

    if p_data.get('centered'):
        return f'\t\t\t<p class="center">{text}</p>'
    elif p_data.get('right'):
        return f'\t\t\t<p class="right">{text}</p>'
    else:
        return f'\t\t\t<p>{text}</p>'

def write_xhtml_file(filepath, title, body_content):
    """Write an XHTML file with standard SE headers."""
    content = XHTML_HEADER.format(title=html.escape(title))
    content += body_content
    content += "\n</html>\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def process_footnotes_in_text(text, chapter_file):
    """Convert OOo footnote references to SE endnote references.

    Input: <SUP><A CLASS="sdfootnoteanc" NAME="sdfootnote1anc" HREF="#sdfootnote1sym"><SUP>1</SUP></A></SUP>
    Output: <a href="endnotes.xhtml#note-1" id="noteref-1" epub:type="noteref">1</a>
    """
    def replace_footnote(m):
        num = m.group(1)
        return f'<a href="endnotes.xhtml#note-{num}" id="noteref-{num}" epub:type="noteref">{num}</a>'

    # Match the double-SUP pattern from OOo
    text = re.sub(
        r'<sup><A CLASS="sdfootnoteanc"[^>]*HREF="#sdfootnote(\d+)sym"[^>]*><sup>\d+</sup></A></sup>',
        replace_footnote, text, flags=re.IGNORECASE
    )

    # Also match single-SUP variant
    text = re.sub(
        r'<A CLASS="sdfootnoteanc"[^>]*HREF="#sdfootnote(\d+)sym"[^>]*><sup>\d+</sup></A>',
        replace_footnote, text, flags=re.IGNORECASE
    )

    # Match any remaining patterns with SUP wrapping
    text = re.sub(
        r'<sup>,</sup>',
        ',', text
    )

    return text

def extract_footnote_definitions(text):
    """Extract footnote definitions from DIV sections at end of file."""
    footnotes = {}

    pattern = re.compile(
        r'<DIV ID="sdfootnote(\d+)">\s*(.*?)\s*</DIV>',
        re.DOTALL | re.IGNORECASE
    )

    for m in pattern.finditer(text):
        num = int(m.group(1))
        content = m.group(2)

        # Extract the text from the P tag
        p_match = re.search(r'<P[^>]*>(.*?)</P>', content, re.DOTALL | re.IGNORECASE)
        if p_match:
            footnote_text = p_match.group(1)

            # Remove the back-reference anchor
            footnote_text = re.sub(
                r'<A CLASS="sdfootnotesym"[^>]*>\d+</A>\s*',
                '', footnote_text, flags=re.IGNORECASE
            )

            # Clean up
            footnote_text = clean_paragraph_text(footnote_text)
            footnotes[num] = footnote_text

    return footnotes

def build_chapter_content(paragraphs, is_fiction=True):
    """Build the paragraph content for a chapter."""
    lines = []
    in_hr = False

    for p in paragraphs:
        if p['type'] == 'hr':
            lines.append('\t\t\t<hr/>')
            in_hr = True
            continue

        lines.append(format_paragraph(p))

    return '\n'.join(lines)

def main():
    print("Reading source file...")
    raw_text = read_source()

    print("Fixing symbol fonts...")
    text = fix_symbol_fonts(raw_text)

    print("Extracting footnote definitions...")
    footnotes = extract_footnote_definitions(text)
    print(f"  Found {len(footnotes)} footnotes")

    print("Parsing sections...")
    sections = parse_chapters(text)

    # Debug: show what we found
    for s in sections:
        print(f"  H{s['level']}: {s['title'][:60]}")

    # Classify sections
    # Structure:
    # H2: Prelude: 'lawbreaker
    # H2: B-Max
    # H3: Counterstrike ... (B-Max chapters)
    # H2: Seppuku
    # H3: Dune ... (Seppuku chapters)
    # H2: Epilog: Singular Hessian
    # H2: Acknowledgements
    # H2: Notes and references
    # H2: Creative Commons Licensing Information

    prelude = None
    bmax_header = None
    bmax_chapters = []
    seppuku_header = None
    seppuku_chapters = []
    epilog = None
    acknowledgements = None
    notes_section = None

    current_division = None  # 'bmax' or 'seppuku'

    for s in sections:
        title = s['title']

        if "Prelude" in title and "'lawbreaker" in title:
            prelude = s
            continue
        elif title == "B-Max" or title.startswith("B-") and "Max" in title:
            bmax_header = s
            current_division = 'bmax'
            continue
        elif title == "Seppuku" and s['level'] == 2:
            seppuku_header = s
            current_division = 'seppuku'
            continue
        elif "Epilog" in title:
            epilog = s
            current_division = None
            continue
        elif "Acknowledgements" in title or "Acknowledgments" in title:
            acknowledgements = s
            current_division = None
            continue
        elif "Notes and references" in title:
            notes_section = s
            current_division = None
            continue
        elif "Creative" in title and "Commons" in title:
            current_division = None
            continue

        if s['level'] == 3:
            if current_division == 'bmax':
                bmax_chapters.append(s)
            elif current_division == 'seppuku':
                seppuku_chapters.append(s)

    print(f"\nStructure found:")
    print(f"  Prelude: {'Yes' if prelude else 'No'}")
    print(f"  B-Max header: {'Yes' if bmax_header else 'No'}")
    print(f"  B-Max chapters: {len(bmax_chapters)}")
    print(f"  Seppuku header: {'Yes' if seppuku_header else 'No'}")
    print(f"  Seppuku chapters: {len(seppuku_chapters)}")
    print(f"  Epilog: {'Yes' if epilog else 'No'}")
    print(f"  Acknowledgements: {'Yes' if acknowledgements else 'No'}")
    print(f"  Notes section: {'Yes' if notes_section else 'No'}")

    # =========================================================
    # EXTRACT DEDICATION from front matter
    # =========================================================
    # The dedication is between the title page and the author's note
    # Look for it in the original text before the TOC
    toc_start = text.find('Table of Contents1')
    front_matter = text[:toc_start] if toc_start > 0 else ""

    # The dedication is between first <hr> and "Author's Note"
    # "In memory of Strange Cat..." and "And in memory of Chuckwalla..."

    # =========================================================
    # EXTRACT EPIGRAPHS from B-Max and Seppuku headers
    # =========================================================

    # B-Max epigraph: The world is not dying... - Utah Phillips
    bmax_epigraph_paras = extract_paragraphs(bmax_header['content']) if bmax_header else []

    # Seppuku epigraph: Two quotes - E.O. Wilson and J.D.S. Haldane
    seppuku_epigraph_paras = extract_paragraphs(seppuku_header['content']) if seppuku_header else []

    # =========================================================
    # EXTRACT AUTHOR'S NOTE from front matter
    # =========================================================
    # Between "Author's Note" heading and the TOC
    authors_note_text = ""
    an_start = front_matter.find("Author\u2019s\nNote")
    if an_start == -1:
        an_start = front_matter.find("Author's\nNote")
    if an_start == -1:
        an_start = front_matter.find("Author\xe2\x80\x99s Note")
    if an_start == -1:
        # Try without apostrophe
        an_start = front_matter.find("Author")

    # =========================================================
    # WRITE FILES
    # =========================================================

    print("\nWriting XHTML files...")

    # --- Dedication ---
    ded_content = """\t<body epub:type="frontmatter">
\t\t<section id="dedication" epub:type="dedication">
\t\t\t<p>In memory of Strange Cat, <i><abbr class="eoc">a.k.a.</abbr></i> Carcinoma,<br/>
\t\t\t1984&#8211;2003</p>
\t\t\t<p>She wouldn't have cared.</p>
\t\t\t<p>And in memory of Chuckwalla,<br/>
\t\t\t1994&#8211;2001</p>
\t\t\t<p>A victim of technology run amok.</p>
\t\t</section>
\t</body>"""
    write_xhtml_file(os.path.join(TEXT_DIR, "dedication.xhtml"), "Dedication", ded_content)
    print("  dedication.xhtml")

    # --- Author's Note (foreword) ---
    # Extract from front matter
    an_match = re.search(
        r'Author.s\s*Note</B></FONT></P>\s*(.*?)<hr',
        front_matter, re.DOTALL
    )

    an_paras = []
    if an_match:
        an_html = an_match.group(1)
        an_parts = extract_paragraphs(an_html)
        an_paras = [p for p in an_parts if p['type'] == 'p']

    foreword_body = '\t<body epub:type="frontmatter">\n'
    foreword_body += '\t\t<section id="foreword" epub:type="foreword">\n'
    foreword_body += '\t\t\t<h2 epub:type="title">Author\'s Note</h2>\n'
    for p in an_paras:
        foreword_body += f'\t\t\t<p>{p["text"]}</p>\n'
    foreword_body += '\t\t</section>\n'
    foreword_body += '\t</body>'
    write_xhtml_file(os.path.join(TEXT_DIR, "foreword.xhtml"), "Author's Note", foreword_body)
    print("  foreword.xhtml")

    # --- Half title page ---
    ht_content = """\t<body epub:type="frontmatter">
\t\t<section id="halftitlepage" epub:type="halftitlepage">
\t\t\t<h2 epub:type="fulltitle">Behemoth</h2>
\t\t</section>
\t</body>"""
    write_xhtml_file(os.path.join(TEXT_DIR, "halftitlepage.xhtml"), "Behemoth", ht_content)
    print("  halftitlepage.xhtml")

    # --- Prelude ---
    if prelude:
        prelude_paras = extract_paragraphs(prelude['content'])
        prelude_body = '\t<body epub:type="bodymatter z3998:fiction">\n'
        prelude_body += '\t\t<section id="prelude" epub:type="prologue">\n'
        prelude_body += '\t\t\t<hgroup>\n'
        prelude_body += '\t\t\t\t<h2 epub:type="title">Prelude</h2>\n'
        prelude_body += "\t\t\t\t<p epub:type=\"subtitle\">\u2019lawbreaker</p>\n"
        prelude_body += '\t\t\t</hgroup>\n'

        for p in prelude_paras:
            if p['type'] == 'hr':
                prelude_body += '\t\t\t<hr/>\n'
            elif p['type'] == 'p':
                prelude_body += f'\t\t\t<p>{p["text"]}</p>\n'

        prelude_body += '\t\t</section>\n'
        prelude_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, "prelude.xhtml"), "Prelude: \u2019lawbreaker", prelude_body)
        print("  prelude.xhtml")

    # --- Division 1: B-Max ---
    div1_body = '\t<body epub:type="bodymatter z3998:fiction">\n'
    div1_body += '\t\t<section id="division-1" epub:type="division">\n'
    div1_body += '\t\t\t<hgroup>\n'
    div1_body += '\t\t\t\t<h2 epub:type="title">Behemoth</h2>\n'
    div1_body += '\t\t\t\t<p epub:type="subtitle">B-Max</p>\n'
    div1_body += '\t\t\t</hgroup>\n'
    div1_body += '\t\t</section>\n'
    div1_body += '\t</body>'
    write_xhtml_file(os.path.join(TEXT_DIR, "division-1.xhtml"), "Behemoth: B-Max", div1_body)
    print("  division-1.xhtml")

    # --- B-Max epigraph ---
    if bmax_epigraph_paras:
        epigraph_1_body = '\t<body epub:type="bodymatter z3998:fiction" data-parent="division-1">\n'
        epigraph_1_body += '\t\t<section id="epigraph-1" epub:type="epigraph">\n'
        for p in bmax_epigraph_paras:
            if p['type'] == 'p':
                text = p['text']
                # Check if it's an attribution line (starts with em-dash)
                if text.startswith('\u2014') or text.startswith('\u2013') or text.startswith('\xe9'):
                    epigraph_1_body += f'\t\t\t<p epub:type="z3998:attribution">{text}</p>\n'
                else:
                    epigraph_1_body += f'\t\t\t<blockquote>\n\t\t\t\t<p>{text}</p>\n'
        # Close the blockquote before attribution
        # Actually, let's build this more carefully

    # Re-do epigraph handling more carefully
    # B-Max has:
    # "The world is not dying, it is being killed. And those that are killing it have names and addresses."
    # —Utah Phillips
    epigraph_1_body = '\t<body epub:type="bodymatter z3998:fiction" data-parent="division-1">\n'
    epigraph_1_body += '\t\t<section id="epigraph-1" epub:type="epigraph">\n'
    epigraph_1_body += '\t\t\t<blockquote>\n'
    epigraph_1_body += '\t\t\t\t<p>\u201cThe world is not dying, it is being killed. And those that are killing it have names and addresses.\u201d</p>\n'
    epigraph_1_body += '\t\t\t\t<cite>\u2014<i>Utah Phillips</i></cite>\n'
    epigraph_1_body += '\t\t\t</blockquote>\n'
    epigraph_1_body += '\t\t</section>\n'
    epigraph_1_body += '\t</body>'
    write_xhtml_file(os.path.join(TEXT_DIR, "epigraph-1.xhtml"), "Epigraph", epigraph_1_body)
    print("  epigraph-1.xhtml")

    # --- B-Max Chapters ---
    bmax_chapter_names = [
        "Counterstrike", "The Shiva Iterations", "Outgroup", "Huddle",
        "Zombie", "Portrait of the Sadist as a Young Boy", "Confidence Limits",
        "Cavalry", "Nemesis", "Portrait of the Sadist as an Adolescent",
        "Bedside Manor", "Boilerplate", "Portrait of the Sadist as a Young Man",
        "Fire Drill", "Family Values", "Portrait of the Sadist as a Free Man",
        "Confessional", "Conscript", "Portrait of the Sadist as a Team Player",
        "Automechanica", "Gravediggers", "Striptease", "Frontier", "Groundwork",
        "Harpodon", "The Bloodhound Iterations", "Without Sin", "Baptism",
        "Tag", "Fulcrum", "Incoming"
    ]

    for i, chapter in enumerate(bmax_chapters):
        ch_num = i + 1
        filename = f"chapter-1-{ch_num}.xhtml"

        paras = extract_paragraphs(chapter['content'])

        ch_body = '\t<body epub:type="bodymatter z3998:fiction" data-parent="division-1">\n'
        ch_body += f'\t\t<section id="chapter-1-{ch_num}" epub:type="chapter">\n'
        ch_body += f'\t\t\t<h3 epub:type="title">{html.escape(chapter["title"])}</h3>\n'

        for p in paras:
            if p['type'] == 'hr':
                ch_body += '\t\t\t<hr/>\n'
            elif p['type'] == 'p':
                text = process_footnotes_in_text(p['text'], filename)
                ch_body += f'\t\t\t<p>{text}</p>\n'

        ch_body += '\t\t</section>\n'
        ch_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, filename), chapter['title'], ch_body)

    print(f"  {len(bmax_chapters)} B-Max chapter files")

    # --- Division 2: Seppuku ---
    div2_body = '\t<body epub:type="bodymatter z3998:fiction">\n'
    div2_body += '\t\t<section id="division-2" epub:type="division">\n'
    div2_body += '\t\t\t<hgroup>\n'
    div2_body += '\t\t\t\t<h2 epub:type="title">Behemoth</h2>\n'
    div2_body += '\t\t\t\t<p epub:type="subtitle">Seppuku</p>\n'
    div2_body += '\t\t\t</hgroup>\n'
    div2_body += '\t\t</section>\n'
    div2_body += '\t</body>'
    write_xhtml_file(os.path.join(TEXT_DIR, "division-2.xhtml"), "Behemoth: Seppuku", div2_body)
    print("  division-2.xhtml")

    # --- Seppuku epigraph ---
    # Has two quotes:
    # "The essence of humanity's spiritual dilemma..." - E.O. Wilson
    # "I would gladly lay down my life for two brothers or eight cousins." - J.D.S. Haldane
    epigraph_2_body = '\t<body epub:type="bodymatter z3998:fiction" data-parent="division-2">\n'
    epigraph_2_body += '\t\t<section id="epigraph-2" epub:type="epigraph">\n'
    epigraph_2_body += '\t\t\t<blockquote>\n'
    epigraph_2_body += '\t\t\t\t<p>\u201cThe essence of humanity\u2019s spiritual dilemma is that we evolved genetically to accept one truth and discovered another.\u201d</p>\n'
    epigraph_2_body += '\t\t\t\t<cite>\u2014E. O. Wilson</cite>\n'
    epigraph_2_body += '\t\t\t</blockquote>\n'
    epigraph_2_body += '\t\t\t<blockquote>\n'
    epigraph_2_body += '\t\t\t\t<p>\u201cI would gladly lay down my life for two brothers or eight cousins.\u201d</p>\n'
    epigraph_2_body += '\t\t\t\t<cite>\u2014<abbr class="eoc">J. D. S.</abbr> Haldane</cite>\n'
    epigraph_2_body += '\t\t\t</blockquote>\n'
    epigraph_2_body += '\t\t</section>\n'
    epigraph_2_body += '\t</body>'
    write_xhtml_file(os.path.join(TEXT_DIR, "epigraph-2.xhtml"), "Epigraph", epigraph_2_body)
    print("  epigraph-2.xhtml")

    # --- Seppuku Chapters ---
    for i, chapter in enumerate(seppuku_chapters):
        ch_num = i + 1
        filename = f"chapter-2-{ch_num}.xhtml"

        paras = extract_paragraphs(chapter['content'])

        ch_body = '\t<body epub:type="bodymatter z3998:fiction" data-parent="division-2">\n'
        ch_body += f'\t\t<section id="chapter-2-{ch_num}" epub:type="chapter">\n'
        ch_body += f'\t\t\t<h3 epub:type="title">{html.escape(chapter["title"])}</h3>\n'

        for p in paras:
            if p['type'] == 'hr':
                ch_body += '\t\t\t<hr/>\n'
            elif p['type'] == 'p':
                text = process_footnotes_in_text(p['text'], filename)
                ch_body += f'\t\t\t<p>{text}</p>\n'

        ch_body += '\t\t</section>\n'
        ch_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, filename), chapter['title'], ch_body)

    print(f"  {len(seppuku_chapters)} Seppuku chapter files")

    # --- Epilog ---
    if epilog:
        epilog_paras = extract_paragraphs(epilog['content'])
        epilog_body = '\t<body epub:type="bodymatter z3998:fiction">\n'
        epilog_body += '\t\t<section id="epilog" epub:type="epilogue">\n'
        epilog_body += '\t\t\t<hgroup>\n'
        epilog_body += '\t\t\t\t<h2 epub:type="title">Epilog</h2>\n'
        epilog_body += '\t\t\t\t<p epub:type="subtitle">Singular Hessian</p>\n'
        epilog_body += '\t\t\t</hgroup>\n'

        for p in epilog_paras:
            if p['type'] == 'hr':
                epilog_body += '\t\t\t<hr/>\n'
            elif p['type'] == 'p':
                text = p['text']
                if p.get('centered'):
                    epilog_body += f'\t\t\t<p class="center">{text}</p>\n'
                else:
                    epilog_body += f'\t\t\t<p>{text}</p>\n'

        epilog_body += '\t\t</section>\n'
        epilog_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, "epilog.xhtml"), "Epilog: Singular Hessian", epilog_body)
        print("  epilog.xhtml")

    # --- Acknowledgements ---
    if acknowledgements:
        ack_paras = extract_paragraphs(acknowledgements['content'])
        ack_body = '\t<body epub:type="backmatter">\n'
        ack_body += '\t\t<section id="acknowledgements" epub:type="acknowledgments">\n'
        ack_body += '\t\t\t<h2 epub:type="title">Acknowledgements</h2>\n'

        for p in ack_paras:
            if p['type'] == 'p':
                ack_body += f'\t\t\t<p>{p["text"]}</p>\n'

        ack_body += '\t\t</section>\n'
        ack_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, "acknowledgements.xhtml"), "Acknowledgements", ack_body)
        print("  acknowledgements.xhtml")

    # --- Notes and References (as endnotes) ---
    # The notes section has both prose text and footnote references
    # We'll create two files: notes.xhtml (prose) and endnotes.xhtml (footnote defs)

    if notes_section:
        notes_paras = extract_paragraphs(notes_section['content'])
        notes_body = '\t<body epub:type="backmatter">\n'
        notes_body += '\t\t<section id="notes" epub:type="appendix">\n'
        notes_body += '\t\t\t<h2 epub:type="title">Notes and References</h2>\n'

        for p in notes_paras:
            if p['type'] == 'p':
                text = process_footnotes_in_text(p['text'], 'notes.xhtml')

                # Check if this is a bold section header
                if text.startswith('<b>') and text.endswith('</b>'):
                    notes_body += f'\t\t\t<p>\n\t\t\t\t{text}\n\t\t\t</p>\n'
                else:
                    notes_body += f'\t\t\t<p>{text}</p>\n'

        notes_body += '\t\t</section>\n'
        notes_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, "notes.xhtml"), "Notes and References", notes_body)
        print("  notes.xhtml")

    # --- Endnotes ---
    if footnotes:
        en_body = '\t<body epub:type="backmatter">\n'
        en_body += '\t\t<section id="endnotes" epub:type="endnotes">\n'
        en_body += '\t\t\t<h2 epub:type="title">Endnotes</h2>\n'
        en_body += '\t\t\t<ol>\n'

        for num in sorted(footnotes.keys()):
            text = footnotes[num]
            text = clean_paragraph_text(text)
            en_body += f'\t\t\t\t<li id="note-{num}" epub:type="endnote">\n'
            en_body += f'\t\t\t\t\t<p>{text} <a href="notes.xhtml#noteref-{num}" epub:type="backlink">\u21a9</a></p>\n'
            en_body += f'\t\t\t\t</li>\n'

        en_body += '\t\t\t</ol>\n'
        en_body += '\t\t</section>\n'
        en_body += '\t</body>'
        write_xhtml_file(os.path.join(TEXT_DIR, "endnotes.xhtml"), "Endnotes", en_body)
        print(f"  endnotes.xhtml ({len(footnotes)} notes)")

    print("\nConversion complete!")
    print(f"Total files written: {2 + 1 + 1 + len(bmax_chapters) + 2 + len(seppuku_chapters) + 1 + 1 + 1 + 1 + 1}")

if __name__ == "__main__":
    main()
