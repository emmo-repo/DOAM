#!/bin/env python
import re
import types
from pathlib import Path

from bs4 import BeautifulSoup

from ontopy import World
import owlready2


# Version of the ISO/ASTM standard (not direct accessable from html)
# The final part after the point is the version of the generated ontology
version = "2021v1.1"

# Base iri prepended to all concepts in the generated ontology
astm_iri = "http://iso.org/astm-52900#"

# Header numbers, mapped to (header_name, header_documentation) tuples
headers = {
    # General concepts
    "3.1": ("General concepts",
            "General concepts related to additive manufacturing."),
    # Process categories
    "3.2": ("Process categories",
            "Categorisation according to AM processing architecture."),
    # ProcessingRelated
    "3.3": ("ProcessingRelated: general processing",
            "General concepts related to AM processing."),
    "3.4": ("ProcessingRelated: data related",
            "Terms related to software and data handling."),
    "3.5": ("ProcessingRelated: positioning coordinates and orientation",
            "Terms related to AM positioning, coordinates and "
            "orientation."),
    "3.6": ("ProcessingRelated: material related",
            "Terms related to material (including part material and feedstock) "
            "in AM processing."),
    "3.7": ("ProcessingRelated: material extrusion related",
            "Terms related to material extrusion processes."),
    "3.8": ("ProcessingRelated: powder bed fusion related",
            "Terms related to powder bed fusion."),
    # PartsRelated
    "3.9": ("PartsRelated: general parts",
            "AM products categorised according to structure."),
    "3.10": ("PartsRelated: part application related",
            "Categorisation according to application within AM."),
    "3.11": ("PartsRelated: part property related",
            "Part-related properties."),
    "3.12": ("PartsRelated: part evaluation related",
            "Terms related to evaluation of AM products."),
}

# Description of top-level headers (that cannot be derived from `headers`)
topheaders = {
    "ProcessingRelated": "Terms related to AM processing.",
    "PartsRelated": "The class of all terms  within additive manufaturing "
           "that are related to parts.",
}

