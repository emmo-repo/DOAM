#!/bin/env python
import types
from pathlib import Path

from bs4 import BeautifulSoup

from ontopy import World
import owlready2


# Version of the ISO/ASTM standard (not direct accessable from html)
version = "v1"

# Base iri prepended to all concepts in the generated ontology
astm_iri = "http://iso.org/astm#"

# Header numbers, mapped to (header_name, header_documentation) tuples
headers = {
    "3.1": ("General terms",
            "General terms related to additive manufacturing."),
    "3.2": ("Process categories",
            "Categorisation according to AM processing technique."),
    "3.3": ("Processing: general processing",
            "General terms related to AM processing."),
    "3.4": ("Processing: data",
            "Software-related terms."),
    "3.5": ("Processing: positioning coordination and orientation",
            "Terms related to AM positioning, coordination and "
            "orientation."),
    "3.6": ("Processing: material",
            "Material-related terms for AM processing."),
    "3.7": ("Processing: material extrusion",
            "Material-related terms for AM extrusion"),
    "3.8": ("Processing: powder bed fusion",
            "Terms related to powder bed fusion."),
    "3.9": ("Parts: general parts",
            "AM products categorised according to structure."),
    "3.10": ("Parts: applocations",
            "Categorisation according to application within AM."),
    "3.11": ("Parts: properties",
            "Part-related properties."),
    "3.12": ("Parts: evaluation",
            "Terms related to evaluation of AM products."),
}

# Description of top-level headers (that cannot be derived from `headers`)
topheaders = {
    "Processing": "Terms related to AM processing.",
    "Parts": "The class of all terms  within additive manufaturing "
           "that are related to parts.",
}

# Additional rdfs:subClassOf relations
subclassOf = {
    "3DPrinting": ["AdditiveManufacturing"],
}


# -- Start of main script --
def en(s):
    """Returns `s` as an English location string."""
    return owlready2.locstr(s, lang="en")


def fixtitle(title):
    """Fix ASTM title."""
    for type in "noun", "verb", "adjective", "participle":
        if title.endswith(f",{type}"):
            title = title[:-len(type)-1]
            break
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


thisdir = Path(__file__).absolute().parent
world = World()


# Selected annotations from SKOS
skos = world.get_ontology("http://www.w3.org/2004/02/skos/core#")
with skos:
    class prefLabel(owlready2.rdfs.label):
        """The preferred label for a concept."""

    class altLabel(owlready2.rdfs.label):
        """Alternative label for a concept."""

    class hiddenLabel(owlready2.rdfs.label):
        """A lexical label for a resource that should be hidden when
        generating visual displays of the resource, but should still
        be accessible to free text search operations."""
        comment = ["May be used for deprecated or misspelled labels."]


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


with astm:
    class astmNo(owlready2.AnnotationProperty):
        """ASTM number."""

    class astmId(owlready2.AnnotationProperty):
        """Full ISO/ASTM identifier."""

    class astmDef(owlready2.rdfs.comment):
        """ASTM definition."""

    class ASTMType(owlready2.Thing):
        """Categorisation according to grammatical category in linguistics."""

    class Noun(ASTMType):
        """Terms that are nouns, i.e. that are names of something."""

    class Verb(ASTMType):
        """Terms that are verbs."""

    class Adjective(ASTMType):
        """Terms that describe or limit/restrict the meaning of a noun.
        Typically a condition."""

    class Participle(ASTMType):
        """A verbal that expresses a state of an entity."""


    # Add classes from headers
    for headerno, (header, astmdef) in headers.items():
        if ":" in header:
            topname, _ = header.split(":")
            name = f"ASTM_{topname}"
            if name not in astm:
                preflabel = en(fixtitle(topname))
                TopHeader = types.new_class(name, (owlready2.Thing,))
                TopHeader.prefLabel.append(en(preflabel))
                TopHeader.astmDef.append(en(topheaders[preflabel]))

    for headerno, (header, astmdef) in headers.items():
        if ":" in header:
            topname, preflabel = header.split(":")
            base = astm[f"ASTM_{topname}"]
        else:
            preflabel = header
            base = owlready2.Thing
        Header = types.new_class(f"ASTM_{headerno}", (base,))
        Header.prefLabel.append(en(fixtitle(preflabel)))
        Header.astmNo = headerno
        Header.astmDef = en(astmdef)


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
        notes = [" ".join(list(note.strings)[1:]) for note in term.find_all(
            "div", attrs={"class": "sts-tbx-note"})]

        headerno = ".".join(termno.split(".")[:2])
        Header = astm[f"ASTM_{headerno}"]

        if titles[0].endswith("noun"):
            bases = (Header, Noun)
        elif titles[0].endswith("verb"):
            bases = (Header, Verb)
        elif titles[0].endswith("adjective"):
            bases = (Header, Adjective)
        elif titles[0].endswith("participle"):
            bases = (Header, Participle)
        else:
            bases = (Header,)

        Term = types.new_class(f"ASTM_{termno}", bases)
        Term.prefLabel.append(en(fixtitle(titles[0])))
        for title in titles[1:]:
            if title.lower().startswith("deprecated:"):
                Term.hiddenLabel.append(en(fixtitle(title[11:])))
            else:
                Term.altLabel.append(en(fixtitle(title)))
        Term.astmNo = termno
        Term.astmId = termid
        Term.astmDef = en(fixdef(definition))
        Term.comment.extend(en(fixdef(note)) for note in notes)

# Add additional subclass relations
for clsname, subclasses in subclassOf.items():
    astm[clsname].is_a.extend(astm[name] for name in subclasses)

# Convert class docstrings to rdfs:comment
astm.sync_attributes()

# Add metadata
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

# Save to file
astm.save(thisdir / "astm.ttl", format="turtle", overwrite=True)
