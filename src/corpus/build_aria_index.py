import math
from os import listdir
import os
from os.path import isfile, join
from src.corpus.models import AriaHeaderModel, AriaMetaDataModel
from src.paths import ARIA_INDEX_PATH, MSCX_FOLDER_DIR
import re, json
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pydantic import TypeAdapter

def build_index (index_path: Path):
    folder_path = MSCX_FOLDER_DIR
    music_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]

    DIDONE_FILE_NAME_PAT = re.compile(
        r'^(?P<drama>[A-Za-z]+)'
        r'(?P<aria_no>\d+[A-Z]?)'         # e.g. 31M
        r'-'
        r'(?P<incipit>.+?)'               # non-greedy incipit slug (Tu_vuoi)
        r'-'
        r'(?P<year>nd|\d{4})'             # year or 'nd'
        r'-'
        r'(?P<composer>[^\[]+)'           # composer up to [
        r'\['
        r'(?P<act_scene>[^\]]+)'          # first bracket group
        r'\]'
        r'\['
        r'(?P<item_id>\d+)'               # numeric id
        r'\]'
        r'\.mscx$'
    )

    def parse_filename(fname: str) -> dict | None:
        """Parse a DIDONE-style filename into a dict or return None on mismatch."""

        m = DIDONE_FILE_NAME_PAT.match(Path(fname).name)
        if not m:
            return None
        d = m.groupdict()

        # post-process common normalization
        d['incipit'] = d['incipit'].replace('_', ' ')


        # split act and scene
        act_scene = re.match(r'^(?P<act>\d+)\.(?P<scene>\d+)', d['act_scene'])
        if act_scene:
            d["act"] = int(act_scene.group("act"))
            d["scene"] = int(act_scene.group("scene")) if act_scene.group("scene") is not None else None
        else:
            d["act"] = None
            d["scene"] = None

        # try to split aria_no into numeric and suffix
        nmc_sfx = re.match(r'(?P<num>\d+)(?P<suffix>[A-Z])?$', d['aria_no'])
        if nmc_sfx:
            d['aria_number'] = int(nmc_sfx.group('num'))
            d['aria_suffix'] = nmc_sfx.group('suffix') or ''
        else:
            d['aria_number'] = d['aria_no']
            d['aria_suffix'] = ''

        return d


    def extract_header_from_mscx (file_path: Path) -> AriaHeaderModel:
        """Extract header info from a MuseScore .mscx file using <metaTag> elements."""
        out = AriaHeaderModel()

        # parse iteratively to stop early without parsing the actual music data
        # look for <metaTag name="..."> inside Score
        for event, elem in ET.iterparse(file_path, events=("start", "end")):
            # first Part element => already passed meta tags
            if event == "start" and elem.tag == "Part":
                break

            if event == "end":
                # e.g. <metaTag name="movementTitle">text</metaTag>
                if elem.tag == "metaTag":
                    name = elem.get("name")
                    text = elem.text.strip() if elem.text and elem.text.strip() else None
                    if not name or not text:
                        elem.clear()
                        continue
                    else:
                        name = name.lower()

                    match name:
                        case "id":
                            try:
                                out.id = int(text)
                            except:
                                # some arias seem to have faulty id values, as with Art12M-Rendimi_il-1772-Paisiello[2.01][2283].mscx
                                pass
                        case "ismn":
                            out.ismn = text
                        case "act&scene":
                            out.act_scene = text
                        case "aria":
                            out.aria = text
                        case "aria_label":
                            out.aria_label = text
                        case "character":
                            out.character = text
                        case "composer":
                            out.composer = text
                        case "movementnumber":
                            out.movement_number = int(text)
                        case "movementtitle":
                            out.movement_title = text
                        case "opera":
                            out.opera = text
                        case "creationdate":
                            out.creation_date = text
                        case "originalformat":
                            out.original_format = text
                        case "lyricist":
                            out.lyricist = text
                        case "platform":
                            out.platform = text
                        case "source":
                            out.source = text
                        case "year":
                            try:
                                out.year = int(text)
                            except ValueError:
                                if not text == "nd":
                                    try:
                                        # parse uncertain years like 1784[1780] from Did20M-Fosca_nube-1780-Piticchio[2.08][1874].mscx
                                        out.year = int(text.split('[')[0].strip())
                                        out.source_year = text
                                    except:
                                        pass
                        case "creationDate":
                            out.creation_date = text
        
                # free memory
                elem.clear()

        return out

    arias: list[AriaMetaDataModel] = []
    for aria in music_files:
        file_data = parse_filename(aria)

        if (folder_path / aria).is_file() and (folder_path / aria).suffix.lower() == ".mscx":
            header_data = extract_header_from_mscx(folder_path / aria)

            if file_data and header_data and header_data.id:
                # ids have to match
                assert int(file_data["item_id"]) == int(header_data.id)

                # takes extracted meta data from mscx file over file name data, but compares id
                aria_data = AriaMetaDataModel()
                aria_data = header_data
                aria_data.file_name = aria
                aria_data.incipit = file_data["incipit"]

                if not aria_data.aria:
                    aria_data.aria = file_data["aria_no"]

                arias.append(aria_data)

    # save to file
    with open(index_path, "wb") as f:
        for aria in arias:
            b = aria.model_dump_json(ensure_ascii=False).encode("utf8")
            f.write(b + b"\n")

        print(f'Wrote aria index at { index_path } with a total of {len(arias)} arias at around { math.ceil(os.path.getsize(index_path) / 1024) } kB.')


def load_aria_index() -> list[AriaHeaderModel]:
    arias: list[AriaHeaderModel] = []
    with ARIA_INDEX_PATH.open("r", encoding="utf8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                arias.append(AriaHeaderModel.model_validate_json(line))
            except Exception as e:
                print(f"Skipping invalid JSONL line {line_no}: {e}")
    return arias


def create_or_load_aria_index () -> list[AriaHeaderModel]:
    # generate aria_index if not already existing
    if not ARIA_INDEX_PATH.is_file():
        print(f'No aria index found. Generating new aria index at { ARIA_INDEX_PATH }.')
        build_index(ARIA_INDEX_PATH)
    else:
        print(f'Using existing aria index at {ARIA_INDEX_PATH}.')
    
    return load_aria_index()