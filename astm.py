#!/bin/env python
import types
from pathlib import Path

from bs4 import BeautifulSoup

from ontopy import World
import owlready2


#thisdir = os.path.abspath(os.path.dirname(__file__))
thisdir = Path(__file__).absolute().parent


def en(s):
    """Returns `s` as an English location string."""
    return owlready2.locstr(s, lang="en")


def fixtitle(title):
    """Fix ASTM title."""
    if title.endswith(",noun"):
        title = title[:-5]
    return "".join(r if r.isupper() else r.title() for r in title.split(" "))


def fixdef(definition):
    """Fix ASTM definition."""
    definition = definition.replace("\n(", " (")
    definition = definition.replace("\n (", " (")
    definition = definition.replace(") ,", "),")
    definition = definition.replace("  ", " ")
    definition = definition.replace(" .", ".")
    first, rest = definition.split(" ", 1)
    definition = f"{first.title()} {rest.strip()}"
    return definition if definition.endswith(".") else f"{definition}."


astm_iri = "http://iso.org/astm#"

world = World()
astm = world.get_ontology(astm_iri)
astm.base_iri = astm_iri

with astm:

    class prefLabel(owlready2.AnnotationProperty):
        iri = "http://www.w3.org/2004/02/skos/core#prefLabel"

    class altLabel(owlready2.AnnotationProperty):
        iri = "http://www.w3.org/2004/02/skos/core#altLabel"

    class astmNo(owlready2.AnnotationProperty):
        comment = "ASTM number."

    class astmId(owlready2.AnnotationProperty):
        comment = "ASTM id."

    class astmDef(owlready2.AnnotationProperty):
        comment = "ASTM definition."


    # Parse ASTM HTML file
    filename = thisdir / "ISO_ASTM_52900_2021_Additive_manufacturing.html"
    with open(filename, "rt") as f:
        parsed = BeautifulSoup(f.read(), features="html.parser")

    for term in parsed.body.find_all(
            "div", attrs={"class": "sts-section sts-tbx-sec"}):
        termno = term.find("div", attrs={"class": "sts-tbx-label"}).text
        termid = term.attrs.get("id")
        titles = [t.text for t in term.find_all(
            "div", attrs={"class": "sts-tbx-term"})]
        definition = term.find("div", attrs={"class": "sts-tbx-def"}).text
        #notes = [note for note in term.find_all(
        #    "div", attrs={"class": "sts-tbx-note"})]
        notes = [" ".join(list(note.strings)[1:]) for note in term.find_all(
            "div", attrs={"class": "sts-tbx-note"})]

        Term = types.new_class(f"ASTM_{termno}", (owlready2.Thing, ))
        Term.prefLabel.append(en(fixtitle(titles[0])))
        Term.altLabel.extend(en(fixtitle(title)) for title in titles[1:])
        Term.astmNo = termno
        Term.astmId = termid
        Term.astmDef = en(fixdef(definition))
        Term.comment.extend(en(fixdef(note)) for note in notes)

#astm.metadata.title.append(en('xxx'))

astm.set_version(version="v1", version_iri="http://iso.org/v1/astm#")
astm.save(thisdir / "astm.ttl", format="turtle", overwrite=True)
