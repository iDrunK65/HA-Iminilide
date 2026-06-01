from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "custom_components" / "iminilide"

custom_components_package = types.ModuleType("custom_components")
custom_components_package.__path__ = [str(PROJECT_ROOT / "custom_components")]
sys.modules.setdefault("custom_components", custom_components_package)

iminilide_package = types.ModuleType("custom_components.iminilide")
iminilide_package.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("custom_components.iminilide", iminilide_package)

_load_module("custom_components.iminilide.exceptions", PACKAGE_ROOT / "exceptions.py")
parser = _load_module("custom_components.iminilide.parser", PACKAGE_ROOT / "parser.py")

parse_general_configuration = parser.parse_general_configuration
parse_network_configuration = parser.parse_network_configuration
parse_refresh_payload = parser.parse_refresh_payload
parse_voie_configuration = parser.parse_voie_configuration
parse_voie_list = parser.parse_voie_list


GENERAL_CONFIGURATION_HTML = """
<form>
<input type="text" name="nom_iminilide" value="PIC - ch froides sanitaires niv3" />
</form>
<div class="bas_de_page">
<div class="element_bas_de_page">numero de serie : 1021213418</div>
<div class="element_bas_de_page">afficheur : 6.14</div>
<div class="element_bas_de_page">base : 6.14</div>
<div class="element_bas_de_page">page internet : 3.0</div>
</div>
"""

NETWORK_CONFIGURATION_HTML = """
<div style="text-align: center;margin-top: 30px;" class="champs">RESEAU (MAC adr) : 00:1E:AC:FC:CF:12</div>
"""

VOIE_LIST_HTML = """
<h1>Configuration des voies</h1>
<div class="champs"><div class="champs_libelle"><a href="/index?configuration_voie1">Voie 1 (CF PIC WC n3
NEGATIVE)</a></div><div class="clearer"> </div></div>
<div class="champs"><div class="champs_libelle"><a href="/index?configuration_voie2">Voie 2 (libre
)</a></div></div>
"""

VOIE_CONFIGURATION_HTML = """
<form method="post" action="/index?configuration_voie1">
<input type="hidden" name="action" value="configurer_voie" />
<input type="hidden" name="numero" value="1" />
<input type="checkbox" id="active" name="active" value="ok" checked />
<input type="text" id="nom1" name="nom1" maxlength="12" value="CF PIC WC n3" />
<input type="text" id="nom2" name="nom2" maxlength="11" value="NEGATIVE" />
<select id="type" name="type">
<option name="Temperature" value="0" selected="selected">Temperature</option>
<option name="Contact" value="1">Contact</option>
</select>
<select id="unite" name="unite">
<option value="0" selected="selected">&deg;C</option>
</select>
<select id="surveillance_alarme" name="surveillance_alarme">
<option value="O" selected="selected">Activee</option>
<option value="N">Desactivee</option>
</select>
<input type="text" id="seuil_alarme_haut" name="seuil_alarme_haut" value="-14.0" />
<input type="text" id="seuil_alarme_bas" name="seuil_alarme_bas" value="-25.0" />
</form>
"""

REFRESH_PAYLOAD = """
{
  "0": {
    "nom_num_voie": "VOIE",
    "num_voie": "1",
    "nom_voie": "CF PIC WC n3 NEGATIVE",
    "etat_voie": "",
    "modal": "Disabled",
    "duree": "",
    "nom_produit": "",
    "cycle_en_cours": "",
    "valeur_voie": "-10.3 &deg;C"
  },
  "1": {
    "nom_num_voie": "VOIE",
    "num_voie": "2",
    "nom_voie": "libre ",
    "etat_voie": "alarme_haute",
    "modal": "Disabled",
    "duree": "90 min",
    "nom_produit": "",
    "cycle_en_cours": "Defrost",
    "valeur_voie": "25.2 &deg;C"
  },
  "btn": {
    "btn_acquitter": ""
  }
}
"""


class ParserTests(unittest.TestCase):
    def test_parse_general_configuration(self) -> None:
        metadata = parse_general_configuration(
            GENERAL_CONFIGURATION_HTML, NETWORK_CONFIGURATION_HTML
        )

        self.assertEqual(metadata.name, "PIC - ch froides sanitaires niv3")
        self.assertEqual(metadata.serial_number, "1021213418")
        self.assertEqual(metadata.mac_address, "00:1e:ac:fc:cf:12")
        self.assertEqual(metadata.firmware_web, "3.0")

    def test_parse_network_configuration(self) -> None:
        mac_address = parse_network_configuration(NETWORK_CONFIGURATION_HTML)

        self.assertEqual(mac_address, "00:1e:ac:fc:cf:12")

    def test_parse_voie_list(self) -> None:
        voies = parse_voie_list(VOIE_LIST_HTML)

        self.assertEqual(len(voies), 2)
        self.assertEqual(voies[0].number, 1)
        self.assertEqual(voies[0].name, "CF PIC WC n3 NEGATIVE")
        self.assertEqual(voies[1].name, "libre")

    def test_parse_voie_configuration(self) -> None:
        voie = parse_voie_configuration(VOIE_CONFIGURATION_HTML)

        self.assertEqual(voie.number, 1)
        self.assertTrue(voie.active)
        self.assertEqual(voie.name, "CF PIC WC n3 NEGATIVE")
        self.assertEqual(voie.sensor_type, "Temperature")
        self.assertAlmostEqual(voie.alarm_high_threshold, -14.0)
        self.assertAlmostEqual(voie.alarm_low_threshold, -25.0)

    def test_parse_refresh_payload(self) -> None:
        readings = parse_refresh_payload(REFRESH_PAYLOAD)

        self.assertEqual(set(readings), {1, 2})
        self.assertAlmostEqual(readings[1].numeric_value, -10.3)
        self.assertEqual(readings[1].name, "CF PIC WC n3 NEGATIVE")
        self.assertEqual(readings[2].state, "alarme_haute")
        self.assertEqual(readings[2].duration, "90 min")
        self.assertEqual(readings[2].cycle_in_progress, "Defrost")


if __name__ == "__main__":
    unittest.main()