# Additional rdfs:subClassOf relations
subclassOf = {
    #"GeneralConcepts": ["ThematicCategorisation"],
    "3DPrinting": ["AdditiveManufacturing"],

    "Filament": ["Feedstock"],
    "Pellets": ["Feedstock"],
    #"Cure": ["ProcessingRelated"],

    # 3.1 General terms
    "3DPrinter": ["Equipment"],
    "AdditiveManufacturing": ["Process"],
    "AdditiveSystem": ["Equipment"],
    "AMMachine": ["Equipment"],
    "AMMachineUser": ["Role"],
    "AMSystemUser": ["Role"],
    "Front": ["EquipmentPart"],
    "MaterialSupplier": ["Role"],
    "MultiStepProcess": ["Process"],
    "SingleStepProcess": ["Process"],
    # 3.2 Process categories
    "ProcessCategories": ["Process"],
    # 3.3 General processing
    "3DPrinting": ["Process"],
    "BuildChamber": ["EquipmentPart"],
    "BuildCycle": ["Process"],
    "BuildPlatform": ["Equipment"],
    "BuildSpace": ["Geometrical"],
    "BuildSurface": ["Geometrical"],
    "BuildVolume": ["Geometrical"],
    "Layer": ["Material"],
    "ManufacturingLot": ["Material"],  # ???
    "ManufacturingPlan": ["Data"],  # ???
    "ProcessChain": ["Process"],  # ???
    "ProcessParameters": ["Data"],
    "ProductionRun": ["Material"],  # check
    "Support": ["Material"],
    "SystemSetUp": ["Data"],
    # 3.4 Data-related
    "3DScanning": ["Process"],
    "AdditiveManufacturingFileFormat": ["Data"],
    "AMFConsumer": ["Role"],
    "AMFEditor": ["Role"],
    "AMFProducer": ["Role"],
    "Attribute": ["Data"],
    "Comment": ["Data"],
    "Element": ["Data"],
    "Facet": ["Geometrical"],
    "PDES": ["Data"],
    "STEP": ["Data"],
    "STL": ["Data"],
    "SurfaceModel": ["Data"],  # Model ???
    # 3.5 Positioning, coordinated and orientation
    "ArbitrarilyOrientedBoundingBox": ["Geometrical", "BoundingBox"],
    "BoundingBox": ["Geometrical"],
    "BuildEnvelope": ["Geometrical"],
    "BuildOrigin": ["Geometrical", "Origin"],
    "GeometricCentre": ["Geometrical"],
    "InitialBuildOrientation": ["Geometrical"],
    "MachineBoundingBox": ["Geometrical", "BoundingBox"],
    "MachineCoordinateSystem": ["Geometrical"],
    "MachineOrigin": ["Geometrical", "Origin"],
    "MasterBoundingBox": ["Geometrical", "BoundingBox"],
    "Nesting": [],  # Geometrical or Material or Situation/Condition ???
    "Origin": ["Geometrical"],
    "OrthogonalOrientationNotation": ["Geometrical"],  # ???
    "PartLocation": ["Geometrical"],
    "PartReorientation": ["Geometrical"],  # or is it a process/operation ???
    "XAxis": ["Geometrical"],
    "YAxis": ["Geometrical"],
    "ZAxis": ["Geometrical"],
    # 3.6 Material-related
    "Batch": ["Material"],  # inverse(hasPart) only Feedstock
    "Cure": ["Process"],
    "Feedstock": ["Material"],
    "FeedstockManufacturer": ["Role"],
    "FeedstockSupplier": ["Role"],
    "Fusion": ["Process"],
    "Lot": ["Material"],  # inverse(hasPart) only Feedstock
    "PostProcessing": ["Process"],
    "Spreadability": ["Property"],  # check
    "Virgin": ["Feedstock"],  # Condition (note it is an adjective) ???
    # 3.7 Material extrusion-related
    "BuildSheet": ["EquipmentPart"],
    "ExtruderHead": [],  # Union of EquipmentPart and Material ???
    "ExtrusionNozzle": ["EquipmentPart"],
    "Filament": ["Feedstock"],  # check
    "Pellets": ["Feedstock"],  # check
    # 3.8 Powder bed fusion
    "BatchFeedProcessing": ["Process"],
    "ContinuousFeedProcessing": ["Process"],
    "FeedRegion": ["Geometrical"],
    "LaserSintering": ["Process"],
    "OverflowRegion": ["Geometrical"],
    "PartCake": ["Material"],  # check
    "PowderBed": ["Geometrical"],
    "PowderBlend": ["Material"],
    "PowderMix": ["Material"],
    "UsedPowder": ["Material"],
    # 3.9 General parts
    "Lattice": ["Geometrical"],
    "Part": ["Material"],
    # 3.10 Part application-related
    "Prototype": ["Material"],
    "PrototypeTooling": ["Equipment"],
    "RapidPrototyping": ["Process"],
    "RapidTooling": ["Process"],
    # 3.11 Part property-related
    "Accuracy": ["Property"],  # check
    "AsBuilt": ["Material"],  # MaterialState ???
    "AsDesigned": ["Data"],  # MaterialState ???
    "FullyDense": ["Material"],  # may also be Property or MaterialState ???
    "NearNetShape": ["Material"],  # MaterialState ???
    "Porosity": ["Property"],
    "Precision": ["Property"],  # check
    "Repeatability": ["Property"],
    "Resolution": ["Property"],  # check
    # 3.12 Part evaluation-related
    "FinalInspection": ["Process"],
    "FirstArticle": ["Part"],
    "InspectionPlan": ["Data"],  # instruction, plan
    "Qualification": ["Process"],
    "ReferencePart": ["Part"],
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
    title = "".join(r if r and r[0].isupper() else r.title()
                    for r in title.split(" "))
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
    class conformsTo(owlready2.AnnotationProperty):
        """An established standard to which the described resource conforms."""

    class contributor(owlready2.AnnotationProperty):
        """An entity responsible for making contributions to the resource."""

    class creator(owlready2.AnnotationProperty):
        """An entity primarily responsible for making the resource."""

    class description(owlready2.AnnotationProperty):
        """An account of the resource."""

    class identifier(owlready2.AnnotationProperty):
        """An unambiguous reference to the resource within a given context."""

    class license(owlready2.AnnotationProperty):
        """A legal document giving official permission to do something with
        the resource."""

    class publisher(owlready2.AnnotationProperty):
        """An entity responsible for making the resource available."""

    class title(owlready2.AnnotationProperty):
        """A name given to the resource."""


# Create ASTM ontology
astm = world.get_ontology(astm_iri)
astm.base_iri = astm_iri


with astm:
    # -- Annotation properties
    class astmNo(identifier):
        """ASTM number."""

    class astmId(identifier):
        """Full ISO/ASTM identifier."""

    class astmDef(owlready2.rdfs.comment):
        """ASTM definition."""

    class astmRef(owlready2.rdfs.seeAlso):
        """A reference to another ASTM term."""

    class astmForeword(description):
        """General forword about an ASTM standard."""

    class astmIntroduction(description):
        """Short introduction of an ASTM standard."""

    class astmScope(description):
        """The scope of an ASTM standard."""

    class example(owlready2.rdfs.comment):
        """Illustrative example of how the entity is used."""

    # -- Classes
    class ThematicCategorisation(owlready2.Thing):
        """Categorisation according to the sections in the ASTM standard."""

    class GramaticalCategorisation(owlready2.Thing):
        """Categorisation according to grammatical category in linguistics."""

    class Noun(GramaticalCategorisation):
        """Terms that are nouns, i.e. that are names of something."""

    class Verb(GramaticalCategorisation):
        """Terms that are verbs."""

    class Adjective(GramaticalCategorisation):
        """Terms that describe or limit/restrict the meaning of a noun.
        Typically a condition."""

    class Participle(GramaticalCategorisation):
        """A verbal that expresses a state of an entity."""

    # -- Some top-level categories for describing what things really are
    class Equipment(owlready2.Thing):
        """An item necessary for realising a particular purpose.

        -- Oxford Languages
        """

    class EquipmentPart(owlready2.Thing):
        """A part of an equipment."""

    class Material(owlready2.Thing):
        """A real world material representing an amount of a physical
        substance (or mixture of substances) in different states of
        matter or phases."""

    class Process(owlready2.Thing):
        """A series of actions or steps taken in order to achieve a
        particular end.

        -- Oxford Languages
        """

    class Role(owlready2.Thing):
        """An actor's part in a process."""
        example = en("A person or a software.")

    class Data(owlready2.Thing):
        """An object whose variation in properties are encoded by
        an agent and that can be decoded by another agent according to
        a specific rule."""
        example = en("A morse code radio transmission.")

    class Geometrical(Data):
        """A geometrical object, like a position, an area or a volume."""

    class Property(owlready2.Thing):
        """An attribute, quality or characteristic of something.

        -- Oxford Languages
        """


    # Add classes from headers
    for headerno, (header, astmdef) in headers.items():
        if ":" in header:
            topname, _ = header.split(":")
            name = f"ASTM_{topname}"
            if name not in astm:
                preflabel = en(fixtitle(topname))
                TopHeader = types.new_class(name, (ThematicCategorisation, ))
                TopHeader.prefLabel.append(en(preflabel))
                TopHeader.astmDef.append(en(topheaders[preflabel]))

    for headerno, (header, astmdef) in headers.items():
        if ":" in header:
            topname, preflabel = header.split(":")
            base = astm[f"ASTM_{topname}"]
        else:
            preflabel = header
            base = ThematicCategorisation
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
        Term.astmRef.extend(f"{astm_iri}ASTM_{ref}" for ref in re.findall(
            r"\((\d+\.\d+\.\d+)\)", definition))

    foreword = parsed.body.find(
        'div',
        attrs={'id': 'toc_iso_std_iso-astm_52900_ed-2_v1_en_sec_foreword'},
    ).find('div').text
    introduction = parsed.body.find(
        'div',
        attrs={'id': 'toc_iso_std_iso-astm_52900_ed-2_v1_en_sec_intro'},
    ).find('div').text
    sec1 = parsed.body.find(
        'div', attrs={'id': 'toc_iso_std_iso-astm_52900_ed-2_v1_en_sec_1'})
    sec2 = parsed.body.find(
        'div', attrs={'id': 'toc_iso_std_iso-astm_52900_ed-2_v1_en_sec_2'})
    scope = sec1.find('div').text
    normative_references = sec2.find('div').text


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
astm.metadata.creator.append(en('Even Wilberg Hovig, SINTEF, NO'))
astm.metadata.publisher.append(en('ISO/ASTM'))
astm.metadata.astmForeword.append(en(foreword))
astm.metadata.astmIntroduction.append(en(introduction))
astm.metadata.astmScope.append(en(scope))
astm.metadata.conformsTo.append(en(
    'ISO Online browsing platform: available at https://www.iso.org/obp'))
astm.metadata.conformsTo.append(en(
    'IEC Electropedia: available at https://www.electropedia.org/'))
astm.metadata.comment.append(en(
    'This ontology is generated from the ASTM 52900 standard published online '
    'on https://www.iso.org/obp/ui/#iso:std:iso-astm:52900:ed-2:v1:en.'))
astm.metadata.comment.append(en(
    'The CC-BY4.0 license applies to this document, not to the source from '
    'which it was generated'))
astm.metadata.license.append(en(
    'https://creativecommons.org/licenses/by/4.0/legalcode'))
astm.metadata.versionInfo.append(en(version))

astm.metadata.comment.append(en(
    """The version consists of two parts, first an identifier for the
    version of the ISO/ASTM standard followed by a point and the version
    of the generated ontology."""))
astm.set_version(
    version=version, version_iri=f"http://iso.org/astm/{version}#")

# Save to file
astm.save(thisdir / "astm.ttl", format="turtle", overwrite=True)
