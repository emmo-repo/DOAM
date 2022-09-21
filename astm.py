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
    if title.endswith(",adjective"):
        title = title[:-10]
    if title.endswith(",participle"):
        title = title[:-11]
    title = "".join(r if r.isupper() else r.title() for r in title.split(" "))
    return title.replace("-", "")


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


version = "v1"
astm_iri = "http://iso.org/astm#"

world = World()


# Selected annotations from SKOS
skos = world.get_ontology("http://www.w3.org/2004/02/skos/core#")
with skos:
    class prefLabel(owlready2.rdfs.label):
        pass

    class altLabel(owlready2.rdfs.label):
        pass


# Selected annotations from Dublin Core terms
dcterms = world.get_ontology("http://purl.org/dc/terms/")
with dcterms:
    class title(owlready2.AnnotationProperty):
        pass

    class abstract(owlready2.AnnotationProperty):
        pass

    class creator(owlready2.AnnotationProperty):
        pass

    class publisher(owlready2.AnnotationProperty):
        pass

    class license(owlready2.AnnotationProperty):
        pass


# Create ASTM ontology
astm = world.get_ontology(astm_iri)
astm.base_iri = astm_iri

headers = {
    "3.1": "General terms",
    "3.2": "Process categories",
    "3.3": "Processing: general processing",
    "3.4": "Processing: data",
    "3.5": "Processing: positioning coordination and orientation",
    "3.6": "Processing: material",
    "3.7": "Processing: material extrusion",
    "3.8": "Processing: powder bed fusion",
    "3.9": "Parts: general parts",
    "3.10": "Parts: applocations",
    "3.11": "Parts: properties",
    "3.12": "Parts: evaluation",
}

with astm:
    class astmNo(owlready2.AnnotationProperty):
        prefLabel = ["astmNo"]
        comment = ["ASTM number."]

    class astmId(owlready2.AnnotationProperty):
        prefLabel = ["astmId"]
        comment = ["ASTM id."]

    class astmDef(owlready2.AnnotationProperty):
        prefLabel = ["astmDef"]
        comment = ["ASTM definition."]

    class ASTMType(owlready2.Thing):
        prefLabel = ["ASTMType"]
        comment = ["Type categorisation."]

    class Noun(ASTMType):
        prefLabel = ["Noun"]

    class Adjective(ASTMType):
        prefLabel = ["Adjective"]

    class Participle(ASTMType):
        prefLabel = ["Participle"]

    for headerno, header in headers.items():
        if ":" in header:
            topname, _ = header.split(":")
            name = f"ASTM_{topname}"
            if name not in astm:
                TopHeader = types.new_class(name, (owlready2.Thing,))
                TopHeader.prefLabel.append(en(fixtitle(topname)))

    for headerno, header in headers.items():
        if ":" in header:
            topname, preflabel = header.split(":")
            base = astm[f"ASTM_{topname}"]
        else:
            preflabel = header
            base = owlready2.Thing
        Header = types.new_class(f"ASTM_{headerno}", (base,))
        Header.prefLabel.append(en(fixtitle(preflabel)))
        Header.astmNo = headerno


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

        headerno = ".".join(termno.split(".")[:2])
        Header = astm[f"ASTM_{headerno}"]

        if titles[0].endswith("noun"):
            bases = (Header, Noun)
        elif titles[0].endswith("adjective"):
            bases = (Header, Adjective)
        elif titles[0].endswith("participle"):
            bases = (Header, Participle)
        else:
            bases = (Header,)

        Term = types.new_class(f"ASTM_{termno}", bases)
        Term.prefLabel.append(en(fixtitle(titles[0])))
        Term.altLabel.extend(en(fixtitle(title)) for title in titles[1:])
        Term.astmNo = termno
        Term.astmId = termid
        Term.astmDef = en(fixdef(definition))
        Term.comment.extend(en(fixdef(note)) for note in notes)


astm.metadata.title.append(en(
    'ISO/ASTM 52900:2021 Additive manufacturing - General principles - '
    'Fundamentals and vocabulary'))
astm.metadata.creator.append(en('Klas Boivie, SINTEF, NO'))
astm.metadata.creator.append(en('Jesper Friis, SINTEF, NO'))
astm.metadata.creator.append(en('Sylvain Gouttebroze, SINTEF, NO'))
astm.metadata.publisher.append(en('ISO/ASTM'))
astm.metadata.abstract.append(en("""
Additive manufacturing (AM) is the general term for those technologies
that successively join material to create physical objects as
specified by 3D model data. These technologies are presently used for
various applications in engineering industry as well as other areas of
society, such as medicine, education, architecture, cartography, toys
and entertainment.

During the development of additive manufacturing technology, there
have been numerous different terms and definitions in use, often with
reference to specific application areas and trademarks. This is often
ambiguous and confusing, which hampers communication and wider
application of this technology.

It is the intention of this document to provide a basic understanding
of the fundamental principles for additive manufacturing processes,
and based on this, to give clear definitions for terms and
nomenclature associated with additive manufacturing technology. The
objective of this standardization of terminology for additive
manufacturing is to facilitate communication between people involved
in this field of technology on a worldwide basis.
"""))
astm.metadata.comment.append(en(
    'This ontology is generated from the ASTM 52900 standard published online '
    'on https://www.iso.org/obp/ui/#iso:std:iso-astm:52900:ed-2:v1:en.'))
astm.metadata.comment.append(en(
    'The CC-BY4.0 license applies to this document, not to the source from '
    'which it was generated'))
astm.metadata.license.append(en(
    'https://creativecommons.org/licenses/by/4.0/legalcode'))
astm.metadata.versionInfo.append(en(version))

astm.set_version(
    version=version, version_iri=f"http://iso.org/{version}/astm#")
astm.save(thisdir / "astm.ttl", format="turtle", overwrite=True)
